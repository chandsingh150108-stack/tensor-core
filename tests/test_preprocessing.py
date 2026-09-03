"""Tests for the preprocessing module."""
import os

import numpy as np
import pytest

from src.common.schema import ImageMetadata
from src.preprocessing.clahe import apply_clahe
from src.preprocessing.denoise import denoise
from src.preprocessing.photometric import photometric_correct
from src.preprocessing.pipeline import PreprocessingPipeline
from src.preprocessing.shadow_normalize import shadow_aware_normalize

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _make_meta(**kwargs):
    defaults = dict(
        product_id="test",
        sensor="TMC2",
        archive_standard="PDS3",
        pixel_scale_m=5.0,
        sun_azimuth_deg=45.0,
        sun_elevation_deg=30.0,
        image_shape=(64, 64),
    )
    defaults.update(kwargs)
    return ImageMetadata(**defaults)


class TestDenoise:
    def test_output_shape_matches_input(self):
        img = np.random.randint(0, 255, (64, 64), dtype=np.uint8)
        result = denoise(img, method="nlm")
        assert result.shape == img.shape
        assert result.dtype == img.dtype

    def test_output_shape_3d(self):
        img = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        result = denoise(img, method="bilateral")
        assert result.shape == img.shape


class TestCLAHE:
    def test_output_shape_matches_input(self):
        img = np.random.randint(0, 255, (64, 64), dtype=np.uint8)
        result = apply_clahe(img)
        assert result.shape == img.shape

    def test_increases_contrast(self):
        gradient = np.tile(np.arange(64, dtype=np.uint8), (64, 1))
        std_before = np.std(gradient)
        result = apply_clahe(gradient, clip_limit=3.0)
        std_after = np.std(result)
        assert std_after >= std_before * 0.8

    def test_uint16_input(self):
        img = np.random.randint(0, 65535, (64, 64), dtype=np.uint16)
        result = apply_clahe(img)
        assert result.shape == img.shape
        assert result.dtype == np.uint16


class TestShadowNormalize:
    def test_all_zero_returns_unchanged(self):
        img = np.zeros((64, 64), dtype=np.uint16)
        result = shadow_aware_normalize(img)
        np.testing.assert_array_equal(result, img)

    def test_output_shape(self):
        img = np.random.rand(64, 64).astype(np.float64) * 255
        result = shadow_aware_normalize(img)
        assert result.shape == img.shape


class TestPhotometricCorrect:
    def test_no_sun_angle_returns_unchanged(self):
        img = np.random.randint(0, 255, (64, 64), dtype=np.uint16)
        meta = _make_meta(sun_elevation_deg=None)
        result = photometric_correct(img, meta)
        assert np.array_equal(result, img)

    def test_output_shape(self):
        img = np.random.randint(0, 255, (64, 64), dtype=np.uint16)
        meta = _make_meta()
        result = photometric_correct(img, meta)
        assert result.shape == img.shape


class TestPipeline:
    def test_full_pipeline_runs(self):
        img = np.random.randint(0, 255, (64, 64), dtype=np.uint16)
        meta = _make_meta()
        pipeline = PreprocessingPipeline()
        result = pipeline.run(img, meta)
        assert result.shape == img.shape
        assert not np.any(np.isnan(result.astype(np.float64)))

    def test_pipeline_no_nan_on_pds3_fixture(self):
        from src.ingestion.loader import load_image

        img, meta = load_image(os.path.join(FIXTURES, "synth_pds3_label.lbl"))
        pipeline = PreprocessingPipeline()
        result = pipeline.run(img, meta)
        assert not np.any(np.isnan(result.astype(np.float64)))

    def test_pipeline_no_nan_on_pds4_fixture(self):
        from src.ingestion.loader import load_image

        img, meta = load_image(os.path.join(FIXTURES, "synth_pds4_label.xml"))
        pipeline = PreprocessingPipeline()
        result = pipeline.run(img, meta)
        assert not np.any(np.isnan(result.astype(np.float64)))

    def test_all_zero_image(self):
        img = np.zeros((64, 64), dtype=np.uint16)
        meta = _make_meta()
        pipeline = PreprocessingPipeline()
        result = pipeline.run(img, meta)
        np.testing.assert_array_equal(result, img)
