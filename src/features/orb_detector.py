from __future__ import annotations

import cv2
import numpy as np

from src.features.base import BaseDetector, FeatureResult, ImageTooSmallError

ALLOWED_PARAMS = {"nfeatures", "scaleFactor", "nlevels", "edgeThreshold", "firstLevel", "WTA_K", "scoreType", "patchSize", "fastThreshold"}


class ORBDetector(BaseDetector):
    def __init__(self, **params):
        bad_keys = set(params.keys()) - ALLOWED_PARAMS
        if bad_keys:
            raise ValueError(f"Unknown ORB parameters: {bad_keys}")
        self._detector = cv2.ORB_create(**params)

    def detect_and_compute(self, img: np.ndarray) -> FeatureResult:
        self._validate_image(img)
        work = img.copy()
        if work.dtype != np.uint8:
            if work.max() <= 1.0:
                work = (work * 255).astype(np.uint8)
            else:
                work = cv2.normalize(work, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            import logging
            logging.getLogger(__name__).warning("Converted non-uint8 input to uint8 for ORB")

        if work.ndim == 3:
            work = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)

        keypoints, descriptors = self._detector.detectAndCompute(work, None)

        if not keypoints or len(keypoints) == 0:
            return FeatureResult(
                keypoints=np.empty((0, 2), dtype=np.float32),
                descriptors=np.empty((0, 32), dtype=np.uint8),
                responses=np.empty((0,), dtype=np.float32),
                detector_name="orb",
            )

        kps = np.array([[kp.pt[0], kp.pt[1]] for kp in keypoints], dtype=np.float32)
        resps = np.array([kp.response for kp in keypoints], dtype=np.float32)

        return FeatureResult(
            keypoints=kps,
            descriptors=descriptors,
            responses=resps,
            detector_name="orb",
        )
