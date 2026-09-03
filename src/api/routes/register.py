from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks

from src.api.background import get_job, run_registration_job
from src.api.routes.upload import get_stored_image
from src.api.schemas import RegisterRequest, RegisterResponse, JobStatus, ErrorResponse
from src.common.errors import UnsupportedFormatError

router = APIRouter()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=202,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def start_registration(request: RegisterRequest, background_tasks: BackgroundTasks):
    src = get_stored_image(request.source_image_id)
    ref = get_stored_image(request.reference_image_id)

    if src is None:
        raise ValueError(f"Image not found: {request.source_image_id}")
    if ref is None:
        raise ValueError(f"Image not found: {request.reference_image_id}")

    img_a, meta_a = ref
    img_b, meta_b = src

    job_id = str(uuid.uuid4())
    get_job(job_id)  # ensure exists
    from src.api.background import _jobs
    _jobs[job_id] = {"job_id": job_id, "status": "pending", "result": None}

    background_tasks.add_task(run_registration_job, job_id, img_a, meta_a, img_b, meta_b)

    return RegisterResponse(job_id=job_id, status="pending")


@router.get(
    "/register/{job_id}",
    response_model=JobStatus,
    responses={404: {"model": ErrorResponse}},
)
async def poll_registration(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise ValueError(f"Job not found: {job_id}")
    return JobStatus(
        job_id=job["job_id"],
        status=job["status"],
        result=job.get("result"),
    )
