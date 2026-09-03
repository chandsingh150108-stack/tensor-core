from __future__ import annotations

import logging
from typing import Literal, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class TransformEstimationFailedError(Exception):
    """Raised when RANSAC fails to estimate a transform."""


class InsufficientCorrespondencesError(Exception):
    """Raised when fewer than the minimum required correspondences are found."""


def estimate_transform(
    pts_a: np.ndarray,
    pts_b: np.ndarray,
    model: Literal["homography", "affine", "tps"] = "homography",
    method: int = cv2.USAC_MAGSAC,
    ransac_thresh: float = 3.0,
) -> Tuple[np.ndarray, np.ndarray]:
    if model in ("homography", "affine"):
        min_correspondences = 4
    else:
        min_correspondences = 3

    if len(pts_a) < min_correspondences:
        raise InsufficientCorrespondencesError(
            f"Need at least {min_correspondences} correspondences for {model}; got {len(pts_a)}"
        )

    pts_a_2d = pts_a.reshape(-1, 1, 2).astype(np.float64)
    pts_b_2d = pts_b.reshape(-1, 1, 2).astype(np.float64)

    if model == "homography":
        transform, mask = cv2.findHomography(
            pts_a_2d, pts_b_2d, method=method, ransacReprojThreshold=ransac_thresh
        )
        if transform is None:
            raise TransformEstimationFailedError(
                f"Homography estimation failed with {len(pts_a)} correspondences"
            )
        inlier_mask = mask.ravel().astype(bool) if mask is not None else np.ones(len(pts_a), dtype=bool)
        return transform, inlier_mask

    elif model == "affine":
        transform = cv2.estimateAffinePartial2D(
            pts_a_2d, pts_b_2d, method=method, ransacReprojThreshold=ransac_thresh
        )
        if transform[0] is None:
            raise TransformEstimationFailedError(
                f"Affine estimation failed with {len(pts_a)} correspondences"
            )
        matrix, inliers = transform
        inlier_mask = inliers.ravel().astype(bool) if inliers is not None else np.ones(len(pts_a), dtype=bool)
        return matrix, inlier_mask

    elif model == "tps":
        tps = cv2.createThinPlateSplineShapeTransformer()
        matches = [cv2.DMatch(i, i, 0) for i in range(len(pts_a))]
        tps.estimateTransformation(pts_b_2d, pts_a_2d, matches)
        return tps, np.ones(len(pts_a), dtype=bool)

    else:
        raise ValueError(f"Unknown model: {model}. Use 'homography', 'affine', or 'tps'.")
