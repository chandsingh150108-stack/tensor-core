from __future__ import annotations

import logging
import mmap
import os
import re
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


def _find_any_text(root, paths):
    for path in paths:
        text = _find_element_text(root, path)
        if text is not None:
            return text
    return None


def _parse_float(text):
    if text is None:
        return None
    try:
        return float(text.strip())
    except (ValueError, TypeError):
        return None


def _find_isda_text(root, local_name):
    for el in root.iter():
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if tag == local_name:
            return el.text
    return None


def _find_sun_metadata(root):
    sun_azimuth = None
    sun_elevation = None

    sun_azimuth = _parse_float(_find_isda_text(root, "sun_azimuth"))
    sun_elevation = _parse_float(_find_isda_text(root, "sun_elevation"))

    if sun_azimuth is None:
        sun_azimuth = _parse_float(_find_isda_text(root, "Solar_Azimuth"))
    if sun_elevation is None:
        sun_elevation = _parse_float(_find_isda_text(root, "Solar_Elevation"))
    if sun_azimuth is None:
        sun_azimuth = _parse_float(_find_isda_text(root, "Sub_Solar_Azimuth"))
    if sun_elevation is None:
        sun_elevation = _parse_float(_find_isda_text(root, "Sub_Solar_Elevation"))

    return sun_azimuth, sun_elevation


def read_pds4(xml_label_path: str) -> Tuple[np.ndarray, ImageMetadata]:
    from xml.etree import ElementTree as ET

    xml_path = Path(xml_label_path)
    if not xml_path.exists():
        raise FileNotFoundError(f"PDS4 XML label not found: {xml_label_path}")

    tree = ET.parse(str(xml_path))
    root = tree.getroot()

    product_id = _find_element_text(root, "Identification_Area/product_name")
    if not product_id:
        logical_id = _find_element_text(root, "Identification_Area/logical_identifier")
        if logical_id:
            product_id = logical_id.split(":")[-1]
        else:
            product_id = xml_path.stem

    instrument_name = ""
    for inst_el in root.iter():
        tag = inst_el.tag.split("}")[-1] if "}" in inst_el.tag else inst_el.tag
        if tag == "name" and inst_el.text:
            parent_tag = ""
            for parent in root.iter():
                for child in parent:
                    if child is inst_el:
                        ptag = parent.tag.split("}")[-1] if "}" in parent.tag else parent.tag
                        parent_tag = ptag
                        break
            if parent_tag == "Observing_System_Component":
                instrument_name = inst_el.text
                break

    sensor = "TMC2"
    if "OHRC" in instrument_name.upper():
        sensor = "OHRC"
    elif "TMC" in instrument_name.upper():
        sensor = "TMC2"
    elif "IIRS" in instrument_name.upper():
        sensor = "IIRS"

    pixel_scale = None
    for path in [
        "File_Area_Observational/Array_2D_Image/scaling_factor",
        "File_Area_Observational/Array_2D_Image/scale_factor",
        "File_Area_Observational/Array_2D_Image/Scale",
    ]:
        pixel_scale = _parse_float(_find_element_text(root, path))
        if pixel_scale is not None:
            break

    sun_azimuth, sun_elevation = _find_sun_metadata(root)

    pixel_resolution = _parse_float(_find_isda_text(root, "pixel_resolution"))
    if pixel_scale is None and pixel_resolution is not None:
        pixel_scale = pixel_resolution

    if pixel_scale is None:
        pixel_scale = 1.0

    acq_str = _find_element_text(root, "Observation_Area/Time_Coordinates/start_date_time")
    acq_time = None
    if acq_str:
        try:
            acq_time = datetime.fromisoformat(acq_str.strip().replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass

    lines_el, samples_el, data_type_str = _parse_array_shape(root)

    binary_path = _resolve_binary_path(xml_path)
    img_data = _read_pds4_binary_mmap(binary_path, lines_el, samples_el, data_type_str)

    lines, samples = img_data.shape[:2] if img_data.size > 0 else (0, 0)

    bit_depth = 16
    if data_type_str and "8" in data_type_str:
        bit_depth = 8
    elif data_type_str and "32" in data_type_str:
        bit_depth = 32

    swath = _parse_float(_find_isda_text(root, "swath_width"))
    altitude = _parse_float(_find_isda_text(root, "spacecraft_altitude"))

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


def _parse_array_shape(root):
    lines_el = None
    samples_el = None
    data_type_str = None

    for array_el in root.iter():
        tag = array_el.tag.split("}")[-1] if "}" in array_el.tag else array_el.tag
        if tag == "Element_Array":
            for child in array_el:
                ctag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if ctag == "data_type":
                    data_type_str = (child.text or "").strip()

    for axis_array in root.iter():
        tag = axis_array.tag.split("}")[-1] if "}" in axis_array.tag else axis_array.tag
        if tag in ("Axis_Array", "Array_Dimension_Axis"):
            axis_name = None
            axis_count = None
            for child in axis_array:
                ctag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if ctag == "axis_name":
                    axis_name = (child.text or "").strip().lower()
                elif ctag in ("elements", "axis_length"):
                    try:
                        axis_count = int((child.text or "").strip())
                    except (ValueError, TypeError):
                        pass
            if axis_name == "line" and axis_count is not None:
                lines_el = axis_count
            elif axis_name == "sample" and axis_count is not None:
                samples_el = axis_count

    if lines_el is None or samples_el is None:
        logger.warning("Could not parse array shape from XML; defaulting to 64x64")
        lines_el = lines_el or 64
        samples_el = samples_el or 64

    return lines_el, samples_el, data_type_str


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


def _read_pds4_binary_mmap(binary_path: Path, lines: int, samples: int, data_type_str: str = None) -> np.ndarray:
    if not binary_path.exists():
        raise FileNotFoundError(f"PDS4 image body not found: {binary_path}")

    dtype = np.uint16
    if data_type_str:
        dt_lower = data_type_str.lower()
        if "unsignedlsb1" in dt_lower or "uint8" in dt_lower:
            dtype = np.uint8
        elif "unsignedlsb2" in dt_lower or "uint16" in dt_lower:
            dtype = np.uint16
        elif "signedlsb4" in dt_lower or "int32" in dt_lower:
            dtype = np.int32
        elif "unsignedlsb4" in dt_lower or "uint32" in dt_lower:
            dtype = np.uint32
        elif "real" in dt_lower or "float" in dt_lower:
            dtype = np.float32

    item_size = np.dtype(dtype).itemsize
    expected_bytes = lines * samples * item_size
    file_size = binary_path.stat().st_size

    if file_size < expected_bytes:
        raise IOError(
            f"PDS4 body truncated: expected {expected_bytes} bytes "
            f"({lines}x{samples}x{item_size}), got {file_size}"
        )

    file_size_gb = file_size / (1024 ** 3)
    logger.info(
        "Loading PDS4 image: %dx%d %s (%.1f GB file)",
        lines, samples, dtype, file_size_gb,
    )

    if file_size > 500 * 1024 * 1024:
        logger.info("Large file detected; using memory mapping")
        return _mmap_read(binary_path, lines, samples, dtype, expected_bytes)

    raw = binary_path.read_bytes()
    arr = np.frombuffer(raw[:expected_bytes], dtype=dtype)
    return arr.reshape(lines, samples)


def _mmap_read(binary_path: Path, lines: int, samples: int, dtype, expected_bytes: int) -> np.ndarray:
    with open(binary_path, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            raw = mm[:expected_bytes]
        finally:
            mm.close()

    arr = np.frombuffer(raw, dtype=dtype)
    return arr.reshape(lines, samples)
