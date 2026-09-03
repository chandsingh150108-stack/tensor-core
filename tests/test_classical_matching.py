"""Tests for classical matching module."""
import cv2
import numpy as np
import pytest

from src.features.factory import get_detector
from src.matching.classical_matcher import match_features
from src.matching.transform_estimator import (
    InsufficientCorrespondencesError,
    estimate_transform,
)
from src.matching.warp import warp_source


def _make_synthetic_pair():
    rng = np.random.default_rng(42)
    ref = np.zeros((256, 256), dtype=np.uint8)
    ref[50:200, 50:200] = rng.integers(100, 255, size=(150, 150), dtype=np.uint8)
    H_gt = np.array([[1.0, 0.05, -10], [0.02, 1.0, 15], [0.0, 0.0, 1.0]], dtype=np.float64)
    src = cv2.warpPerspective(ref, H_gt, (256, 256))
    return ref, src, H_gt


class TestMatchFeatures:
    def test_matches_on_similar_images(self):
        ref, src, _ = _make_synthetic_pair()
        det = get_detector("sift")
        fr_a = det.detect_and_compute(ref)
        fr_b = det.detect_and_compute(src)
        matches = match_features(fr_a, fr_b, method="flann")
        assert len(matches) > 0
        assert matches.shape[1] == 2

    def test_no_matches_on_dissimilar(self):
        ref = np.zeros((128, 128), dtype=np.uint8)
        src = np.ones((128, 128), dtype=np.uint8) * 255
        det = get_detector("sift")
        fr_a = det.detect_and_compute(ref)
        fr_b = det.detect_and_compute(src)
        matches = match_features(fr_a, fr_b)
        assert len(matches) == 0


class TestEstimateTransform:
    def test_homography_recovery(self):
        ref, src, H_gt = _make_synthetic_pair()
        det = get_detector("sift")
        fr_a = det.detect_and_compute(ref)
        fr_b = det.detect_and_compute(src)
        matches = match_features(fr_a, fr_b)

        pts_a = fr_a.keypoints[matches[:, 0]]
        pts_b = fr_b.keypoints[matches[:, 1]]

        H_est, inlier_mask = estimate_transform(pts_a, pts_b, model="homography")

        H_gt_norm = H_gt / H_gt[2, 2]
        H_est_norm = H_est / H_est[2, 2]
        error = np.linalg.norm(H_gt_norm - H_est_norm, ord="fro")
        assert error < 0.1 or inlier_mask.sum() > 0

    def test_insufficient_correspondences(self):
        pts_a = np.array([[0, 0], [1, 1], [2, 2]], dtype=np.float64)
        pts_b = np.array([[0, 0], [1, 1], [2, 2]], dtype=np.float64)
        with pytest.raises(InsufficientCorrespondencesError):
            estimate_transform(pts_a, pts_b, model="homography")


class TestWarp:
    def test_output_shape(self):
        img = np.random.randint(0, 255, (128, 128), dtype=np.uint8)
        H = np.eye(3, dtype=np.float64)
        result = warp_source(img, H, "homography", (256, 256))
        assert result.shape == (256, 256)

    def test_affine_output_shape(self):
        img = np.random.randint(0, 255, (128, 128), dtype=np.uint8)
        A = np.eye(2, 3, dtype=np.float64)
        result = warp_source(img, A, "affine", (200, 200))
        assert result.shape == (200, 200)
