"""Tests for the routing engine."""
import numpy as np
import pytest

from src.common.schema import ImageMetadata
from src.routing.difficulty_estimator import estimate_difficulty
from src.routing.retry_loop import register_with_retry
from src.routing.router import RegistrationResult, route_and_register


def _make_meta(**kwargs):
    defaults = dict(
        product_id="test",
        sensor="TMC2",
        archive_standard="PDS3",
        pixel_scale_m=5.0,
        sun_azimuth_deg=45.0,
        sun_elevation_deg=30.0,
        image_shape=(128, 128),
    )
    defaults.update(kwargs)
    return ImageMetadata(**defaults)


class TestDifficultyEstimator:
    def test_identical_images_low_score(self):
        rng = np.random.default_rng(42)
        img = rng.integers(0, 255, (128, 128), dtype=np.uint8)
        meta = _make_meta()
        score = estimate_difficulty(img, img, meta, meta)
        assert score < 0.5

    def test_different_sun_angles_higher_score(self):
        rng = np.random.default_rng(42)
        img = rng.integers(0, 255, (128, 128), dtype=np.uint8)
        meta_a = _make_meta(sun_elevation_deg=10.0)
        meta_b = _make_meta(sun_elevation_deg=70.0)
        score = estimate_difficulty(img, img, meta_a, meta_b)
        assert score >= 0.19


class TestRouter:
    def test_classical_path_used(self):
        rng = np.random.default_rng(42)
        ref = np.zeros((128, 128), dtype=np.uint8)
        ref[30:90, 30:90] = rng.integers(100, 255, size=(60, 60), dtype=np.uint8)
        src = ref.copy()
        meta_a = _make_meta()
        meta_b = _make_meta()
        result = route_and_register(ref, src, meta_a, meta_b)
        assert isinstance(result, RegistrationResult)
        assert result.matcher_used == "classical"


class TestRetryLoop:
    def test_pathological_pair_returns_failure(self):
        img_a = np.zeros((64, 64), dtype=np.uint8)
        img_b = np.zeros((64, 64), dtype=np.uint8)
        meta = _make_meta()
        result = register_with_retry(img_a, img_b, meta, meta, max_retries=1)
        assert isinstance(result, RegistrationResult)
        assert not result.success or result.inlier_ratio < 0.3
