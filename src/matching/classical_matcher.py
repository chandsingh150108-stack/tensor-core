from __future__ import annotations

import logging

import cv2
import numpy as np

from src.features.base import FeatureResult

logger = logging.getLogger(__name__)


class InsufficientCorrespondencesError(Exception):
    """Raised when fewer than the minimum required correspondences are found."""


def match_features(
    fr_a: FeatureResult,
    fr_b: FeatureResult,
    method: str = "flann",
    ratio_thresh: float = 0.75,
) -> np.ndarray:
    if len(fr_a.keypoints) == 0 or len(fr_b.keypoints) == 0:
        return np.empty((0, 2), dtype=np.int32)

    desc_a = fr_a.descriptors
    desc_b = fr_b.descriptors

    if desc_a.dtype == np.uint8:
        return _match_binary(desc_a, desc_b, method)
    else:
        return _match_float(desc_a, desc_b, method, ratio_thresh)


def _match_float(
    desc_a: np.ndarray,
    desc_b: np.ndarray,
    method: str,
    ratio_thresh: float,
) -> np.ndarray:
    if method == "flann":
        index_params = dict(algorithm=1, trees=5)
        search_params = dict(checks=50)
        matcher = cv2.FlannBasedMatcher(index_params, search_params)
    else:
        matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)

    try:
        knn_matches = matcher.knnMatch(desc_a, desc_b, k=2)
    except cv2.error:
        return np.empty((0, 2), dtype=np.int32)

    good_matches = []
    for m_n in knn_matches:
        if len(m_n) == 2:
            m, n = m_n
            if m.distance < ratio_thresh * n.distance:
                good_matches.append(m)

    if not good_matches:
        return np.empty((0, 2), dtype=np.int32)

    return np.array([[m.queryIdx, m.trainIdx] for m in good_matches], dtype=np.int32)


def _match_binary(
    desc_a: np.ndarray,
    desc_b: np.ndarray,
    method: str,
) -> np.ndarray:
    if method == "flann":
        index_params = dict(
            algorithm=6,
            table_number=12,
            key_size=12,
            multi_probe_level=1,
        )
        search_params = dict(checks=50)
        matcher = cv2.FlannBasedMatcher(index_params, search_params)
    else:
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    try:
        knn_matches = matcher.knnMatch(desc_a, desc_b, k=2)
    except cv2.error:
        return np.empty((0, 2), dtype=np.int32)

    good_matches = []
    for m_n in knn_matches:
        if len(m_n) == 2:
            m, n = m_n
            if m.distance < 0.8 * n.distance:
                good_matches.append(m)

    if not good_matches:
        return np.empty((0, 2), dtype=np.int32)

    return np.array([[m.queryIdx, m.trainIdx] for m in good_matches], dtype=np.int32)
