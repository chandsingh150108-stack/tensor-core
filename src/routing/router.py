from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import yaml

from src.common.schema import ImageMetadata
from src.matching.classical_matcher import match_features
from src.matching.transform_estimator import (
    InsufficientCorrespondencesError,
    TransformEstimationFailedError,
    estimate_transform,
)
from src.routing.difficulty_estimator import estimate_difficulty

logger = logging.getLogger(__name__)

CONFIG_PATH = "configs/routing.yaml"


@dataclass
class RegistrationResult:
    transform: Optional[np.ndarray] = None
    inlier_ratio: float = 0.0
    matcher_used: str = "none"
    difficulty: float = 0.0
    success: bool = False
    error_message: str = ""


def _load_config(path: str = CONFIG_PATH) -> dict:
    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {
            "difficulty_threshold": 0.5,
            "min_inlier_ratio": 0.3,
        }


def route_and_register(
    img_a: np.ndarray,
    img_b: np.ndarray,
    meta_a: ImageMetadata,
    meta_b: ImageMetadata,
    config: dict | None = None,
) -> RegistrationResult:
    cfg = config or _load_config()
    threshold = cfg.get("difficulty_threshold", 0.5)

    if not (0.0 <= threshold <= 1.0):
        raise ValueError(f"difficulty_threshold must be in [0,1], got {threshold}")

    difficulty = estimate_difficulty(img_a, img_b, meta_a, meta_b)

    if difficulty < threshold:
        return _try_classical(img_a, img_b, difficulty)
    else:
        return _try_deep(img_a, img_b, difficulty)


def _try_classical(
    img_a: np.ndarray, img_b: np.ndarray, difficulty: float
) -> RegistrationResult:
    try:
        from src.features.factory import get_detector

        det = get_detector("sift")
        fr_a = det.detect_and_compute(img_a)
        fr_b = det.detect_and_compute(img_b)

        matches = match_features(fr_a, fr_b)
        if len(matches) == 0:
            return RegistrationResult(
                difficulty=difficulty,
                matcher_used="classical",
                error_message="No matches found",
            )

        pts_a = fr_a.keypoints[matches[:, 0]]
        pts_b = fr_b.keypoints[matches[:, 1]]

        transform, inlier_mask = estimate_transform(pts_a, pts_b, model="homography")
        inlier_ratio = inlier_mask.sum() / len(inlier_mask) if len(inlier_mask) > 0 else 0.0

        return RegistrationResult(
            transform=transform,
            inlier_ratio=inlier_ratio,
            matcher_used="classical",
            difficulty=difficulty,
            success=True,
        )
    except (TransformEstimationFailedError, InsufficientCorrespondencesError) as e:
        return RegistrationResult(
            difficulty=difficulty,
            matcher_used="classical",
            error_message=str(e),
        )
    except Exception as e:
        return RegistrationResult(
            difficulty=difficulty,
            matcher_used="classical",
            error_message=f"Classical path failed: {e}",
        )


def _try_deep(
    img_a: np.ndarray, img_b: np.ndarray, difficulty: float
) -> RegistrationResult:
    try:
        import torch
        from src.deep_matching.loftr_wrapper import LoFTRMatcher

        matcher = LoFTRMatcher(device=torch.device("cpu"))
        pts_a, pts_b, confidence = matcher.match(img_a, img_b)

        if len(pts_a) < 4:
            return RegistrationResult(
                difficulty=difficulty,
                matcher_used="deep",
                error_message="Insufficient deep matches",
            )

        transform, inlier_mask = estimate_transform(pts_a, pts_b, model="homography")
        inlier_ratio = inlier_mask.sum() / len(inlier_mask) if len(inlier_mask) > 0 else 0.0

        return RegistrationResult(
            transform=transform,
            inlier_ratio=inlier_ratio,
            matcher_used="deep",
            difficulty=difficulty,
            success=True,
        )
    except Exception as e:
        return RegistrationResult(
            difficulty=difficulty,
            matcher_used="deep",
            error_message=f"Deep path failed: {e}",
        )
