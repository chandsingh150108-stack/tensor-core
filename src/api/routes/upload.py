from __future__ import annotations

import tempfile
import uuid

from fastapi import APIRouter, UploadFile, File

from src.api.schemas import ErrorResponse, UploadResponse, ImageMetadataModel
from src.ingestion.loader import load_image

router = APIRouter()

_image_store: dict[str, tuple] = {}


@router.post("/images/upload", response_model=UploadResponse, responses={422: {"model": ErrorResponse}})
async def upload_image(file: UploadFile = File(...)):
    import os
    import shutil

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename or ".img")[1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        img, meta = load_image(tmp_path)
    except FileNotFoundError:
        base = os.path.splitext(tmp_path)[0]
        for ext in [".img", ".IMG", ".dat", ".DAT", ".raw", ".bin"]:
            candidate = base + ext
            if os.path.exists(candidate):
                try:
                    img, meta = load_image(candidate)
                    break
                except Exception:
                    continue
        else:
            os.unlink(tmp_path)
            raise ValueError(f"Could not load image or find companion files for {file.filename}")
    except Exception as e:
        os.unlink(tmp_path)
        raise ValueError(str(e))

    image_id = str(uuid.uuid4())
    _image_store[image_id] = (img, meta)

    meta_model = ImageMetadataModel(
        product_id=meta.product_id,
        sensor=meta.sensor,
        archive_standard=meta.archive_standard,
        pixel_scale_m=meta.pixel_scale_m,
        swath_km=meta.swath_km,
        altitude_km=meta.altitude_km,
        sun_azimuth_deg=meta.sun_azimuth_deg,
        sun_elevation_deg=meta.sun_elevation_deg,
        acquisition_time=meta.acquisition_time,
        image_shape=meta.image_shape,
        bit_depth=meta.bit_depth,
        source_path=meta.source_path,
    )

    return UploadResponse(image_id=image_id, metadata=meta_model)


def get_stored_image(image_id: str):
    return _image_store.get(image_id)
