"""
Analysis router for BioAge-X API.
Runs preprocessing and supervised feature selection on multi-omics datasets.
"""

import json
from pathlib import Path
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd

from apps.api.core.config import settings
from apps.api.core.database import get_db
from apps.api.models.db_models import DatasetRecord, AnalysisRecord
from apps.api.schemas.api_schemas import AnalysisCreateRequest, AnalysisResponseSchema
from bioage.preprocessing.methylation import MethylationPreprocessor
from bioage.preprocessing.transcriptomics import TranscriptomicsPreprocessor
from bioage.preprocessing.feature_selection import FeatureSelector
from bioage.utils.logger import get_logger

logger = get_logger("apps.api.routers.analyses")
router = APIRouter(prefix="/analyses", tags=["Analyses"])


@router.post("", response_model=AnalysisResponseSchema)
def run_analysis(request: AnalysisCreateRequest, db: Session = Depends(get_db)):
    """Executes modality-specific preprocessing and statistical feature selection."""
    dataset = db.query(DatasetRecord).filter(DatasetRecord.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = pd.read_csv(dataset.file_path, index_col=0)
    age_col = dataset.age_column or "chronological_age"
    if age_col not in df.columns:
        # Fallback search
        for c in df.columns:
            if "age" in c.lower():
                age_col = c
                break
    if age_col not in df.columns:
        raise HTTPException(status_code=400, detail=f"No chronological age column found in dataset '{dataset.name}'.")

    y = df[age_col]
    cfg = request.config
    analysis_id = f"ANA-{uuid.uuid4().hex[:8].upper()}"

    # Partition columns by modality
    meth_cols = [c for c in df.columns if c.startswith("cg") and c != age_col]
    trans_cols = [c for c in df.columns if not c.startswith("cg") and c not in {"sample_id", age_col, "sex", "smoking_status", "bmi", "true_age_acceleration", "data_provenance"}]

    provenance = {}
    cleaned_frames = []

    if meth_cols and cfg.modality in {"methylation", "multimodal"}:
        meth_prep = MethylationPreprocessor(
            min_variance=cfg.min_variance,
            imputation_strategy=cfg.imputation_strategy,
            standardize=cfg.standardize,
        )
        df_m_clean, m_prov = meth_prep.fit_transform(df[meth_cols])
        cleaned_frames.append(df_m_clean)
        provenance["methylation"] = m_prov

    if trans_cols and cfg.modality in {"transcriptomics", "multimodal"}:
        trans_prep = TranscriptomicsPreprocessor(
            min_variance=cfg.min_variance,
            imputation_strategy=cfg.imputation_strategy,
        )
        df_t_clean, t_prov = trans_prep.fit_transform(df[trans_cols])
        cleaned_frames.append(df_t_clean)
        provenance["transcriptomics"] = t_prov

    if not cleaned_frames:
        # Use all numeric columns
        num_cols = df.select_dtypes(include=["number"]).columns.drop(age_col, errors="ignore")
        cleaned_frames.append(df[num_cols].fillna(df[num_cols].median()))

    combined_features = pd.concat(cleaned_frames, axis=1)

    # Supervised feature selection
    selector = FeatureSelector(
        max_features=cfg.max_features,
        method=cfg.feature_selection_method,
    )
    X_selected = selector.fit_transform(combined_features, y)
    provenance["selection"] = selector.provenance_

    # Save preprocessed matrix to disk
    out_path = settings.PROCESSED_DIR / f"{analysis_id}_features.csv"
    # Append target age column for training convenience
    save_df = X_selected.copy()
    save_df["chronological_age"] = y
    save_df.to_csv(out_path, index=True)

    record = AnalysisRecord(
        id=analysis_id,
        dataset_id=dataset.id,
        status="COMPLETED",
        modality=cfg.modality,
        preprocessed_path=str(out_path),
        provenance_json=json.dumps(provenance),
        selected_features_json=json.dumps(selector.selected_features_),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return AnalysisResponseSchema(
        id=record.id,
        dataset_id=record.dataset_id,
        status=record.status,
        modality=record.modality,
        selected_features=selector.selected_features_,
        provenance=provenance,
        created_at=record.created_at.isoformat(),
    )


@router.get("/{analysis_id}", response_model=AnalysisResponseSchema)
def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """Retrieves preprocessed analysis details and selected biomarkers."""
    record = db.query(AnalysisRecord).filter(AnalysisRecord.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found")

    selected_features = json.loads(record.selected_features_json) if record.selected_features_json else []
    provenance = json.loads(record.provenance_json) if record.provenance_json else {}

    return AnalysisResponseSchema(
        id=record.id,
        dataset_id=record.dataset_id,
        status=record.status,
        modality=record.modality,
        selected_features=selected_features,
        provenance=provenance,
        created_at=record.created_at.isoformat(),
    )
