from __future__ import annotations

import logging
from typing import Optional

import cv2
import numpy as np
from skimage.metrics import structural_similarity

logger = logging.getLogger(__name__)


def compute_ssim(ref: np.ndarray, warped: np.ndarray) -> float:
    if ref.shape != warped.shape:
        raise ValueError(f"Shape mismatch: ref={ref.shape}, warped={warped.shape}")

    if ref.ndim == 3:
        ref_gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
        warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    else:
        ref_gray = ref
        warped_gray = warped

    valid_ref = ref_gray > 0
    valid_warped = warped_gray > 0
    overlap = valid_ref & valid_warped

    if overlap.sum() == 0:
        return 0.0

    ssim = structural_similarity(ref_gray, warped_gray, full=True)
    if isinstance(ssim, tuple):
        ssim = ssim[0]

    return float(ssim)


def compute_mutual_information(ref: np.ndarray, warped: np.ndarray) -> float:
    if ref.shape != warped.shape:
        raise ValueError(f"Shape mismatch: ref={ref.shape}, warped={warped.shape}")

    if ref.ndim == 3:
        ref_gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
        warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    else:
        ref_gray = ref
        warped_gray = warped

    valid = (ref_gray > 0) & (warped_gray > 0)
    if valid.sum() == 0:
        return 0.0

    ref_vals = ref_gray[valid].astype(np.float64)
    warped_vals = warped_gray[valid].astype(np.float64)

    hist_2d, _, _ = np.histogram2d(ref_vals, warped_vals, bins=64)
    hist_2d = hist_2d / hist_2d.sum()

    p_x = hist_2d.sum(axis=1)
    p_y = hist_2d.sum(axis=0)

    p_x = p_x[p_x > 0]
    p_y = p_y[p_y > 0]

    H_x = -np.sum(p_x * np.log2(p_x))
    H_y = -np.sum(p_y * np.log2(p_y))

    non_zero = hist_2d[hist_2d > 0]
    H_xy = -np.sum(non_zero * np.log2(non_zero))

    mi = H_x + H_y - H_xy
    return float(max(0.0, mi))


def compute_inlier_ratio(inlier_mask: np.ndarray) -> float:
    if len(inlier_mask) == 0:
        return 0.0
    return float(inlier_mask.sum() / len(inlier_mask))


def compute_corner_reprojection_error(
    transform: np.ndarray,
    model: str,
    image_shape: tuple[int, int],
    ground_truth_corners: Optional[np.ndarray] = None,
) -> Optional[float]:
    if ground_truth_corners is None:
        return None

    h, w = image_shape
    if model == "homography":
        corners = np.array(
            [[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float64
        ).reshape(-1, 1, 2)
        projected = cv2.perspectiveTransform(corners, transform)
        error = np.linalg.norm(projected.reshape(-1, 2) - ground_truth_corners, axis=1)
        return float(error.mean())
    elif model == "affine":
        corners = np.array(
            [[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float64
        ).reshape(-1, 1, 2)
        projected = cv2.transform(corners, transform)
        error = np.linalg.norm(projected.reshape(-1, 2) - ground_truth_corners, axis=1)
        return float(error.mean())

    return None
