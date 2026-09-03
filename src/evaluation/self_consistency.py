from __future__ import annotations

import logging

import numpy as np

from src.common.schema import ImageMetadata
from src.routing.retry_loop import register_with_retry

logger = logging.getLogger(__name__)


def forward_backward_rmse(
    img_a: np.ndarray,
    img_b: np.ndarray,
    meta_a: ImageMetadata,
    meta_b: ImageMetadata,
    config: dict | None = None,
    grid_size: int = 10,
) -> float:
    result_ab = register_with_retry(img_a, img_b, meta_a, meta_b, config)
    result_ba = register_with_retry(img_b, img_a, meta_b, meta_a, config)

    if not result_ab.success or not result_ba.success:
        logger.warning("Forward or backward registration failed; returning inf")
        return float("inf")

    if result_ab.transform is None or result_ba.transform is None:
        return float("inf")

    h, w = img_a.shape[:2]
    grid_x = np.linspace(0, w - 1, grid_size)
    grid_y = np.linspace(0, h - 1, grid_size)
    grid_xx, grid_yy = np.meshgrid(grid_x, grid_y)
    pts = np.stack([grid_xx.ravel(), grid_yy.ravel()], axis=-1).astype(np.float64)

    if result_ab.transform.shape == (3, 3) and result_ba.transform.shape == (3, 3):
        pts_h = np.hstack([pts, np.ones((len(pts), 1))])
        pts_ab = (result_ab.transform @ pts_h.T).T
        pts_ab = pts_ab[:, :2] / pts_ab[:, 2:3]

        pts_ba_h = np.hstack([pts_ab, np.ones((len(pts_ab), 1))])
        pts_composed = (result_ba.transform @ pts_ba_h.T).T
        pts_composed = pts_composed[:, :2] / pts_composed[:, 2:3]

        rmse = np.sqrt(np.mean(np.sum((pts_composed - pts) ** 2, axis=1)))
        return float(rmse)

    return float("inf")
