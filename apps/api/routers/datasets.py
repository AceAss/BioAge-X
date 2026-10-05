"""
Dataset router for BioAge-X API.
Handles multi-omics dataset uploads, loading demo cohorts, profiling, and preview.
"""

import json
from pathlib import Path
import shutil
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query
from sqlalchemy.orm import Session
import pandas as pd

from apps.api.core.config import settings
from apps.api.core.database import get_db
from apps.api.models.db_models import DatasetRecord
from apps.api.schemas.api_schemas import DatasetResponseSchema
from bioage.ingestion.loaders import DatasetLoader
from bioage.utils.logger import get_logger

logger = get_logger("apps.api.routers.datasets")
router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("/upload", response_model=DatasetResponseSchema)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Uploads a multi-omics dataset (CSV, TSV, Parquet, H5AD), profiles it, and stores record."""
    filename = file.filename or "uploaded_data.csv"
    ext = Path(filename).suffix.lower()
    
    if ext not in {".csv", ".tsv", ".txt", ".parquet", ".pq", ".h5ad"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Must be CSV, TSV, Parquet, or H5AD.",
        )

    dataset_id = f"DS-{uuid.uuid4().hex[:8].upper()}"
    save_path = settings.UPLOAD_DIR / f"{dataset_id}_{filename}"

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    loader = DatasetLoader()
    try:
        df, profile = loader.load_file(save_path)
    except Exception as e:
        if save_path.exists():
            save_path.unlink()
        raise HTTPException(status_code=400, detail=f"Failed to profile dataset: {str(e)}")

    record = DatasetRecord(
        id=dataset_id,
        name=filename,
        file_path=str(save_path),
        format=ext.replace(".", ""),
        n_samples=profile.n_samples,
        n_features=profile.n_features,
        orientation=profile.orientation,
        missing_fraction=profile.missing_fraction,
        age_column=profile.age_column,
        detected_modality=profile.detected_modality,
        profile_json=json.dumps(profile.to_dict()),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return DatasetResponseSchema(
        id=record.id,
        name=record.name,
        format=record.format,
        n_samples=record.n_samples,
        n_features=record.n_features,
        orientation=record.orientation,
        missing_fraction=record.missing_fraction,
        age_column=record.age_column,
        detected_modality=record.detected_modality,
        profile=profile.to_dict(),
        created_at=record.created_at.isoformat(),
    )


@router.post("/demo/load", response_model=DatasetResponseSchema)
def load_demo_dataset(db: Session = Depends(get_db)):
    """Loads the pre-packaged synthetic multi-omics demo cohort."""
    demo_file = settings.EXAMPLE_DIR / "demo_multiomics.csv"
    if not demo_file.exists():
        # Generate it if not found
        from scripts.generate_demo_data import main as gen_demo
        gen_demo()

    # Check if demo record already exists in database
    existing = db.query(DatasetRecord).filter(DatasetRecord.name == "demo_multiomics.csv").first()
    if existing:
        profile_data = json.loads(existing.profile_json) if existing.profile_json else None
        return DatasetResponseSchema(
            id=existing.id,
            name=existing.name,
            format=existing.format,
            n_samples=existing.n_samples,
            n_features=existing.n_features,
            orientation=existing.orientation,
            missing_fraction=existing.missing_fraction,
            age_column=existing.age_column,
            detected_modality=existing.detected_modality,
            profile=profile_data,
            created_at=existing.created_at.isoformat(),
        )

    loader = DatasetLoader()
    df, profile = loader.load_file(demo_file)
    dataset_id = "DS-DEMO-MULTIOMICS"

    record = DatasetRecord(
        id=dataset_id,
        name="demo_multiomics.csv",
        file_path=str(demo_file),
        format="csv",
        n_samples=profile.n_samples,
        n_features=profile.n_features,
        orientation=profile.orientation,
        missing_fraction=profile.missing_fraction,
        age_column=profile.age_column,
        detected_modality=profile.detected_modality,
        profile_json=json.dumps(profile.to_dict()),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return DatasetResponseSchema(
        id=record.id,
        name=record.name,
        format=record.format,
        n_samples=record.n_samples,
        n_features=record.n_features,
        orientation=record.orientation,
        missing_fraction=record.missing_fraction,
        age_column=record.age_column,
        detected_modality=record.detected_modality,
        profile=profile.to_dict(),
        created_at=record.created_at.isoformat(),
    )


@router.get("", response_model=list[DatasetResponseSchema])
def list_datasets(db: Session = Depends(get_db)):
    """Lists all registered datasets."""
    records = db.query(DatasetRecord).order_by(DatasetRecord.created_at.desc()).all()
    results = []
    for r in records:
        prof = json.loads(r.profile_json) if r.profile_json else None
        results.append(
            DatasetResponseSchema(
                id=r.id,
                name=r.name,
                format=r.format,
                n_samples=r.n_samples,
                n_features=r.n_features,
                orientation=r.orientation,
                missing_fraction=r.missing_fraction,
                age_column=r.age_column,
                detected_modality=r.detected_modality,
                profile=prof,
                created_at=r.created_at.isoformat(),
            )
        )
    return results


@router.get("/public")
def list_public_datasets():
    """Lists curated publicly available benchmark cohorts for one-click ingestion."""
    return [
        {
            "key": "gse40279_hannum",
            "name": "GSE40279 Hannum Whole Blood Epigenetic Clock Benchmark",
            "modality": "DNA Methylation",
            "sample_count": 80,
            "feature_count": 75,
            "age_range": "20.0 - 88.0 years",
            "description": (
                "Curated benchmark cohort modeled after the landmark Hannum et al. whole-blood dataset (GSE40279). "
                "Contains all 71 Hannum clock CpGs, canonical Horvath loci, chronological age, sex, and smoking status."
            ),
            "reference": "Hannum G, et al. Molecular Cell 2013;49(2):359-367.",
            "file_name": "GSE40279_Hannum_Blood_Benchmark.csv",
        },
        {
            "key": "demo_multiomics",
            "name": "BioAge-X Multi-Omics Cohort (DNAm + RNA + Phenotypic)",
            "modality": "Multi-Omics",
            "sample_count": 150,
            "feature_count": 273,
            "age_range": "20.0 - 85.0 years",
            "description": (
                "Synthetic multi-omics cohort combining DNA methylation beta values (120 CpGs), "
                "transcriptomics (150 gene transcripts), and clinical covariates with embedded biological aging signals."
            ),
            "reference": "BioAge-X Research Platform Synthetic Multi-Omics Benchmark (In Silico Cohort).",
            "file_name": "demo_multiomics.csv",
        },
    ]


@router.post("/public/load/{dataset_key}", response_model=DatasetResponseSchema)
def load_public_dataset(dataset_key: str, db: Session = Depends(get_db)):
    """Loads a curated public benchmark cohort into the active research database."""
    if dataset_key == "gse40279_hannum":
        file_path = settings.DATA_DIR / "public" / "GSE40279_Hannum_Blood_Benchmark.csv"
        if not file_path.exists():
            from scripts.create_public_benchmarks import generate_hannum_public_benchmark
            generate_hannum_public_benchmark()
        name = "GSE40279_Hannum_Blood_Benchmark.csv"
        dataset_id = "DS-PUBLIC-GSE40279"
    elif dataset_key == "demo_multiomics":
        file_path = settings.EXAMPLE_DIR / "demo_multiomics.csv"
        if not file_path.exists():
            from scripts.generate_demo_data import main as gen_demo
            gen_demo()
        name = "demo_multiomics.csv"
        dataset_id = "DS-DEMO-MULTIOMICS"
    else:
        raise HTTPException(status_code=404, detail=f"Public benchmark dataset '{dataset_key}' not recognized.")

    existing = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if existing:
        prof = json.loads(existing.profile_json) if existing.profile_json else None
        return DatasetResponseSchema(
            id=existing.id,
            name=existing.name,
            format=existing.format,
            n_samples=existing.n_samples,
            n_features=existing.n_features,
            orientation=existing.orientation,
            missing_fraction=existing.missing_fraction,
            age_column=existing.age_column,
            detected_modality=existing.detected_modality,
            profile=prof,
            created_at=existing.created_at.isoformat(),
        )

    loader = DatasetLoader()
    df, profile = loader.load_file(file_path)

    record = DatasetRecord(
        id=dataset_id,
        name=name,
        file_path=str(file_path),
        format="csv",
        n_samples=profile.n_samples,
        n_features=profile.n_features,
        orientation=profile.orientation,
        missing_fraction=profile.missing_fraction,
        age_column=profile.age_column,
        detected_modality=profile.detected_modality,
        profile_json=json.dumps(profile.to_dict()),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return DatasetResponseSchema(
        id=record.id,
        name=record.name,
        format=record.format,
        n_samples=record.n_samples,
        n_features=record.n_features,
        orientation=record.orientation,
        missing_fraction=record.missing_fraction,
        age_column=record.age_column,
        detected_modality=record.detected_modality,
        profile=profile.to_dict(),
        created_at=record.created_at.isoformat(),
    )


@router.get("/{dataset_id}")
def get_dataset(dataset_id: str, preview_rows: int = Query(5, ge=1, le=50), db: Session = Depends(get_db)):
    """Fetches dataset metadata, profile, and preview rows."""
    record = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found")

    profile_data = json.loads(record.profile_json) if record.profile_json else {}

    # Read preview rows
    try:
        df = pd.read_csv(record.file_path, nrows=preview_rows)
        preview_data = df.to_dict(orient="records")
        preview_columns = list(df.columns[:25])
    except Exception as e:
        preview_data = []
        preview_columns = []

    return {
        "id": record.id,
        "name": record.name,
        "format": record.format,
        "n_samples": record.n_samples,
        "n_features": record.n_features,
        "age_column": record.age_column,
        "detected_modality": record.detected_modality,
        "profile": profile_data,
        "preview_columns": preview_columns,
        "preview_rows": preview_data,
        "created_at": record.created_at.isoformat(),
    }
