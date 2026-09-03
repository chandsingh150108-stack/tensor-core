from __future__ import annotations

import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def shadow_aware_normalize(
    img: np.ndarray, shadow_thresh_percentile: float = 5.0
) -> np.ndarray:
    if img.size == 0 or (img == 0).all():
        return img.copy()

    if img.dtype != np.float64:
        work = img.astype(np.float64)
    else:
        work = img.copy()

    flat = work.flatten()
    non_zero = flat[flat > 0]
    if non_zero.size == 0:
        return img.copy()

    thresh = np.percentile(non_zero, shadow_thresh_percentile)
    shadow_mask = ((work > 0) & (work <= thresh)).astype(np.float64)

    if shadow_mask.sum() == 0:
        return img.copy()

    illuminated = work[work > 0]
    if illuminated.size == 0:
        return img.copy()

    mean_illuminated = illuminated.mean()
    if mean_illuminated <= 0:
        return img.copy()

    result = work.copy()
    shadow_pixels = work[shadow_mask.astype(bool)]
    if shadow_pixels.size > 0:
        mean_shadow = shadow_pixels.mean()
        if mean_shadow > 0:
            gamma = np.log(mean_illuminated * 0.8) / np.log(mean_shadow)
            gamma = np.clip(gamma, 0.5, 3.0)
            normalized = np.power(work[shadow_mask.astype(bool)] / mean_shadow, gamma) * mean_illuminated
            result[shadow_mask.astype(bool)] = np.clip(normalized, 0, work.max())

    kernel_size = max(3, min(work.shape) // 16)
    if kernel_size % 2 == 0:
        kernel_size += 1
    blur_mask = cv2.GaussianBlur(
        shadow_mask, (kernel_size, kernel_size), 0
    )
    blur_mask = np.clip(blur_mask, 0, 1)

    final = blur_mask * result + (1 - blur_mask) * work

    if img.dtype != np.float64:
        return final.astype(img.dtype)
    return final
