from __future__ import annotations

import cv2
import numpy as np


def warp_source(
    src_img: np.ndarray,
    transform: np.ndarray,
    model: str,
    output_shape: tuple[int, int],
) -> np.ndarray:
    h, w = output_shape

    if model == "homography":
        return cv2.warpPerspective(src_img, transform, (w, h))
    elif model == "affine":
        return cv2.warpAffine(src_img, transform, (w, h))
    elif model == "tps":
        if hasattr(transform, "warpImage"):
            map_x, map_y = transform.warpImage(src_img)
            return cv2.remap(src_img, map_x, map_y, cv2.INTER_LINEAR)
        else:
            h_src, w_src = src_img.shape[:2]
            grid_x, grid_y = np.meshgrid(np.arange(w), np.arange(h))
            grid_xy = np.stack([grid_x.ravel(), grid_y.ravel()], axis=-1).astype(np.float32)
            pts_src = grid_xy.reshape(1, -1, 2)
            pts_dst = transform.applyTransformation(pts_src)[0]
            map_x = pts_dst[0, :, 0].reshape(h, w).astype(np.float32)
            map_y = pts_dst[0, :, 1].reshape(h, w).astype(np.float32)
            return cv2.remap(src_img, map_x, map_y, cv2.INTER_LINEAR)
    else:
        raise ValueError(f"Unknown model: {model}")
