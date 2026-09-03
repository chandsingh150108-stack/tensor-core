from __future__ import annotations

import logging
import traceback
from typing import Optional

import numpy as np

from src.common.schema import ImageMetadata
from src.evaluation.confidence import composite_confidence
from src.evaluation.metrics import compute_inlier_ratio, compute_mutual_information, compute_ssim
from src.matching.warp import warp_source
from src.preprocessing.pipeline import PreprocessingPipeline
from src.routing.retry_loop import register_with_retry

logger = logging.getLogger(__name__)

_jobs: dict[str, dict] = {}


def get_job(job_id: str) -> Optional[dict]:
    return _jobs.get(job_id)


def run_registration_job(
    job_id: str,
    img_a: np.ndarray,
    meta_a: ImageMetadata,
    img_b: np.ndarray,
    meta_b: ImageMetadata,
) -> None:
    _jobs[job_id]["status"] = "running"
    try:
        pipeline = PreprocessingPipeline()
        processed_a = pipeline.run(img_a, meta_a)
        processed_b = pipeline.run(img_b, meta_b)

        result = register_with_retry(processed_a, processed_b, meta_a, meta_b)

        metrics = {}
        if result.success and result.transform is not None:
            warped = warp_source(
                processed_b, result.transform, "homography", processed_a.shape[:2]
            )
            metrics["ssim"] = compute_ssim(processed_a, warped)
            metrics["mutual_information"] = compute_mutual_information(processed_a, warped)
            metrics["inlier_ratio"] = result.inlier_ratio
            metrics["corner_reprojection_error"] = None
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
