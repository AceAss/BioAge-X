"""
Models router for BioAge-X API.
Trains biological age estimation algorithms (ElasticNet, RF, XGBoost, Fusion)
and computes standardized benchmark performance metrics.
"""

import json
from pathlib import Path
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd

from apps.api.core.config import settings
from apps.api.core.database import get_db
from apps.api.models.db_models import DatasetRecord, AnalysisRecord, ModelRecord
from apps.api.schemas.api_schemas import ModelTrainRequest, ModelResponseSchema
from bioage.models.elasticnet import BioAgeElasticNet
from bioage.models.random_forest import BioAgeRandomForest
from bioage.models.xgboost_model import BioAgeXGBoost
from bioage.models.fusion import MultiOmicsEarlyFusion, MultiOmicsLateFusion, MultiOmicsWeightedEnsemble
from bioage.evaluation.metrics import evaluate_predictions
from bioage.evaluation.acceleration import compute_age_acceleration, summarize_acceleration_cohort
from bioage.utils.logger import get_logger

logger = get_logger("apps.api.routers.models")
router = APIRouter(prefix="/models", tags=["Models"])


@router.post("/train", response_model=ModelResponseSchema)
def train_model(request: ModelTrainRequest, db: Session = Depends(get_db)):
    """Trains a biological age estimator and stores benchmark metrics."""
    dataset = db.query(DatasetRecord).filter(DatasetRecord.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Load feature matrix
    if request.analysis_id:
        analysis = db.query(AnalysisRecord).filter(AnalysisRecord.id == request.analysis_id).first()
        if not analysis or not Path(analysis.preprocessed_path).exists():
            raise HTTPException(status_code=404, detail="Preprocessed analysis data not found")
        data_df = pd.read_csv(analysis.preprocessed_path, index_col=0)
    else:
        # Load raw dataset directly
        data_df = pd.read_csv(dataset.file_path, index_col=0)

    age_col = "chronological_age" if "chronological_age" in data_df.columns else dataset.age_column
    if age_col not in data_df.columns:
        for c in data_df.columns:
            if "age" in c.lower():
                age_col = c
                break
    if age_col not in data_df.columns:
        raise HTTPException(status_code=400, detail="Missing chronological age target column.")

    y = data_df[age_col]
    
    # Exclude metadata columns from feature matrix X
    drop_cols = {
        age_col, "sample_id", "sex", "smoking_status", "bmi",
        "true_age_acceleration", "data_provenance"
    }
    feature_cols = [c for c in data_df.columns if c not in drop_cols and pd.api.types.is_numeric_dtype(data_df[c])]
    X = data_df[feature_cols].fillna(data_df[feature_cols].median())

    # Instantiate chosen model architecture
    m_type = request.model_type
    hparams = request.hyperparameters or {}

    if m_type == "ElasticNet":
        model = BioAgeElasticNet(**hparams)
    elif m_type == "RandomForest":
        model = BioAgeRandomForest(**hparams)
    elif m_type == "XGBoost":
        model = BioAgeXGBoost(**hparams)
    elif m_type == "EarlyFusion":
        model = MultiOmicsEarlyFusion()
    elif m_type == "LateFusion":
        model = MultiOmicsLateFusion()
    elif m_type == "WeightedEnsemble":
        model = MultiOmicsWeightedEnsemble()
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported model type '{m_type}'.")

    logger.info(f"Training {m_type} on {X.shape[0]} samples with {X.shape[1]} features")
    model.fit(X, y)
    preds = model.predict(X)

    # Compute evaluation metrics
    metrics = evaluate_predictions(
        y.values,
        preds,
        n_features=X.shape[1],
        training_time_sec=model.training_time_sec_,
    )

    feature_importances = model.get_feature_importance()
    top_importances = dict(list(feature_importances.items())[:30])

    model_id = f"MDL-{uuid.uuid4().hex[:8].upper()}"
    artifact_path = settings.PROCESSED_DIR / f"{model_id}.joblib"
    model.save(artifact_path)

    record = ModelRecord(
        id=model_id,
        name=f"{m_type}_{dataset.name}",
        model_type=m_type,
        dataset_id=dataset.id,
        mae=metrics.mae,
        rmse=metrics.rmse,
        r2=metrics.r2,
        pearson_r=metrics.pearson_r,
        spearman_rho=metrics.spearman_rho,
        n_features=metrics.n_features,
        training_time_sec=metrics.training_time_sec,
        artifact_path=str(artifact_path),
        feature_importance_json=json.dumps(top_importances),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return ModelResponseSchema(
        id=record.id,
        name=record.name,
        model_type=record.model_type,
        dataset_id=record.dataset_id,
        mae=record.mae,
        rmse=record.rmse,
        r2=record.r2,
        pearson_r=record.pearson_r,
        spearman_rho=record.spearman_rho,
        n_features=record.n_features,
        training_time_sec=record.training_time_sec,
        feature_importance=top_importances,
        created_at=record.created_at.isoformat(),
    )


@router.get("", response_model=list[ModelResponseSchema])
def list_models(db: Session = Depends(get_db)):
    """Lists all trained biological age models and their metrics."""
    records = db.query(ModelRecord).order_by(ModelRecord.created_at.desc()).all()
    results = []
    for r in records:
        imp = json.loads(r.feature_importance_json) if r.feature_importance_json else {}
        results.append(
            ModelResponseSchema(
                id=r.id,
                name=r.name,
                model_type=r.model_type,
                dataset_id=r.dataset_id,
                mae=r.mae,
                rmse=r.rmse,
                r2=r.r2,
                pearson_r=r.pearson_r,
                spearman_rho=r.spearman_rho,
                n_features=r.n_features,
                training_time_sec=r.training_time_sec,
                feature_importance=imp,
                created_at=r.created_at.isoformat(),
            )
        )
    return results


@router.get("/{model_id}")
def get_model_details(model_id: str, db: Session = Depends(get_db)):
    """Fetches full model metadata, predictions, and age acceleration distribution."""
    record = db.query(ModelRecord).filter(ModelRecord.id == model_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Model record not found")

    dataset = db.query(DatasetRecord).filter(DatasetRecord.id == record.dataset_id).first()
    if not dataset or not Path(dataset.file_path).exists():
        raise HTTPException(status_code=404, detail="Underlying dataset not found")

    # Load model and dataset
    try:
        from bioage.models.base import BaseBioAgeModel
        model = BaseBioAgeModel.load(record.artifact_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model artifact: {e}")

    df = pd.read_csv(dataset.file_path, index_col=0)
    age_col = dataset.age_column or "chronological_age"
    y = df[age_col]
    preds = model.predict(df)

    covariates = df[["sex", "smoking_status", "bmi"]] if {"sex", "smoking_status", "bmi"}.issubset(df.columns) else None
    df_accel = compute_age_acceleration(y, preds, sample_ids=list(df.index), covariates_df=covariates)
    accel_summary = summarize_acceleration_cohort(df_accel)

    return {
        "id": record.id,
        "name": record.name,
        "model_type": record.model_type,
        "dataset_id": record.dataset_id,
        "metrics": {
            "mae": record.mae,
            "rmse": record.rmse,
            "r2": record.r2,
            "pearson_r": record.pearson_r,
            "spearman_rho": record.spearman_rho,
            "n_features": record.n_features,
            "training_time_sec": record.training_time_sec,
        },
        "feature_importance": json.loads(record.feature_importance_json) if record.feature_importance_json else {},
        "acceleration_summary": accel_summary,
        "sample_predictions": df_accel.head(60).to_dict(orient="records"),
        "created_at": record.created_at.isoformat(),
    }
