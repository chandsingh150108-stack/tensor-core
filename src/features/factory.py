from __future__ import annotations

from typing import Literal

from src.features.base import BaseDetector


def get_detector(
    name: Literal["sift", "orb", "akaze"], **params
) -> BaseDetector:
    if name == "sift":
        from src.features.sift_detector import SIFTDetector
        return SIFTDetector(**params)
    elif name == "orb":
        from src.features.orb_detector import ORBDetector
        return ORBDetector(**params)
    elif name == "akaze":
        from src.features.akaze_detector import AKAZEDetector
        return AKAZEDetector(**params)
    else:
        raise ValueError(f"Unknown detector: {name}. Valid options: sift, orb, akaze")
