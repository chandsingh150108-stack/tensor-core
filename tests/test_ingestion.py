"""Tests for the ingestion module."""
import os
import tempfile

import numpy as np
import pytest

from src.common.errors import UnsupportedFormatError
from src.common.schema import ImageMetadata
from src.ingestion.loader import load_image


FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestImageMetadata:
    def test_valid_metadata(self):
        meta = ImageMetadata(
            product_id="test",
            sensor="TMC2",
            archive_standard="PDS3",
            pixel_scale_m=5.0,
            sun_azimuth_deg=45.0,
            sun_elevation_deg=30.0,
        )
        assert meta.product_id == "test"
        assert meta.sensor == "TMC2"

    def test_invalid_azimuth_raises(self):
        with pytest.raises(ValueError, match="sun_azimuth_deg"):
            ImageMetadata(
                product_id="test",
                sensor="TMC2",
                archive_standard="PDS3",
                pixel_scale_m=5.0,
                sun_azimuth_deg=400.0,
            )

    def test_invalid_elevation_raises(self):
        with pytest.raises(ValueError, match="sun_elevation_deg"):
            ImageMetadata(
                product_id="test",
                sensor="TMC2",
                archive_standard="PDS3",
                pixel_scale_m=5.0,
                sun_elevation_deg=100.0,
            )

    def test_negative_pixel_scale_raises(self):
        with pytest.raises(ValueError, match="pixel_scale_m"):
            ImageMetadata(
                product_id="test",
                sensor="TMC2",
                archive_standard="PDS3",
                pixel_scale_m=-1.0,
            )


class TestPDS3Reader:
    def test_load_pds3(self):
        label_path = os.path.join(FIXTURES, "synth_pds3_label.lbl")
        img, meta = load_image(label_path)
        assert img.shape == (64, 64)
        assert meta.archive_standard == "PDS3"
        assert meta.product_id == "TEST_PDS3_LABEL"
        assert meta.sun_azimuth_deg == 45.0
        assert meta.sun_elevation_deg == 30.0


class TestPDS4Reader:
    def test_load_pds4(self):
        label_path = os.path.join(FIXTURES, "synth_pds4_label.xml")
        img, meta = load_image(label_path)
        assert meta.archive_standard == "PDS4"
        assert meta.sun_elevation_deg == 35.0
        assert meta.sun_azimuth_deg == 120.0
        assert meta.pixel_scale_m == 0.28


class TestGeoTIFFReader:
    def test_load_geotiff(self):
        tif_path = os.path.join(FIXTURES, "synth_geotiff.tif")
        img, meta = load_image(tif_path)
        assert meta.archive_standard == "GEOTIFF"
        assert img.shape == (64, 64)
        assert meta.sun_azimuth_deg == 150.0
        assert meta.sun_elevation_deg == 25.0


class TestEdgeCases:
    def test_invalid_azimuth_raises(self):
        """A label with SUB_SOLAR_AZIMUTH = 400 should raise ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".lbl", mode="w", delete=False) as f:
            f.write(
                'OBJECT = ROOT\n'
                '  SUB_SOLAR_AZIMUTH = 400\n'
                '  LINES = 64\n'
                '  LINE_SAMPLES = 64\n'
                '  SAMPLE_BITS = 16\n'
                'END_OBJECT = ROOT\n'
            )
            f.flush()
            try:
                body_path = f.name.replace(".lbl", ".img")
                np.zeros((64, 64), dtype=np.uint16).tofile(body_path)
                with pytest.raises(ValueError, match="sun_azimuth_deg"):
                    load_image(f.name)
            finally:
                os.unlink(f.name)
                if os.path.exists(body_path):
                    os.unlink(body_path)

    def test_missing_label_raises(self):
        with pytest.raises(FileNotFoundError):
            load_image("/nonexistent/path/file.img")

    def test_unsupported_format_raises(self):
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            try:
                with pytest.raises(UnsupportedFormatError):
                    load_image(f.name)
            finally:
                os.unlink(f.name)


class TestRoundTrip:
    def test_all_fixtures_round_trip(self):
        fixtures = [
            os.path.join(FIXTURES, "synth_pds3_label.lbl"),
            os.path.join(FIXTURES, "synth_pds4_label.xml"),
            os.path.join(FIXTURES, "synth_geotiff.tif"),
        ]
        for path in fixtures:
            img, meta = load_image(path)
            assert isinstance(img, np.ndarray)
            assert isinstance(meta, ImageMetadata)
            assert meta.product_id is not None
            assert meta.source_path == path
            assert meta.image_shape[0] > 0
            assert meta.image_shape[1] > 0
