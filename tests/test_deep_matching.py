"""Tests for deep matching module."""
import numpy as np
import pytest
import torch

from src.deep_matching.device_manager import get_device
from src.deep_matching.superpoint_wrapper import SuperPointExtractor
from src.features.base import FeatureResult


class TestDeviceManager:
    def test_cpu_prefer_gpu_false(self):
        device = get_device(prefer_gpu=False)
        assert device.type == "cpu"

    def test_cpu_when_no_gpu(self):
        device = get_device(prefer_gpu=True)
        assert device.type in ("cpu", "cuda")


class TestSuperPoint:
    def test_returns_feature_result(self):
        img = np.random.randint(0, 255, (128, 128), dtype=np.uint8)
        sp = SuperPointExtractor(device=torch.device("cpu"))
        result = sp.detect_and_compute(img)
        assert isinstance(result, FeatureResult)
        assert result.keypoints.shape[1] == 2

    def test_output_shapes_consistent(self):
        img = np.random.randint(0, 255, (128, 128), dtype=np.uint8)
        sp = SuperPointExtractor(device=torch.device("cpu"))
        result = sp.detect_and_compute(img)
        assert result.keypoints.shape[0] == result.responses.shape[0]


class TestLoFTR:
    def test_loftr_runs(self):
        try:
            import kornia.feature
        except ImportError:
            pytest.skip("Kornia not available")

        from src.deep_matching.loftr_wrapper import LoFTRMatcher

        img = np.random.randint(50, 200, (128, 128), dtype=np.uint8)
        matcher = LoFTRMatcher(device=torch.device("cpu"))
        pts_a, pts_b, conf = matcher.match(img, img)
        assert pts_a.shape[1] == 2
        assert pts_b.shape[1] == 2
        assert len(conf) > 0
        assert conf.mean() > 0.0


class TestLightGlue:
    def test_lightglue_runs(self):
        try:
            import kornia.feature as kf
            if not hasattr(kf, "SuperPoint") or not hasattr(kf, "LightGlue"):
                pytest.skip("LightGlue/SuperPoint not available in this kornia version")
        except ImportError:
            pytest.skip("Kornia not available")

        from src.deep_matching.lightglue_wrapper import LightGlueMatcher

        img = np.random.randint(50, 200, (128, 128), dtype=np.uint8)
        matcher = LightGlueMatcher(device=torch.device("cpu"))
        pts_a, pts_b, conf = matcher.match(img, img)
        assert pts_a.shape[1] == 2
        assert pts_b.shape[1] == 2
