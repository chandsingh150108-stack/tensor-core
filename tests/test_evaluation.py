"""Tests for the evaluation module."""
import numpy as np
import pytest

from src.evaluation.confidence import composite_confidence
from src.evaluation.metrics import (
    compute_inlier_ratio,
    compute_mutual_information,
    compute_ssim,
)


class TestSSIM:
    def test_identical_images(self):
        img = np.random.randint(0, 255, (64, 64), dtype=np.uint8)
        ssim = compute_ssim(img, img)
        assert ssim >= 0.99

    def test_shape_mismatch_raises(self):
        a = np.zeros((64, 64), dtype=np.uint8)
        b = np.zeros((32, 32), dtype=np.uint8)
        with pytest.raises(ValueError, match="Shape mismatch"):
            compute_ssim(a, b)


class TestMutualInformation:
    def test_identical_higher_than_random(self):
        img = np.random.randint(0, 255, (64, 64), dtype=np.uint8)
        random_img = np.random.randint(0, 255, (64, 64), dtype=np.uint8)
        mi_same = compute_mutual_information(img, img)
        mi_diff = compute_mutual_information(img, random_img)
        assert mi_same > mi_diff


class TestInlierRatio:
    def test_all_inliers(self):
        mask = np.ones(100, dtype=bool)
        assert compute_inlier_ratio(mask) == 1.0

    def test_empty(self):
        mask = np.array([], dtype=bool)
        assert compute_inlier_ratio(mask) == 0.0


class TestCompositeConfidence:
    def test_with_all_metrics(self):
        metrics = {
            "ssim": 0.95,
            "mutual_information": 3.0,
            "inlier_ratio": 0.9,
            "corner_reprojection_error": 0.5,
        }
        score = composite_confidence(metrics)
        assert 0 <= score <= 100

    def test_with_missing_corner_error(self):
        metrics = {
            "ssim": 0.95,
            "mutual_information": 3.0,
            "inlier_ratio": 0.9,
            "corner_reprojection_error": None,
        }
        score = composite_confidence(metrics)
        assert 0 <= score <= 100
        assert not np.isnan(score)

    def test_empty_metrics(self):
        score = composite_confidence({})
        assert score == 0.0
