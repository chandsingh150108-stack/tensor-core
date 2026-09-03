from __future__ import annotations

import base64
import io
import logging
import traceback
from typing import Optional

import cv2
import numpy as np

from src.common.schema import ImageMetadata
from src.evaluation.confidence import composite_confidence
from src.evaluation.metrics import compute_inlier_ratio, compute_mutual_information, compute_ssim
from src.matching.warp import warp_source
from src.preprocessing.pipeline import PreprocessingPipeline
from src.routing.retry_loop import register_with_retry

logger = logging.getLogger(__name__)

_jobs: dict[str, dict] = {}

MAX_DIMENSION = 4000


def get_job(job_id: str) -> Optional[dict]:
    return _jobs.get(job_id)


def _crop_to_manageable(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    if h <= MAX_DIMENSION and w <= MAX_DIMENSION:
        return img

    crop_h = min(h, MAX_DIMENSION)
    crop_w = min(w, MAX_DIMENSION)
    y = (h - crop_h) // 2
    x = (w - crop_w) // 2

    logger.info(
        "Cropping large image %dx%d to center %dx%d",
        w, h, crop_w, crop_h,
    )

    if img.ndim == 2:
        return img[y:y + crop_h, x:x + crop_w]
    return img[y:y + crop_h, x:x + crop_w, :]


def _create_overlay(source: np.ndarray, warped: np.ndarray) -> np.ndarray:
    h, w = source.shape[:2]
    if warped.shape[:2] != (h, w):
        warped = cv2.resize(warped, (w, h))

    src_norm = cv2.normalize(source, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    wrp_norm = cv2.normalize(warped, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    if src_norm.ndim == 2:
        src_rgb = cv2.cvtColor(src_norm, cv2.COLOR_GRAY2RGB)
    else:
        src_rgb = src_norm
    if wrp_norm.ndim == 2:
        wrp_rgb = cv2.cvtColor(wrp_norm, cv2.COLOR_GRAY2RGB)
    else:
        wrp_rgb = wrp_norm

    overlay = cv2.addWeighted(src_rgb, 0.5, wrp_rgb, 0.5, 0)
    return overlay


def _img_to_base64_png(img: np.ndarray) -> str:
    if img.dtype != np.uint8:
        img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    _, buf = cv2.imencode(".png", img)
    return base64.b64encode(buf).decode("ascii")


def _extract_keypoints(processed_img: np.ndarray):
    try:
        from src.features.factory import get_detector
        det = get_detector("sift")
        fr = det.detect_and_compute(processed_img)
        kps = fr.keypoints[:200]
        return [{"x": float(kp[0]), "y": float(kp[1])} for kp in kps]
    except Exception as e:
        logger.warning("Failed to extract keypoints: %s", e)
        return []


def run_registration_job(
    job_id: str,
    img_a: np.ndarray,
    meta_a: ImageMetadata,
    img_b: np.ndarray,
    meta_b: ImageMetadata,
) -> None:
    _jobs[job_id]["status"] = "running"
    try:
        img_a = _crop_to_manageable(img_a)
        img_b = _crop_to_manageable(img_b)

        pipeline = PreprocessingPipeline()
        processed_a = pipeline.run(img_a, meta_a)
        processed_b = pipeline.run(img_b, meta_b)

        result = register_with_retry(processed_a, processed_b, meta_a, meta_b)

        metrics = {}
        warped_img = None
        feature_points = []

        if result.success and result.transform is not None:
            warped = warp_source(
                processed_b, result.transform, "homography", processed_a.shape[:2]
            )
            metrics["ssim"] = compute_ssim(processed_a, warped)
            metrics["mutual_information"] = compute_mutual_information(processed_a, warped)
            metrics["inlier_ratio"] = result.inlier_ratio
            metrics["corner_reprojection_error"] = None

            overlay = _create_overlay(processed_a, warped)
            warped_img = _img_to_base64_png(overlay)

            feature_points = _extract_keypoints(processed_a)
        else:
            metrics["ssim"] = 0.0
            metrics["mutual_information"] = 0.0
            metrics["inlier_ratio"] = result.inlier_ratio

        conf = composite_confidence(metrics)

        _jobs[job_id].update({
            "status": "done",
            "result": {
                "success": result.success,
                "matcher_used": result.matcher_used,
                "difficulty": result.difficulty,
                "inlier_ratio": result.inlier_ratio,
                "metrics": metrics,
                "confidence": conf,
                "error_message": result.error_message,
                "warped_image": warped_img,
                "source_image": _img_to_base64_png(processed_a),
                "feature_points": feature_points,
            },
        })
    except Exception as e:
        logger.error("Registration job %s failed: %s", job_id, e)
        _jobs[job_id].update({
            "status": "failed",
            "result": {
                "success": False,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
            },
        })
