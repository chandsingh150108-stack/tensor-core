from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

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
    )
