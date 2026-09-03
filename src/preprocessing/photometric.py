from __future__ import annotations

import logging
import math

import numpy as np

from src.common.schema import ImageMetadata

logger = logging.getLogger(__name__)


def photometric_correct(img: np.ndarray, meta: ImageMetadata) -> np.ndarray:
    if meta.sun_elevation_deg is None:
        logger.warning(
            "sun_elevation_deg is None for %s; skipping photometric correction",
            meta.product_id,
        )
        return img.copy()

    sun_elev_rad = math.radians(meta.sun_elevation_deg)
    cos_incidence = math.sin(sun_elev_rad)

    if abs(cos_incidence) < 1e-6:
        logger.warning(
            "Sun elevation too low (%.2f deg) for photometric correction; returning unchanged",
            meta.sun_elevation_deg,
        )
        return img.copy()

    if img.dtype != np.float64:
        work = img.astype(np.float64)
    else:
        work = img.copy()

    k = 0.6
    if work.max() > 0:
        normalized = work / work.max()
    else:
        return img.copy()

    corrected = normalized * math.pow(cos_incidence, k - 1)
    corrected = corrected * work.max()

    if img.dtype != np.float64:
        return corrected.astype(img.dtype)
    return corrected
