from __future__ import annotations

import logging
from typing import Tuple

import cv2
import numpy as np
import torch

from src.deep_matching.device_manager import get_device

logger = logging.getLogger(__name__)


class LightGlueMatcher:
    def __init__(self, device: torch.device | None = None, features: str = "superpoint"):
        self.device = device or get_device()
        self.features = features
        self._extractor = None
        self._matcher = None

    def _ensure_models(self):
        if self._extractor is not None:
            return
        try:
            import kornia.feature as kf
            self._extractor = kf.SuperPoint(superglue=None).to(self.device)
            self._matcher = kf.LightGlue(features=self.features).to(self.device)
            self._extractor.eval()
            self._matcher.eval()
        except Exception as e:
            raise RuntimeError(f"Failed to load LightGlue models: {e}")

    def match(
        self, img_a: np.ndarray, img_b: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        self._ensure_models()

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
            feats_a = self._extractor(ta)
            feats_b = self._extractor(tb)
            match_input = {
                "keypoints0": feats_a["keypoints"],
                "descriptors0": feats_a["descriptors"],
                "keypoints1": feats_b["keypoints"],
                "descriptors1": feats_b["descriptors"],
                "scores0": feats_a.get("scores", torch.ones_like(feats_a["keypoints"][0, :, 0])),
                "scores1": feats_b.get("scores", torch.ones_like(feats_b["keypoints"][0, :, 0])),
            }
            matches = self._matcher(match_input)

        mkpts0 = matches["keypoints0"].cpu().numpy()
        mkpts1 = matches["keypoints1"].cpu().numpy()
        confidence = matches.get("confidence", torch.ones(len(mkpts0))).cpu().numpy()

        return mkpts0, mkpts1, confidence
