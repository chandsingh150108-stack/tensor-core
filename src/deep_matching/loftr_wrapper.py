from __future__ import annotations

import logging
from typing import Tuple

import cv2
import numpy as np
import torch

from src.deep_matching.device_manager import get_device

logger = logging.getLogger(__name__)


class LoFTRMatcher:
    def __init__(self, device: torch.device | None = None, pretrained: str = "outdoor"):
        self.device = device or get_device()
        self.pretrained = pretrained
        self._model = None

    def _ensure_model(self):
        if self._model is not None:
            return
        try:
            import kornia.feature as kf
            self._model = kf.LoFTR(pretrained=self.pretrained).to(self.device)
            self._model.eval()
        except Exception as e:
            raise RuntimeError(f"Failed to load LoFTR model: {e}")

    def match(
        self, img_a: np.ndarray, img_b: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        self._ensure_model()

        def _preprocess(img):
            work = img.copy()
            if work.ndim == 3:
                work = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
            work = work.astype(np.float32)
            if work.max() > 1.0:
                work = work / 255.0
            return torch.from_numpy(work).unsqueeze(0).unsqueeze(0).to(self.device)

        ta = _preprocess(img_a)
        tb = _preprocess(img_b)

        with torch.no_grad():
            input_dict = {"image0": ta, "image1": tb}
            matches = self._model(input_dict)

        mkpts0 = matches["keypoints0"].cpu().numpy()
        mkpts1 = matches["keypoints1"].cpu().numpy()
        confidence = matches["confidence"].cpu().numpy()

        return mkpts0, mkpts1, confidence
