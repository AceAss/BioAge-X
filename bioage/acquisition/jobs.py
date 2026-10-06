"""
Asynchronous Job Management Service for BioAge-X.
Tracks long-running operations (repository downloads, matrix extractions,
model training runs) without freezing web workers or the user interface.
"""

import uuid
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Callable

from bioage.utils.logger import get_logger

logger = get_logger("bioage.acquisition.jobs")


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class JobRecord:
    """State descriptor for an asynchronous platform task."""
    job_id: str
    task_type: str  # "DOWNLOAD", "INGESTION", "PHASE1_ANALYSIS", "GNN_TRAINING"
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0  # 0.0 to 1.0
    status_message: str = "Job queued"
    experiment_id: Optional[str] = None
    dataset_id: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    speed_bytes_sec: Optional[float] = None
    downloaded_bytes: Optional[int] = None
    total_bytes: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


class JobManager:
    """In-memory thread pool job manager for local execution."""

    _instance: Optional["JobManager"] = None

    def __init__(self, max_workers: int = 4):
        self._jobs: Dict[str, JobRecord] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    @classmethod
    def get_instance(cls) -> "JobManager":
        if cls._instance is None:
            cls._instance = JobManager()
        return cls._instance

    def create_job(
        self,
        task_type: str,
        experiment_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        initial_message: str = "Job initialized",
    ) -> JobRecord:
        """Initializes and registers a new tracking job."""
        job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
        record = JobRecord(
            job_id=job_id,
            task_type=task_type,
            experiment_id=experiment_id,
            dataset_id=dataset_id,
            status_message=initial_message,
        )
        self._jobs[job_id] = record
        return record

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        return self._jobs.get(job_id)

    def list_jobs(self, limit: int = 20) -> List[JobRecord]:
        return list(self._jobs.values())[-limit:]

    def update_progress(
        self,
        job_id: str,
        progress: float,
        message: str,
        downloaded_bytes: Optional[int] = None,
        total_bytes: Optional[int] = None,
        speed: Optional[float] = None,
    ) -> None:
        rec = self._jobs.get(job_id)
        if rec and rec.status == JobStatus.RUNNING:
            rec.progress = max(0.0, min(1.0, progress))
            rec.status_message = message
            rec.downloaded_bytes = downloaded_bytes
            rec.total_bytes = total_bytes
            rec.speed_bytes_sec = speed

    def submit_task(
        self,
        job_id: str,
        task_fn: Callable[..., Any],
        *args,
        **kwargs,
    ) -> None:
        """Dispatches worker execution in thread pool."""
        rec = self._jobs.get(job_id)
        if not rec:
            raise KeyError(f"Job ID {job_id} not found.")

        def wrapper():
            rec.status = JobStatus.RUNNING
            rec.started_at = datetime.now(timezone.utc).isoformat()
            rec.status_message = "Task executing..."
            try:
                res = task_fn(*args, **kwargs)
                rec.status = JobStatus.COMPLETED
                rec.progress = 1.0
                rec.status_message = "Task completed successfully."
                rec.result_data = res if isinstance(res, dict) else ({"result": res} if res else None)
                rec.completed_at = datetime.now(timezone.utc).isoformat()
            except Exception as e:
                logger.error(f"Job {job_id} failed: {e}", exc_info=True)
                rec.status = JobStatus.FAILED
                rec.error = str(e)
                rec.status_message = f"Failed: {e}"
                rec.completed_at = datetime.now(timezone.utc).isoformat()

        self._executor.submit(wrapper)

    def cancel_job(self, job_id: str) -> bool:
        rec = self._jobs.get(job_id)
        if rec and rec.status in (JobStatus.QUEUED, JobStatus.RUNNING):
            rec.status = JobStatus.CANCELLED
            rec.status_message = "Job cancelled by user."
            rec.completed_at = datetime.now(timezone.utc).isoformat()
            return True
        return False
