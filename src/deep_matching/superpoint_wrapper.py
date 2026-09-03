from __future__ import annotations

import logging

import cv2
import numpy as np
import torch

from src.deep_matching.device_manager import get_device
from src.features.base import FeatureResult

logger = logging.getLogger(__name__)


class ModelWeightsUnavailableError(Exception):
    """Raised when model weights cannot be loaded."""


class SuperPointExtractor:
    def __init__(self, device: torch.device | None = None):
        self.device = device or get_device()
        try:
            import kornia
            self._has_kornia = True
        except ImportError:
            self._has_kornia = False
            logger.warning("Kornia not available; SuperPoint will use fallback")

    def detect_and_compute(self, img: np.ndarray) -> FeatureResult:
        if not self._has_kornia:
            return self._fallback_detect(img)

        work = img.copy()
        if work.ndim == 3:
            work = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
        work = work.astype(np.float32) / 255.0 if work.max() > 1.0 else work.astype(np.float32)

        try:
            import kornia.feature as kf
            detector = kf.SuperPoint(superglue=None).to(self.device)
            tensor = torch.from_numpy(work).unsqueeze(0).unsqueeze(0).to(self.device)

            with torch.no_grad():
                features = detector(tensor)

            kpts = features.get("keypoints", [torch.empty(0, 2)])[0]
            descs = features.get("descriptors", [torch.empty(0, 256)])[0]
            scores = features.get("scores", [torch.empty(0)])[0]

            kpts_np = kpts.cpu().numpy().astype(np.float32)
            descs_np = descs.cpu().numpy().astype(np.float32)
            scores_np = scores.cpu().numpy().astype(np.float32)

            return FeatureResult(
                keypoints=kpts_np,
                descriptors=descs_np,
                responses=scores_np,
                detector_name="superpoint",
            )
        except Exception as e:
            logger.warning("SuperPoint failed: %s; using fallback", e)
            return self._fallback_detect(img)

    def _fallback_detect(self, img: np.ndarray) -> FeatureResult:
        det = cv2.SIFT_create(nfeatures=500)
        work = img.copy()
        if work.dtype != np.uint8:
            work = cv2.normalize(work, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        if work.ndim == 3:
            work = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)

        kps, descs = det.detectAndCompute(work, None)
        if not kps:
            return FeatureResult(
                keypoints=np.empty((0, 2), dtype=np.float32),
                descriptors=np.empty((0, 128), dtype=np.float32),
                responses=np.empty(0, dtype=np.float32),
                detector_name="superpoint_fallback",
            )

        kps_np = np.array([[kp.pt[0], kp.pt[1]] for kp in kps], dtype=np.float32)
        scores_np = np.array([kp.response for kp in kps], dtype=np.float32)
        return FeatureResult(
            keypoints=kps_np,
            descriptors=descs.astype(np.float32),
            responses=scores_np,
            detector_name="superpoint_fallback",
        )
