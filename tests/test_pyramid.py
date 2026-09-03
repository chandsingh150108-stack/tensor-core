"""Tests for the pyramid module."""
import math

import numpy as np
import pytest

from src.common.schema import ImageMetadata
from src.pyramid.builder import build_gaussian_pyramid, build_laplacian_pyramid
from src.pyramid.scale_estimator import (
    estimate_scale_ratio,
    select_pyramid_levels,
)


def _make_meta(**kwargs):
    defaults = dict(
        product_id="test",
        sensor="TMC2",
        archive_standard="PDS3",
        pixel_scale_m=5.0,
        image_shape=(512, 512),
    )
    defaults.update(kwargs)
    return ImageMetadata(**defaults)


class TestGaussianPyramid:
    def test_output_shapes(self):
        img = np.random.randint(0, 255, (512, 512), dtype=np.uint8)
        pyramid = build_gaussian_pyramid(img, levels=4)
        assert len(pyramid) == 4
        assert pyramid[0].shape == (512, 512)
        assert pyramid[1].shape == (256, 256)
        assert pyramid[2].shape == (128, 128)
        assert pyramid[3].shape == (64, 64)

    def test_single_level(self):
        img = np.random.randint(0, 255, (64, 64), dtype=np.uint8)
        pyramid = build_gaussian_pyramid(img, levels=1)
        assert len(pyramid) == 1
        assert pyramid[0].shape == (64, 64)


class TestLaplacianPyramid:
    def test_reconstruction(self):
        img = np.random.randint(0, 255, (256, 256), dtype=np.uint8)
        gaussian = build_gaussian_pyramid(img, levels=3)
        laplacian = build_laplacian_pyramid(gaussian)
        assert len(laplacian) == 3
        assert laplacian[0].shape == gaussian[0].shape


class TestScaleRatio:
    def test_metadata_ratio(self):
        meta_a = _make_meta(pixel_scale_m=5.0)
        meta_b = _make_meta(pixel_scale_m=0.25)
        ratio = estimate_scale_ratio(meta_a, meta_b)
        assert abs(ratio - 20.0) < 1e-6

    def test_same_scale(self):
        meta_a = _make_meta(pixel_scale_m=5.0)
        meta_b = _make_meta(pixel_scale_m=5.0)
        ratio = estimate_scale_ratio(meta_a, meta_b)
        assert abs(ratio - 1.0) < 1e-6


class TestSelectPyramidLevels:
    def test_ratio_20(self):
        level_a, level_b = select_pyramid_levels(20.0, max_levels=6)
        assert abs(level_a - level_b) == round(math.log2(20.0))

    def test_ratio_1_returns_0_0(self):
        level_a, level_b = select_pyramid_levels(1.0, max_levels=6)
        assert level_a == 0
        assert level_b == 0
