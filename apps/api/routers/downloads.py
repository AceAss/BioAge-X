"""
Downloads and Job Monitoring Router for BioAge-X REST API.
Provides asynchronous job status, streaming download progress, and task cancellation.
"""

from fastapi import APIRouter, HTTPException

from apps.api.schemas.api_schemas import DownloadJobResponseSchema
from bioage.acquisition.jobs import JobManager, JobStatus
from bioage.utils.logger import get_logger

logger = get_logger("apps.api.routers.downloads")
router = APIRouter(prefix="/downloads", tags=["Downloads & Jobs"])


@router.get("/{job_id}", response_model=DownloadJobResponseSchema)
def get_download_job_status(job_id: str):
    """Fetches real-time status, progress percentage, transfer speed, and completion payload for a job."""
    manager = JobManager.get_instance()
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    return DownloadJobResponseSchema(
        job_id=job.job_id,
        task_type=job.task_type,
        status=job.status.value,
        progress=job.progress,
        status_message=job.status_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error=job.error,
        downloaded_bytes=job.downloaded_bytes,
        total_bytes=job.total_bytes,
        speed_bytes_sec=job.speed_bytes_sec,
        result_data=job.result_data,
    )


@router.post("/{job_id}/cancel")
def cancel_download_job(job_id: str):
    """Cancels an active download or processing task."""
    manager = JobManager.get_instance()
    success = manager.cancel_job(job_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Could not cancel job '{job_id}' (may be already finished or invalid).",
        )
    return {"message": f"Job '{job_id}' marked for cancellation.", "status": "CANCELLED"}
