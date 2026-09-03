from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from src.common.schema import ImageMetadata

logger = logging.getLogger(__name__)


def _flatten_label(label) -> dict:
    flat = {}
    for obj_name in label.keys():
        obj = label[obj_name]
        if hasattr(obj, "keys"):
            for key in obj.keys():
                flat[key] = obj[key]
    return flat


def _get_value(flat: dict, key_candidates: list[str], cast_type=None):
    for key in key_candidates:
        if key in flat:
            val = flat[key]
            if hasattr(val, "value"):
                val = val.value
            if cast_type is not None:
                try:
                    val = cast_type(val)
                except (ValueError, TypeError):
                    continue
            return val
    return None


def read_pds3(label_path: str) -> Tuple[np.ndarray, ImageMetadata]:
    try:
        import pvl
    except ImportError:
        raise ImportError("pvl is required for PDS3 label parsing: pip install pvl")

    label_file = Path(label_path)
    if not label_file.exists():
        raise FileNotFoundError(f"Label file not found: {label_path}")

    label = pvl.load(str(label_file))
    flat = _flatten_label(label)

    line_samples = _get_value(flat, ["LINE_SAMPLES", "NS", "ROW_SAMPLES"], int) or 0
    lines = _get_value(flat, ["LINES", "NL", "ROWS"], int) or 0
    sample_bits = _get_value(flat, ["SAMPLE_BITS", "NB"], int) or 16

    product_id = _get_value(flat, ["PRODUCT_ID", "FILE_NAME"], str) or label_file.stem
    sun_azimuth = _get_value(
        flat,
        ["SUB_SOLAR_AZIMUTH", "SOLAR_AZIMUTH", "SOL_AZIMUTH"],
        float,
    )
    sun_elevation = _get_value(
        flat,
        ["SUB_SOLAR_ELEVATION", "SOLAR_ELEVATION", "SOL_ELEVATION"],
        float,
    )

    pixel_scale = _get_value(flat, ["IMAGE_PIXEL_SCALE", "SCALE_FACTOR", "MAP_SCALE"], float) or 1.0

    acq_str = _get_value(
        flat,
        ["START_TIME", "IMAGE_TIME", "EARLY_SAMPLING_TIME"],
        str,
    )
    acq_time = None
    if acq_str:
        try:
            acq_time = datetime.fromisoformat(str(acq_str).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass

    sensor_raw = str(_get_value(flat, ["INSTRUMENT_ID", "MISSION_PHASE_NAME"], str) or "")
    sensor = "LRO_NAC"
    if "TMC2" in sensor_raw.upper():
        sensor = "TMC2"
    elif "OHRC" in sensor_raw.upper():
        sensor = "OHRC"

    body_path = _resolve_body_path(label_file)
    img_data = _read_binary_body(body_path, line_samples, lines, sample_bits)

    meta = ImageMetadata(
        product_id=product_id,
        sensor=sensor,
        archive_standard="PDS3",
        pixel_scale_m=pixel_scale,
        sun_azimuth_deg=sun_azimuth,
        sun_elevation_deg=sun_elevation,
        acquisition_time=acq_time,
        image_shape=(lines, line_samples),
        bit_depth=sample_bits,
        source_path=str(label_file),
    )
    return img_data, meta


def _resolve_body_path(label_file: Path) -> Path:
    for ext in [".img", ".IMG", ".dat", ".DAT", ".raw"]:
        candidate = label_file.with_suffix(ext)
        if candidate.exists():
            return candidate
    stem = label_file.stem
    parent = label_file.parent
    for suffix in ["_body.img", "_BODY.IMG", ".img", ".IMG"]:
        candidate = parent / f"{stem}{suffix}"
        if candidate.exists():
            return candidate
    for f in parent.iterdir():
        if f.suffix.lower() in (".img", ".dat", ".raw") and f.stem != label_file.stem:
            return f
    return label_file.with_suffix(".img")


def _read_binary_body(
    body_path: Path, samples: int, lines: int, bits: int
) -> np.ndarray:
    if not body_path.exists():
        raise FileNotFoundError(f"Image body not found: {body_path}")

    dtype = np.uint16 if bits >= 16 else np.uint8
    expected_bytes = samples * lines * np.dtype(dtype).itemsize

    raw = body_path.read_bytes()
    if len(raw) < expected_bytes:
        raise IOError(
            f"Image body truncated: expected {expected_bytes} bytes, got {len(raw)}"
        )

    if bits == 12:
        arr = np.frombuffer(raw[: samples * lines * 2], dtype=np.uint16)
        arr = arr & 0x0FFF
    else:
        arr = np.frombuffer(raw[:expected_bytes], dtype=dtype)

    return arr.reshape(lines, samples)
