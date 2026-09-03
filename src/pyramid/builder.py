from __future__ import annotations

import logging
import math
from typing import List, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def build_gaussian_pyramid(img: np.ndarray, levels: int) -> List[np.ndarray]:
    min_dim = min(img.shape[:2])
    max_possible = int(math.log2(min_dim / 16)) + 1 if min_dim >= 16 else 1
    if levels > max_possible:
        logger.warning(
            "Requested %d pyramid levels but image is %s; clamping to %d",
            levels,
            img.shape,
            max_possible,
        )
        levels = max_possible

    if levels < 1:
        levels = 1

    pyramid = [img]
    current = img
    for i in range(levels - 1):
        if min(current.shape[:2]) < 16:
            logger.warning(
                "Pyramid level %d reached minimum size %s; stopping",
                i + 1,
                current.shape,
            )
            break
        down = cv2.pyrDown(current)
        pyramid.append(down)
        current = down

    return pyramid


def build_laplacian_pyramid(gaussian_pyramid: List[np.ndarray]) -> List[np.ndarray]:
    laplacian = []
    for i in range(len(gaussian_pyramid) - 1):
        g_curr = gaussian_pyramid[i]
        g_next = gaussian_pyramid[i + 1]
        upsampled = cv2.pyrUp(g_next, dstsize=(g_curr.shape[1], g_curr.shape[0]))
        lap = cv2.subtract(g_curr, upsampled)
        laplacian.append(lap)

    laplacian.append(gaussian_pyramid[-1])
    return laplacian
