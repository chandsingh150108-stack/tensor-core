from __future__ import annotations

import base64

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

from src.api.background import get_job
from src.api.schemas import ReportResponse, ErrorResponse

router = APIRouter()


@router.get(
    "/report/{job_id}",
    response_model=ReportResponse,
    responses={404: {"model": ErrorResponse}, 202: {"model": ReportResponse}},
)
async def get_report(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    if job["status"] == "running" or job["status"] == "pending":
        return JSONResponse(
            status_code=202,
            content={"job_id": job_id, "status": job["status"], "metrics": None, "confidence": None},
        )

    result = job.get("result") or {}
    return ReportResponse(
        job_id=job_id,
        status=job["status"],
        metrics=result.get("metrics"),
        confidence=result.get("confidence"),
        feature_points=result.get("feature_points", []),
    )


@router.get("/report/{job_id}/source-image")
async def get_source_image(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise ValueError(f"Job not found: {job_id}")
    result = job.get("result") or {}
    img_b64 = result.get("source_image")
    if not img_b64:
        raise ValueError("Source image not available")
    img_bytes = base64.b64decode(img_b64)
    return Response(content=img_bytes, media_type="image/png")


@router.get("/report/{job_id}/warped-image")
async def get_warped_image(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise ValueError(f"Job not found: {job_id}")
    result = job.get("result") or {}
    img_b64 = result.get("warped_image")
    if not img_b64:
        raise ValueError("Warped image not available")
    img_bytes = base64.b64decode(img_b64)
    return Response(content=img_bytes, media_type="image/png")


@router.get("/report/{job_id}/feature-points")
async def get_feature_points(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise ValueError(f"Job not found: {job_id}")
    result = job.get("result") or {}
    points = result.get("feature_points", [])
    return {"job_id": job_id, "points": points, "count": len(points)}
