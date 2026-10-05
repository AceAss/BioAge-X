"""
Explainability router for BioAge-X API.
Computes SHAP global rankings, beeswarm data, and individual sample waterfall decompositions.
"""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd

from apps.api.core.database import get_db
from apps.api.models.db_models import DatasetRecord, ModelRecord
from apps.api.schemas.api_schemas import ExplainRequest, ExplainResponseSchema
from bioage.models.base import BaseBioAgeModel
from bioage.explainability.shap_engine import BioAgeShapExplainer
from bioage.utils.logger import get_logger

logger = get_logger("apps.api.routers.explainability")
router = APIRouter(prefix="/explain", tags=["Explainability"])


@router.post("", response_model=ExplainResponseSchema)
def explain_model_predictions(request: ExplainRequest, db: Session = Depends(get_db)):
    """Computes SHAP feature attributions across cohort and sample waterfall decomposition."""
    model_record = db.query(ModelRecord).filter(ModelRecord.id == request.model_id).first()
    if not model_record:
        raise HTTPException(status_code=404, detail="Model record not found")

    dataset_record = db.query(DatasetRecord).filter(DatasetRecord.id == request.dataset_id).first()
    if not dataset_record:
        raise HTTPException(status_code=404, detail="Dataset record not found")

    try:
        model = BaseBioAgeModel.load(model_record.artifact_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model artifact: {e}")

    df = pd.read_csv(dataset_record.file_path, index_col=0)
    sample_ids = list(df.index)

    explainer = BioAgeShapExplainer(model)
    explainer.explain(df, sample_ids=sample_ids)

    global_biomarkers = explainer.get_global_importance(top_k=request.top_k)
    beeswarm_sample = explainer.get_beeswarm_data(top_k=min(request.top_k, 12))
    
    # Safe sample index
    safe_idx = max(0, min(request.sample_idx, len(sample_ids) - 1))
    waterfall_sample = explainer.get_waterfall_explanation(sample_idx=safe_idx, top_k=10)

    return ExplainResponseSchema(
        model_id=model_record.id,
        global_biomarkers=global_biomarkers,
        beeswarm_sample=beeswarm_sample,
        waterfall_sample=waterfall_sample,
    )


@router.get("/bridge/{model_id}")
def get_biomarker_phase2_bridge(model_id: str, db: Session = Depends(get_db)):
    """
    Constructs the formal Phase 1 to Phase 2 biomarker-to-biology bridge.
    Transforms model/SHAP important features into biologically annotated candidate biomarkers
    and generates seed entities and pathways for GraphOmics-AI network construction.
    """
    import json
    from bioage.explainability.biomarker_bridge import BiomarkerToBiologyBridge

    model_record = db.query(ModelRecord).filter(ModelRecord.id == model_id).first()
    if not model_record:
        raise HTTPException(status_code=404, detail="Model record not found")

    importances = json.loads(model_record.feature_importance_json) if model_record.feature_importance_json else {}
    if not importances:
        raise HTTPException(status_code=400, detail="Model does not contain feature importance data")

    bridge = BiomarkerToBiologyBridge()
    candidates = bridge.build_candidate_biomarkers(importances, top_n=20)
    payload = bridge.generate_phase2_bridge_payload(candidates)

    return {
        "model_id": model_record.id,
        "model_name": model_record.name,
        "model_type": model_record.model_type,
        "dataset_id": model_record.dataset_id,
        "bridge_payload": payload,
        "disclaimer": (
            "These molecular features are classified as Candidate Aging-Associated Features or Model-Associated Biomarkers. "
            "They are statistical predictive associations and do not prove causal aging mechanisms without biological validation."
        ),
    }

