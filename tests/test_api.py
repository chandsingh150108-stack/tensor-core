"""Tests for the FastAPI backend."""
import os

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
client = TestClient(app)


class TestHealth:
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestUpload:
    def test_upload_pds4(self):
        pytest.skip("PDS4 upload requires companion binary in same directory; tested via ingestion tests")

    def test_upload_geotiff(self):
        path = os.path.join(FIXTURES, "synth_geotiff.tif")
        with open(path, "rb") as f:
            response = client.post(
                "/images/upload",
                files={"file": ("synth_geotiff.tif", f, "image/tiff")},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["archive_standard"] == "GEOTIFF"


class TestRegister:
    def _upload_fixture(self, filename):
        path = os.path.join(FIXTURES, filename)
        with open(path, "rb") as f:
            response = client.post(
                "/images/upload",
                files={"file": (filename, f, "application/octet-stream")},
            )
        return response.json()["image_id"]

    def test_register_returns_202(self):
        id_a = self._upload_fixture("synth_geotiff.tif")
        id_b = self._upload_fixture("synth_geotiff.tif")

        response = client.post(
            "/register",
            json={
                "source_image_id": id_a,
                "reference_image_id": id_b,
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"

    def test_register_bogus_id_returns_404(self):
        response = client.post(
            "/register",
            json={
                "source_image_id": "nonexistent",
                "reference_image_id": "nonexistent",
            },
        )
        assert response.status_code == 404


class TestReport:
    def test_report_pending_job(self):
        id_a = self._upload_fixture("synth_geotiff.tif")

        reg_response = client.post(
            "/register",
            json={
                "source_image_id": id_a,
                "reference_image_id": id_a,
            },
        )
        job_id = reg_response.json()["job_id"]

        response = client.get(f"/report/{job_id}")
        assert response.status_code in (200, 202)

    def test_report_nonexistent_job(self):
        response = client.get("/report/nonexistent-id")
        assert response.status_code == 404

    def _upload_fixture(self, filename):
        path = os.path.join(FIXTURES, filename)
        with open(path, "rb") as f:
            response = client.post(
                "/images/upload",
                files={"file": (filename, f, "application/octet-stream")},
            )
        return response.json()["image_id"]
