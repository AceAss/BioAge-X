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
from apps.api.schemas.api_schemas import ExperimentCreateRequest, ExperimentResponseSchema
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


@router.post("", response_model=ExperimentResponseSchema)
def create_experiment(
    request: ExperimentCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Triggers an end-to-end experiment run:
    Trains the requested model, computes SHAP explainability, performs pathway and network
    enrichment, benchmarks reference clocks, and persists full reproducible provenance.
    """
    from apps.api.schemas.api_schemas import ModelTrainRequest, ReportGenerateRequest
    from apps.api.routers.models import train_model
    from apps.api.routers.reports import generate_report

    # 1. Train model
    train_req = ModelTrainRequest(
        dataset_id=request.dataset_id,
        analysis_id=request.analysis_id,
        model_type=request.model_type,
        hyperparameters=request.hyperparameters,
    )
    model_res = train_model(train_req, db=db)

    # 2. Generate comprehensive experiment report
    report_req = ReportGenerateRequest(
        dataset_id=request.dataset_id,
        model_id=model_res.id,
        experiment_name=request.name,
    )
    report_res = generate_report(report_req, db=db)

    # 3. Retrieve created record
    record = db.query(ExperimentRecord).filter(ExperimentRecord.id == report_res.experiment_id).first()
    if not record:
        raise HTTPException(status_code=500, detail="Experiment record creation could not be verified.")

    metrics = json.loads(record.metrics_json) if record.metrics_json else {}
    accel = json.loads(record.acceleration_summary_json) if record.acceleration_summary_json else {}
    pdf_filename = Path(record.pdf_path).name if record.pdf_path else None
    pdf_url = f"/api/v1/reports/download/{pdf_filename}" if pdf_filename else None

    return ExperimentResponseSchema(
        id=record.id,
        name=record.name,
        dataset_id=record.dataset_id,
        model_id=record.model_id,
        model_type=record.model_type,
        metrics=metrics,
        acceleration_summary=accel,
        pdf_url=pdf_url,
        created_at=record.created_at.isoformat(),
    )


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


@router.get("/{experiment_id}/status")
def get_experiment_status(experiment_id: str, db: Session = Depends(get_db)):
    """Checks the status and metadata of an experiment run."""
    record = db.query(ExperimentRecord).filter(ExperimentRecord.id == experiment_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Experiment record not found")

    return {
        "id": record.id,
        "status": "completed",
        "name": record.name,
        "model_type": record.model_type,
        "dataset_id": record.dataset_id,
        "created_at": record.created_at.isoformat(),
        "has_pdf": bool(record.pdf_path and Path(record.pdf_path).exists()),
    }


@router.get("/{experiment_id}/results")
def get_experiment_results(experiment_id: str, db: Session = Depends(get_db)):
    """Fetches metrics, acceleration summary, and synthesized report for an experiment."""
    return get_experiment_details(experiment_id, db=db)

