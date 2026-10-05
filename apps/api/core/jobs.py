"""
Asynchronous Job Management for BioAge-X.
Manages long-running bioinformatics pipelines, model training, and GNN execution
via concurrent worker threads with status tracking.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, Any, Callable, Optional
import uuid

from bioage.utils.logger import get_logger

logger = get_logger("bioage.api.jobs")


class JobStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobManager:
    """In-memory job executor with structured status logging."""

    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.jobs: Dict[str, Dict[str, Any]] = {}

    def submit_job(self, task_fn: Callable[..., Any], *args, **kwargs) -> str:
        job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
        self.jobs[job_id] = {
            "id": job_id,
            "status": JobStatus.PENDING,
            "progress": 0,
            "result": None,
            "error": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        def _runner():
            self.jobs[job_id]["status"] = JobStatus.RUNNING
            self.jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
            try:
                result = task_fn(*args, **kwargs)
                self.jobs[job_id]["status"] = JobStatus.COMPLETED
                self.jobs[job_id]["progress"] = 100
                self.jobs[job_id]["result"] = result
            except Exception as e:
                logger.error(f"Job {job_id} failed: {e}", exc_info=True)
                self.jobs[job_id]["status"] = JobStatus.FAILED
                self.jobs[job_id]["error"] = str(e)
            finally:
                self.jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()

        self.executor.submit(_runner)
        logger.info(f"Submitted asynchronous job: {job_id}")
        return job_id

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.get(job_id)


job_manager = JobManager()
