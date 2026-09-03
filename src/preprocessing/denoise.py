from __future__ import annotations

import logging
from typing import Literal

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def denoise(
    img: np.ndarray, method: Literal["nlm", "bilateral", "median"] = "nlm"
) -> np.ndarray:
    original_dtype = img.dtype
    if img.dtype != np.float32:
        work = img.astype(np.float32)
    else:
        work = img.copy()

    if work.ndim == 3:
        work_8u = cv2.normalize(work, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    else:
        work_8u = cv2.normalize(work, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    if method == "nlm":
        denorm = cv2.fastNlMeansDenoising(work_8u, None, h=10, templateWindowSize=7, searchWindowSize=21)
    elif method == "bilateral":
        denorm = cv2.bilateralFilter(work_8u, d=9, sigmaColor=75, sigmaSpace=75)
    elif method == "median":
        denorm = cv2.medianBlur(work_8u, ksize=5)
    else:
        raise ValueError(f"Unknown denoise method: {method}")

    result = denorm.astype(np.float32) / 255.0
    range_val = float(work.max() - work.min()) if work.max() > work.min() else 1.0
    result = result * range_val + float(work.min())

    return result.astype(original_dtype)
