from __future__ import annotations

import logging
import math

import cv2
import numpy as np
import yaml

from src.common.schema import ImageMetadata
from src.pyramid.scale_estimator import estimate_scale_ratio

logger = logging.getLogger(__name__)

CONFIG_PATH = "configs/routing.yaml"


def _load_weights(path: str = CONFIG_PATH) -> dict:
    try:
        with open(path) as f:
            cfg = yaml.safe_load(f)
    except FileNotFoundError:
        return {
            "texture_weight": 0.4,
            "illumination_weight": 0.3,
            "scale_weight": 0.3,
        }
    return cfg.get("difficulty", {}).get("weights", {
        "texture_weight": 0.4,
        "illumination_weight": 0.3,
        "scale_weight": 0.3,
    })


def estimate_difficulty(
    img_a: np.ndarray,
    img_b: np.ndarray,
    meta_a: ImageMetadata,
    meta_b: ImageMetadata,
) -> float:
    weights = _load_weights()

    def _texture_score(img):
        if img.ndim == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(img.astype(np.float64), cv2.CV_64F)
        var = laplacian.var()
        max_var = 5000.0
        return max(0.0, min(1.0, 1.0 - var / max_var))

    tex_a = _texture_score(img_a)
    tex_b = _texture_score(img_b)
    texture_difficulty = (tex_a + tex_b) / 2.0

    if meta_a.sun_elevation_deg is not None and meta_b.sun_elevation_deg is not None:
        illum_gap = abs(meta_a.sun_elevation_deg - meta_b.sun_elevation_deg)
        illumination_difficulty = min(1.0, illum_gap / 90.0)
    else:
        illumination_difficulty = 0.5

    try:
        ratio = estimate_scale_ratio(meta_a, meta_b)
        scale_difficulty = min(1.0, abs(math.log2(max(ratio, 0.01))) / 8.0)
    except Exception:
        scale_difficulty = 0.5

    score = (
        weights.get("texture_weight", 0.4) * texture_difficulty
        + weights.get("illumination_weight", 0.3) * illumination_difficulty
        + weights.get("scale_weight", 0.3) * scale_difficulty
    )
    return float(np.clip(score, 0.0, 1.0))
