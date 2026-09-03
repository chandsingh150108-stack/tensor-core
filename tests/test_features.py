"""Tests for the feature detection module."""
import cv2
import numpy as np
import pytest

from src.features.base import FeatureResult, ImageTooSmallError
from src.features.factory import get_detector


def _checkerboard(size=256, squares=8):
    cb = np.zeros((size, size), dtype=np.uint8)
    sq = size // squares
    for i in range(squares):
        for j in range(squares):
            if (i + j) % 2 == 0:
                cb[i * sq : (i + 1) * sq, j * sq : (j + 1) * sq] = 255
    return cb


CHECKERBOARD = _checkerboard()
FLAT_IMAGE = np.ones((128, 128), dtype=np.uint8) * 128


class TestSIFT:
    def test_detects_keypoints_on_texture(self):
        det = get_detector("sift")
        result = det.detect_and_compute(CHECKERBOARD)
        assert isinstance(result, FeatureResult)
        assert len(result.keypoints) > 0
        assert result.descriptors.shape[0] == result.keypoints.shape[0]

    def test_no_keypoints_on_flat(self):
        det = get_detector("sift")
        result = det.detect_and_compute(FLAT_IMAGE)
        assert len(result.keypoints) == 0

    def test_max_features(self):
        det = get_detector("sift", nfeatures=50)
        result = det.detect_and_compute(CHECKERBOARD)
        assert len(result.keypoints) <= 200


class TestORB:
    def test_detects_keypoints_on_texture(self):
        det = get_detector("orb")
        result = det.detect_and_compute(CHECKERBOARD)
        assert len(result.keypoints) > 0
        assert result.descriptors.shape[0] == result.keypoints.shape[0]

    def test_no_keypoints_on_flat(self):
        det = get_detector("orb")
        result = det.detect_and_compute(FLAT_IMAGE)
        assert len(result.keypoints) == 0


class TestAKAZE:
    @pytest.fixture(autouse=True)
    def check_akaze(self):
        if not hasattr(cv2, "AKAZE_create"):
            pytest.skip("AKAZE not available in this OpenCV build")

    def test_detects_keypoints_on_texture(self):
        det = get_detector("akaze")
        result = det.detect_and_compute(CHECKERBOARD)
        assert len(result.keypoints) > 0
        assert result.descriptors.shape[0] == result.keypoints.shape[0]

    def test_no_keypoints_on_flat(self):
        det = get_detector("akaze")
        result = det.detect_and_compute(FLAT_IMAGE)
        assert len(result.keypoints) == 0


class TestFactory:
    def test_invalid_param_raises(self):
        with pytest.raises(ValueError, match="Unknown"):
            get_detector("sift", bogus_param=1)

    def test_invalid_detector_name(self):
        with pytest.raises(ValueError, match="Unknown detector"):
            get_detector("invalid")
