from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class FeatureResult:
    keypoints: np.ndarray  # Nx2 float32, x,y
    descriptors: np.ndarray  # NxD
    responses: np.ndarray  # N,
    detector_name: str


class BaseDetector(ABC):
    @abstractmethod
    def detect_and_compute(self, img: np.ndarray) -> FeatureResult:
        ...

    def _validate_image(self, img: np.ndarray, min_size: int = 16) -> None:
        if img.shape[0] < min_size or img.shape[1] < min_size:
            from src.features.base import ImageTooSmallError
            raise ImageTooSmallError(
                f"Image shape {img.shape} is smaller than minimum {min_size}x{min_size}"
            )


class ImageTooSmallError(Exception):
    """Raised when an image is smaller than the detector's minimum patch size."""
