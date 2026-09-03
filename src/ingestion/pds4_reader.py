from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Tuple

import numpy as np

from src.common.schema import ImageMetadata

logger = logging.getLogger(__name__)


def _find_element_text(root, tag_path: str):
    parts = tag_path.split("/")
    el = root
    for part in parts:
        found = False
        for child in el:
            local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if local == part:
                el = child
                found = True
                break
        if not found:
            return None
    return el.text


def _parse_float(text):
    if text is None:
        return None
    try:
        return float(text.strip())
    except (ValueError, TypeError):
        return None


def read_pds4(xml_label_path: str) -> Tuple[np.ndarray, ImageMetadata]:
    from xml.etree import ElementTree as ET

    xml_path = Path(xml_label_path)
    if not xml_path.exists():
        raise FileNotFoundError(f"PDS4 XML label not found: {xml_label_path}")

    tree = ET.parse(str(xml_path))
    root = tree.getroot()

    product_id = _find_element_text(root, "Identification_Area/product_name")
    if not product_id:
        product_id = xml_path.stem

    instrument_name = _find_element_text(root, "Observation_Area/Mission_Area/Mission") or ""
    sensor = "TMC2"
    if "OHRC" in instrument_name.upper():
        sensor = "OHRC"

    pixel_scale = None
    for path in [
        "File_Area_Observational/Array_2D_Image/scaling_factor",
        "File_Area_Observational/Array_2D_Image/scale_factor",
        "File_Area_Observational/Array_2D_Image/Scale",
    ]:
        pixel_scale = _parse_float(_find_element_text(root, path))
        if pixel_scale is not None:
            break
    if pixel_scale is None:
        pixel_scale = 1.0

    sun_azimuth = None
    sun_elevation = None
    for az_path in [
        "Observation_Area/Geometry/sun_azimuth",
        "Observation_Area/Geometry/Solar_Azimuth",
        "Observation_Area/Geometry/Sub_Solar_Azimuth",
    ]:
        sun_azimuth = _parse_float(_find_element_text(root, az_path))
        if sun_azimuth is not None:
            break
    for el_path in [
        "Observation_Area/Geometry/sun_elevation",
        "Observation_Area/Geometry/Solar_Elevation",
        "Observation_Area/Geometry/Sub_Solar_Elevation",
    ]:
        sun_elevation = _parse_float(_find_element_text(root, el_path))
        if sun_elevation is not None:
            break

    acq_str = _find_element_text(root, "Observation_Area/Time_Coordinates/start_date_time")
    acq_time = None
    if acq_str:
        try:
            acq_time = datetime.fromisoformat(acq_str.strip().replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass

    binary_path = _resolve_binary_path(xml_path)
    img_data = _read_pds4_binary(root, binary_path)

    lines, samples = img_data.shape[:2] if img_data.size > 0 else (0, 0)

    bit_depth = 16
    depth_str = _find_element_text(root, "File_Area_Observational/Array_2D_Image/Element_Array/data_type")
    if depth_str and "16" in depth_str:
        bit_depth = 16
    elif depth_str and "8" in depth_str:
        bit_depth = 8

    swath = _parse_float(_find_element_text(root, "Observation_Area/Geometry/swath_width"))
    altitude = _parse_float(_find_element_text(root, "Observation_Area/Geometry/Spacecraft_Altitude"))

    meta = ImageMetadata(
        product_id=product_id,
        sensor=sensor,
        archive_standard="PDS4",
        pixel_scale_m=float(pixel_scale),
        swath_km=swath,
        altitude_km=altitude,
        sun_azimuth_deg=sun_azimuth,
        sun_elevation_deg=sun_elevation,
        acquisition_time=acq_time,
        image_shape=(lines, samples),
        bit_depth=bit_depth,
        source_path=str(xml_path),
    )
    return img_data, meta


def _resolve_binary_path(xml_path: Path) -> Path:
    for ext in [".img", ".IMG", ".dat", ".DAT", ".bin"]:
        candidate = xml_path.with_suffix(ext)
        if candidate.exists():
            return candidate
    stem = xml_path.stem
    parent = xml_path.parent
    for f in parent.iterdir():
        if f.suffix.lower() in (".img", ".dat", ".raw", ".bin") and f.stem != stem:
            return f
    return xml_path.with_suffix(".img")


def _read_pds4_binary(root, binary_path: Path) -> np.ndarray:
    if not binary_path.exists():
        raise FileNotFoundError(f"PDS4 image body not found: {binary_path}")

    lines_el = None
    samples_el = None
    for dim in root.iter():
        local = dim.tag.split("}")[-1] if "}" in dim.tag else dim.tag
        if local == "axis_name":
            name = (dim.text or "").strip()
            parent = None
            for p in root.iter():
                for child in p:
                    clocal = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if clocal == "axis_name" and child is dim:
                        parent = p
                        break
            if parent is not None:
                for child in parent:
                    clocal = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if clocal == "axis_length":
                        if name.lower() == "line":
                            lines_el = int(child.text)
                        elif name.lower() == "sample":
                            samples_el = int(child.text)

    if lines_el is None or samples_el is None:
        lines_el = 64
        samples_el = 64

    raw = binary_path.read_bytes()
    expected = lines_el * samples_el * 2
    if len(raw) < expected:
        raise IOError(f"PDS4 body truncated: expected {expected}, got {len(raw)}")

    arr = np.frombuffer(raw[:expected], dtype=np.uint16)
    return arr.reshape(lines_el, samples_el)
