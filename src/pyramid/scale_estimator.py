from __future__ import annotations

import logging
import math
from typing import Tuple

import cv2
import numpy as np

from src.common.schema import ImageMetadata

logger = logging.getLogger(__name__)

MIN_VALID_SCALE = 0.01
MAX_VALID_SCALE = 1000.0


def estimate_scale_ratio(meta_a: ImageMetadata, meta_b: ImageMetadata) -> float:
    if meta_a.pixel_scale_m and meta_b.pixel_scale_m:
        if MIN_VALID_SCALE <= meta_a.pixel_scale_m <= MAX_VALID_SCALE and \
           MIN_VALID_SCALE <= meta_b.pixel_scale_m <= MAX_VALID_SCALE:
            return meta_a.pixel_scale_m / meta_b.pixel_scale_m

    logger.warning(
        "Pixel scale metadata invalid or missing; falling back to phase correlation"
    )
    return 1.0


def estimate_scale_ratio_by_phase_correlation(
    img_a: np.ndarray, img_b: np.ndarray, candidate_scales: list[float] | None = None
) -> float:
    if candidate_scales is None:
        candidate_scales = [0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0]

    work_a = img_a.copy()
    work_b = img_b.copy()

    if work_a.ndim == 3:
        work_a = cv2.cvtColor(work_a, cv2.COLOR_BGR2GRAY)
    if work_b.ndim == 3:
        work_b = cv2.cvtColor(work_b, cv2.COLOR_BGR2GRAY)

    work_a = work_a.astype(np.float32)
    work_b = work_b.astype(np.float32)

    target_size = min(128, min(work_a.shape[:2]))
    if target_size < 16:
        return 1.0

    work_a = cv2.resize(work_a, (target_size, target_size))
    work_b = cv2.resize(work_b, (target_size, target_size))

    best_scale = 1.0
    best_response = -1.0

    for scale in candidate_scales:
        if scale <= 0:
            continue
        new_size = max(16, int(target_size * scale))
        resized_b = cv2.resize(work_b, (new_size, new_size))
        resized_b = cv2.resize(resized_b, (target_size, target_size))

        try:
            response, _ = cv2.phaseCorrelate(work_a, resized_b)
            if response > best_response:
                best_response = response
                best_scale = scale
        except cv2.error:
            continue

    return best_scale


def select_pyramid_levels(ratio: float, max_levels: int) -> Tuple[int, int]:
    if ratio <= 0:
        ratio = 1.0

    log_ratio = math.log2(ratio)
    level_diff = round(log_ratio)
    level_diff = max(0, min(level_diff, max_levels - 1))

    level_a = 0
    level_b = level_diff

    if level_b >= max_levels:
        logger.warning(
            "Scale ratio %.2f exceeds pyramid depth %d; using maximum offset",
            ratio,
            max_levels,
        )
        level_b = max_levels - 1

    return (level_a, level_b)
