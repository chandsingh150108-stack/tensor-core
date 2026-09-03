from __future__ import annotations

import logging

import numpy as np

from src.common.schema import ImageMetadata
from src.routing.router import RegistrationResult, route_and_register

logger = logging.getLogger(__name__)

CONFIG_PATH = "configs/routing.yaml"


def register_with_retry(
    img_a: np.ndarray,
    img_b: np.ndarray,
    meta_a: ImageMetadata,
    meta_b: ImageMetadata,
    config: dict | None = None,
    max_retries: int = 2,
) -> RegistrationResult:
    best_result = RegistrationResult()

    for attempt in range(max_retries + 1):
        result = route_and_register(img_a, img_b, meta_a, meta_b, config)

        if result.success and result.inlier_ratio >= 0.3:
            return result

        if result.inlier_ratio > best_result.inlier_ratio:
            best_result = result

        if attempt < max_retries:
            logger.info(
                "Attempt %d failed (inlier_ratio=%.3f); retrying",
                attempt + 1,
                result.inlier_ratio,
            )

    best_result.success = False
    if not best_result.error_message:
        best_result.error_message = "All retry attempts exhausted"
    return best_result
