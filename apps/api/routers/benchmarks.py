"""
Benchmarks Router for BioAge-X API.
Runs cross-modality ablation benchmarking and comparisons against established
reference epigenetic clocks (Horvath 2013, Hannum 2013, PhenoAge 2018).
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
import pandas as pd

from apps.api.core.database import get_db
from apps.api.models.db_models import DatasetRecord
from bioage.benchmarks.clocks import ReferenceClockBenchmarkSuite, HorvathClock, HannumClock, PhenoAgeClock
from bioage.benchmarks.multi_omics_evaluator import MultiOmicsBenchmarkComparator
from bioage.utils.logger import get_logger

logger = get_logger("apps.api.routers.benchmarks")
router = APIRouter(prefix="/benchmarks", tags=["Benchmarks"])


class BenchmarkRunRequest(BaseModel):
    dataset_id: str
    age_column: Optional[str] = None
    strict_coverage: bool = False


class BenchmarkResultItemSchema(BaseModel):
    name: str
    category: str
    strategy: str
    modality: str
    status: str
    available_features_count: int
    required_features_count: int
    missing_features_count: int
    coverage_pct: float
    mae: Optional[float] = None
    rmse: Optional[float] = None
    r2: Optional[float] = None
    pearson_r: Optional[float] = None
    spearman_rho: Optional[float] = None
    sample_count: Optional[int] = None
    mean_acceleration: Optional[float] = None
    missing_features_sample: Optional[List[str]] = None
    citation: Optional[str] = None
    notes: Optional[str] = None


class BenchmarkResponseSchema(BaseModel):
    dataset_id: str
    dataset_name: str
    research_question: str
    sample_count: int
    age_target_column: str
    best_performing_approach: str
    scientific_synthesis: str
    results: List[BenchmarkResultItemSchema]


@router.get("/clocks")
def list_reference_clocks():
    """Lists supported reference biological and epigenetic clocks with citations."""
    suite = ReferenceClockBenchmarkSuite()
    clocks_meta = []
    for c in suite.clocks:
        clocks_meta.append({
            "name": c.name,
            "citation": c.citation,
            "tissue_context": c.tissue_context,
            "required_cpg_count": len(c.required_features),
            "intercept": c.intercept,
            "min_coverage_threshold": c.min_coverage_threshold,
            "canonical_features": list(c.coefficients.keys())[:15],
            "description": (
                "Mathematical reference clock formulation for external benchmarking. "
                "Evaluates without fabricating missing probes."
            ),
        })
    return {
        "reference_clocks": clocks_meta,
        "disclaimer": (
            "Reference clocks are implemented for computational biology benchmarking and research reproducibility. "
            "They are NOT certified clinical diagnostics."
        ),
    }


@router.post("/evaluate", response_model=BenchmarkResponseSchema)
def run_benchmark(request: BenchmarkRunRequest, db: Session = Depends(get_db)):
    """
    Executes a comprehensive benchmark comparing BioAge-X single-modality models,
    multi-omics fusion, and established reference epigenetic clocks on the dataset.
    """
    dataset = db.query(DatasetRecord).filter(DatasetRecord.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    file_path = Path(dataset.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset file not found on disk")

    try:
        df = pd.read_csv(file_path, index_col=0)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read dataset: {str(e)}")

    age_col = request.age_column or dataset.age_column or "chronological_age"
    if age_col not in df.columns:
        for c in df.columns:
            if "age" in c.lower():
                age_col = c
                break

    if age_col not in df.columns:
        raise HTTPException(status_code=400, detail="Missing chronological age target column for benchmarking.")

    comparator = MultiOmicsBenchmarkComparator()
    try:
        report = comparator.run_comprehensive_benchmark(df, age_col=age_col)
    except Exception as e:
        logger.error(f"Benchmark execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Benchmark execution failed: {str(e)}")

    return BenchmarkResponseSchema(
        dataset_id=dataset.id,
        dataset_name=dataset.name,
        research_question=report["research_question"],
        sample_count=report["sample_count"],
        age_target_column=report["age_target_column"],
        best_performing_approach=report["best_performing_approach"],
        scientific_synthesis=report["scientific_synthesis"],
        results=report["results"],
    )
