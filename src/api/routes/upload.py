from __future__ import annotations

import os
import shutil
import tempfile
import uuid

from fastapi import APIRouter, UploadFile, File, Query

from src.api.schemas import ErrorResponse, UploadResponse, ImageMetadataModel
from src.ingestion.loader import load_image

router = APIRouter()

_image_store: dict[str, tuple] = {}
_upload_dirs: dict[str, str] = {}

CHUNK_SIZE = 8 * 1024 * 1024


def _stream_upload_to_file(file: UploadFile, dest_path: str) -> int:
    total = 0
    with open(dest_path, "wb") as out:
        while True:
            chunk = file.file.read(CHUNK_SIZE)
            if not chunk:
                break
            out.write(chunk)
            total += len(chunk)
    return total


def _find_companion(xml_path: str):
    base_dir = os.path.dirname(xml_path)
    base_name = os.path.splitext(os.path.basename(xml_path))[0]

    for ext in [".img", ".IMG", ".dat", ".DAT", ".raw", ".bin"]:
        candidate = os.path.join(base_dir, base_name + ext)
        if os.path.exists(candidate):
            return candidate

    for f in os.listdir(base_dir):
        full = os.path.join(base_dir, f)
        if os.path.isfile(full) and f.lower().endswith((".img", ".dat", ".raw", ".bin")):
            return full

    return None


@router.post("/images/upload", response_model=UploadResponse, responses={422: {"model": ErrorResponse}})
async def upload_image(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename or ".img")[1]
    upload_dir = tempfile.mkdtemp(prefix="lunar_upload_")
    tmp_path = os.path.join(upload_dir, f"data{suffix}")

    try:
        _stream_upload_to_file(file, tmp_path)
    except Exception:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise ValueError(f"Failed to upload {file.filename}")

    try:
        img, meta = load_image(tmp_path)
    except FileNotFoundError:
        companion = _find_companion(tmp_path)
        if companion:
            try:
                img, meta = load_image(companion)
            except Exception as e:
                shutil.rmtree(upload_dir, ignore_errors=True)
                raise ValueError(f"Could not load image: {e}")
        else:
            shutil.rmtree(upload_dir, ignore_errors=True)
            raise ValueError(f"Could not load image or find companion files for {file.filename}")
    except Exception as e:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise ValueError(str(e))

    image_id = str(uuid.uuid4())
    _image_store[image_id] = (img, meta)
    _upload_dirs[image_id] = upload_dir

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


@router.post("/images/load-local", response_model=UploadResponse, responses={422: {"model": ErrorResponse}})
async def load_local_image(path: str = Query(..., description="Path to XML label or image file")):
    if not os.path.exists(path):
        raise ValueError(f"File not found: {path}")

    try:
        img, meta = load_image(path)
    except FileNotFoundError:
        raise ValueError(f"Could not load image from {path}")
    except Exception as e:
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
