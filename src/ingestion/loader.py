from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import numpy as np

from src.common.errors import UnsupportedFormatError
from src.common.schema import ImageMetadata
from src.ingestion.geotiff_reader import read_geotiff
from src.ingestion.pds3_reader import read_pds3
from src.ingestion.pds4_reader import read_pds4

logger = logging.getLogger(__name__)


def load_image(path: str) -> Tuple[np.ndarray, ImageMetadata]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = file_path.suffix.lower()

    if suffix == ".xml":
        return read_pds4(path)

    if suffix in (".tif", ".tiff"):
        return read_geotiff(path)

    if suffix in (".img", ".lbl", ".dat", ".raw"):
        label_path = _find_label(file_path)
        if label_path is not None:
            if _is_pds4_label(label_path):
                return read_pds4(str(label_path))
            return read_pds3(str(label_path))

        if suffix in (".img", ".dat", ".raw"):
            label_path = file_path.with_suffix(".lbl")
            if label_path.exists():
                if _is_pds4_label(label_path):
                    return read_pds4(str(label_path))
                return read_pds3(str(label_path))

        raise FileNotFoundError(
            f"No companion label file found for {path}. "
            f"Expected {file_path.with_suffix('.lbl')} or {file_path.with_suffix('.xml')}."
        )

    raise UnsupportedFormatError(
        f"Unsupported file format: {suffix}. "
        f"Supported formats: .xml (PDS4), .tif/.tiff (GeoTIFF), "
        f".img/.lbl/.dat/.raw (PDS3)."
    )


def _find_label(img_path: Path) -> Path | None:
    for ext in [".lbl", ".LBL", ".xml", ".XML"]:
        candidate = img_path.with_suffix(ext)
        if candidate.exists():
            return candidate
    stem = img_path.stem
    parent = img_path.parent
    for ext in [".lbl", ".LBL", ".xml", ".XML"]:
        candidate = parent / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    return None


def _is_pds4_label(label_path: Path) -> bool:
    try:
        head = label_path.read_text(encoding="utf-8", errors="ignore")[:500]
        return "<pds:Product_Observational" in head or "<Product_Observational" in head
    except Exception:
        return False
