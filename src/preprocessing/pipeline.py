from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import yaml

from src.common.schema import ImageMetadata
from src.preprocessing.clahe import apply_clahe
from src.preprocessing.denoise import denoise
from src.preprocessing.photometric import photometric_correct
from src.preprocessing.shadow_normalize import shadow_aware_normalize

logger = logging.getLogger(__name__)

CONFIG_PATH = "configs/preprocessing.yaml"


@dataclass
class PipelineConfig:
    denoise_enabled: bool = True
    denoise_method: str = "nlm"
    photometric_enabled: bool = True
    shadow_normalize_enabled: bool = True
    shadow_percentile: float = 5.0
    clahe_enabled: bool = True
    clahe_clip_limit: float = 2.0
    clahe_tile_grid: tuple[int, int] = (8, 8)


def load_pipeline_config(path: str = CONFIG_PATH) -> PipelineConfig:
    try:
        with open(path) as f:
            cfg = yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning("Config %s not found; using defaults", path)
        return PipelineConfig()

    stages = cfg.get("stages", {})
    denoise_cfg = stages.get("denoise", {})
    clahe_cfg = stages.get("clahe", {})
    shadow_cfg = stages.get("shadow_normalize", {})
    photometric_cfg = stages.get("photometric", {})

    return PipelineConfig(
        denoise_enabled=denoise_cfg.get("enabled", True),
        denoise_method=denoise_cfg.get("method", "nlm"),
        photometric_enabled=photometric_cfg.get("enabled", True),
        shadow_normalize_enabled=shadow_cfg.get("enabled", True),
        shadow_percentile=shadow_cfg.get("percentile", 5.0),
        clahe_enabled=clahe_cfg.get("enabled", True),
        clahe_clip_limit=clahe_cfg.get("clip_limit", 2.0),
        clahe_tile_grid=tuple(clahe_cfg.get("tile_grid_size", [8, 8])),
    )


class PreprocessingPipeline:
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or load_pipeline_config()

    def run(self, img: np.ndarray, meta: ImageMetadata) -> np.ndarray:
        result = img.copy()

        if np.all(result == 0):
            logger.warning("All-zero image; returning unchanged")
            return result

        if np.any(np.isnan(result.astype(np.float64))) or np.any(np.isinf(result.astype(np.float64))):
            logger.warning("NaN/Inf detected in image; replacing with zeros")
            mask = np.isnan(result.astype(np.float64)) | np.isinf(result.astype(np.float64))
            result = result.copy()
            result[mask] = 0

        if self.config.denoise_enabled:
            result = denoise(result, method=self.config.denoise_method)

        if self.config.photometric_enabled:
            result = photometric_correct(result, meta)

        if self.config.shadow_normalize_enabled:
            result = shadow_aware_normalize(
                result, shadow_thresh_percentile=self.config.shadow_percentile
            )

        if self.config.clahe_enabled:
            result = apply_clahe(
                result,
                clip_limit=self.config.clahe_clip_limit,
                tile_grid_size=self.config.clahe_tile_grid,
            )

        return result
