from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional, Tuple

from pydantic import BaseModel


class ImageMetadataModel(BaseModel):
    product_id: str
    sensor: Literal["TMC2", "OHRC"]
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


class UploadResponse(BaseModel):
    image_id: str
    metadata: ImageMetadataModel


class RegisterRequest(BaseModel):
    source_image_id: str
    reference_image_id: str
    params: dict = {}


class RegisterResponse(BaseModel):
    job_id: str
    status: str = "pending"


class JobStatus(BaseModel):
    job_id: str
    status: str
    result: Optional[dict] = None


class ReportResponse(BaseModel):
    job_id: str
    status: str
    metrics: Optional[dict] = None
    confidence: Optional[float] = None


class ErrorResponse(BaseModel):
    detail: str
