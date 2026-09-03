from __future__ import annotations

import logging
from typing import Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def apply_clahe(
    img: np.ndarray,
    clip_limit: float = 2.0,
    tile_grid_size: Tuple[int, int] = (8, 8),
) -> np.ndarray:
    original_dtype = img.dtype

    if img.dtype in (np.uint16, np.int16):
        max_val = np.iinfo(img.dtype).max
        work = (img.astype(np.float64) / max_val * 255).astype(np.uint8)
    elif img.dtype == np.float32 or img.dtype == np.float64:
        work = (np.clip(img, 0, None) * 255).astype(np.uint8) if img.max() <= 1.0 else cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    else:
        work = img.copy()

    if work.ndim == 3:
        lab = cv2.cvtColor(work, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        l_clahe = clahe.apply(l)
        lab_clahe = cv2.merge([l_clahe, a, b])
        result = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
    else:
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        result = clahe.apply(work)

    if original_dtype in (np.uint16, np.int16):
        max_val = np.iinfo(original_dtype).max
        result = (result.astype(np.float64) / 255.0 * max_val).astype(original_dtype)
    elif original_dtype in (np.float32, np.float64):
        result = result.astype(original_dtype) / 255.0

    return result
