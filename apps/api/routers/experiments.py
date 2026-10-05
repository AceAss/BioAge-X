"""
Experiments router for BioAge-X API.
Tracks, stores, and compares scientific experiment runs across datasets and models.
"""

import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.core.database import get_db
from apps.api.models.db_models import ExperimentRecord
from apps.api.schemas.api_schemas import ExperimentResponseSchema
from bioage.utils.logger import get_logger

logger = get_logger("apps.api.routers.experiments")
router = APIRouter(prefix="/experiments", tags=["Experiments"])


@router.get("", response_model=list[ExperimentResponseSchema])
def list_experiments(db: Session = Depends(get_db)):
    """Lists all tracked experiment runs."""
    records = db.query(ExperimentRecord).order_by(ExperimentRecord.created_at.desc()).all()
    results = []
    for r in records:
        metrics = json.loads(r.metrics_json) if r.metrics_json else {}
        accel = json.loads(r.acceleration_summary_json) if r.acceleration_summary_json else {}
        pdf_filename = Path(r.pdf_path).name if r.pdf_path else None
        pdf_url = f"/api/v1/reports/download/{pdf_filename}" if pdf_filename else None

        results.append(
            ExperimentResponseSchema(
                id=r.id,
                name=r.name,
                dataset_id=r.dataset_id,
                model_id=r.model_id,
                model_type=r.model_type,
                metrics=metrics,
                acceleration_summary=accel,
                pdf_url=pdf_url,
                created_at=r.created_at.isoformat(),
            )
        )
    return results


@router.get("/{experiment_id}")
def get_experiment_details(experiment_id: str, db: Session = Depends(get_db)):
    """Fetches full experiment details and synthesized report."""
    record = db.query(ExperimentRecord).filter(ExperimentRecord.id == experiment_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Experiment record not found")

    metrics = json.loads(record.metrics_json) if record.metrics_json else {}
    accel = json.loads(record.acceleration_summary_json) if record.acceleration_summary_json else {}
    report = json.loads(record.report_json) if record.report_json else {}
    pdf_filename = Path(record.pdf_path).name if record.pdf_path else None

    return {
        "id": record.id,
        "name": record.name,
        "dataset_id": record.dataset_id,
        "model_id": record.model_id,
        "model_type": record.model_type,
        "metrics": metrics,
        "acceleration_summary": accel,
        "report_data": report,
        "reproducibility_hash": record.reproducibility_hash,
        "pdf_url": f"/api/v1/reports/download/{pdf_filename}" if pdf_filename else None,
        "created_at": record.created_at.isoformat(),
    }
