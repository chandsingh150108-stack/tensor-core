from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional, Tuple


@dataclass(frozen=True)
class ImageMetadata:
    product_id: str
    sensor: Literal["TMC2", "OHRC", "LRO_NAC"]
    archive_standard: Literal["PDS3", "PDS4", "GEOTIFF"]
    pixel_scale_m: float
    swath_km: Optional[float] = None
    altitude_km: Optional[float] = None
    sun_azimuth_deg: Optional[float] = None
    sun_elevation_deg: Optional[float] = None
    acquisition_time: Optional[datetime] = None
    image_shape: Tuple[int, int] = (0, 0)
    bit_depth: int = 16
    source_path: str = ""

    def __post_init__(self) -> None:
        if self.sun_azimuth_deg is not None and not (0 <= self.sun_azimuth_deg < 360):
            raise ValueError(
                f"sun_azimuth_deg must be in [0, 360), got {self.sun_azimuth_deg}"
            )
        if self.sun_elevation_deg is not None and not (-90 <= self.sun_elevation_deg <= 90):
            raise ValueError(
                f"sun_elevation_deg must be in [-90, 90], got {self.sun_elevation_deg}"
            )
        if self.pixel_scale_m <= 0:
            raise ValueError(f"pixel_scale_m must be positive, got {self.pixel_scale_m}")
