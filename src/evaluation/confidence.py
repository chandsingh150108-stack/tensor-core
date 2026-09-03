from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import yaml

logger = logging.getLogger(__name__)

CONFIG_PATH = "configs/evaluation.yaml"


def _load_weights(path: str = CONFIG_PATH) -> dict:
    try:
        with open(path) as f:
            cfg = yaml.safe_load(f)
    except FileNotFoundError:
        return {
            "ssim_weight": 0.3,
            "mi_weight": 0.2,
            "inlier_ratio_weight": 0.3,
            "corner_reproj_weight": 0.2,
        }
    return cfg.get("confidence", {}).get("weights", {
        "ssim_weight": 0.3,
        "mi_weight": 0.2,
        "inlier_ratio_weight": 0.3,
        "corner_reproj_weight": 0.2,
    })


def composite_confidence(
    metrics: dict[str, Optional[float]],
    weights: dict[str, float] | None = None,
) -> float:
    if weights is None:
        weights = _load_weights()

    available = {}
    if metrics.get("ssim") is not None:
        available["ssim"] = (max(0.0, min(1.0, metrics["ssim"])), weights.get("ssim_weight", 0.3))
    if metrics.get("mutual_information") is not None:
        mi_val = metrics["mutual_information"]
        mi_norm = min(1.0, mi_val / 5.0) if mi_val > 0 else 0.0
        available["mutual_information"] = (mi_norm, weights.get("mi_weight", 0.2))
    if metrics.get("inlier_ratio") is not None:
        available["inlier_ratio"] = (max(0.0, min(1.0, metrics["inlier_ratio"])), weights.get("inlier_ratio_weight", 0.3))
    if metrics.get("corner_reprojection_error") is not None:
        err = metrics["corner_reprojection_error"]
        err_score = max(0.0, 1.0 - err / 10.0) if err is not None else 0.0
        available["corner_reprojection_error"] = (err_score, weights.get("corner_reproj_weight", 0.2))

    if not available:
        return 0.0

    total_weight = sum(w for _, w in available.values())
    if total_weight == 0:
        return 0.0

    score = sum(val * w for val, w in available.values()) / total_weight
    return round(float(np.clip(score * 100, 0, 100)), 2)
