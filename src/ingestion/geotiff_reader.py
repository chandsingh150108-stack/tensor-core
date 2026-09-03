from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import numpy as np

from src.common.schema import ImageMetadata

logger = logging.getLogger(__name__)


def read_geotiff(path: str) -> Tuple[np.ndarray, ImageMetadata]:
    try:
        import rasterio
    except ImportError:
        raise ImportError("rasterio is required for GeoTIFF reading: pip install rasterio")

    tif_path = Path(path)
    if not tif_path.exists():
        raise FileNotFoundError(f"GeoTIFF file not found: {path}")

    with rasterio.open(str(tif_path)) as src:
        img_data = src.read(1)
        transform = src.transform
        crs = src.crs
        tags = src.tags()
        dt = src.dtypes[0] if src.dtypes else "uint16"

        lines, samples = img_data.shape
        pixel_scale = abs(transform.a) if transform and transform.a else 1.0
        bit_depth = np.dtype(dt).itemsize * 8

    sun_azimuth = None
    sun_elevation = None
    for key, val in tags.items():
        k = key.lower()
        if "sun_azimuth" in k or "solar_azimuth" in k:
            try:
                sun_azimuth = float(val)
            except (ValueError, TypeError):
                pass
        elif "sun_elevation" in k or "solar_elevation" in k:
            try:
                sun_elevation = float(val)
            except (ValueError, TypeError):
                pass

    meta = ImageMetadata(
        product_id=tif_path.stem,
        sensor="LRO_NAC",
        archive_standard="GEOTIFF",
        pixel_scale_m=float(pixel_scale),
        sun_azimuth_deg=sun_azimuth,
        sun_elevation_deg=sun_elevation,
        image_shape=(lines, samples),
        bit_depth=bit_depth,
        source_path=str(tif_path),
    )
    return img_data, meta
