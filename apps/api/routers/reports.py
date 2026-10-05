"""
Reports router for BioAge-X API.
Generates comprehensive research reports and serves downloadable PDF artifacts.
"""

import json
from pathlib import Path
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import pandas as pd

from apps.api.core.config import settings
from apps.api.core.database import get_db
from apps.api.models.db_models import DatasetRecord, ModelRecord, ExperimentRecord
from apps.api.schemas.api_schemas import ReportGenerateRequest, ReportResponseSchema
from bioage.models.base import BaseBioAgeModel
from bioage.evaluation.acceleration import compute_age_acceleration, summarize_acceleration_cohort
from bioage.explainability.shap_engine import BioAgeShapExplainer
from bioage.pathways.enrichment import PathwayEnrichmentAnalyzer
from bioage.network.interaction_graph import BiologicalInteractionGraph
from bioage.reporting.report_generator import ResearchReportGenerator
from bioage.reporting.pdf_export import export_report_to_pdf
from bioage.utils.logger import get_logger

logger = get_logger("apps.api.routers.reports")
router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate", response_model=ReportResponseSchema)
def generate_report(request: ReportGenerateRequest, db: Session = Depends(get_db)):
    """Synthesizes complete research report across QC, models, SHAP, pathways, and network."""
    dataset = db.query(DatasetRecord).filter(DatasetRecord.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    model_record = db.query(ModelRecord).filter(ModelRecord.id == request.model_id).first()
    if not model_record:
        raise HTTPException(status_code=404, detail="Model record not found")

    # Load model and dataset
    try:
        model = BaseBioAgeModel.load(model_record.artifact_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model artifact: {e}")

    df = pd.read_csv(dataset.file_path, index_col=0)
    age_col = dataset.age_column or "chronological_age"
    y = df[age_col]
    preds = model.predict(df)

    # 1. Acceleration
    covariates = df[["sex", "smoking_status", "bmi"]] if {"sex", "smoking_status", "bmi"}.issubset(df.columns) else None
    df_accel = compute_age_acceleration(y, preds, sample_ids=list(df.index), covariates_df=covariates)
    accel_summary = summarize_acceleration_cohort(df_accel)

    # 2. SHAP
    explainer = BioAgeShapExplainer(model)
    explainer.explain(df, sample_ids=list(df.index))
    top_biomarkers = explainer.get_global_importance(top_k=15)

    # 3. Pathways
    query_genes = [b["gene_symbol"] for b in top_biomarkers]
    pw_analyzer = PathwayEnrichmentAnalyzer()
    pathway_results = pw_analyzer.analyze(query_genes)

    # 4. Network
    edge_file = settings.EXAMPLE_DIR / "aging_network_edges.csv"
    edge_path = edge_file if edge_file.exists() else None
    bio_graph = BiologicalInteractionGraph()
    bio_graph.build_from_biomarkers(query_genes, edge_list_path=edge_path)
    cyto_export = bio_graph.to_cytoscape_json()

    # 5. Reference Clock Benchmarks
    from bioage.benchmarks.clocks import ReferenceClockBenchmarkSuite
    ref_suite = ReferenceClockBenchmarkSuite()
    benchmarks_data = [r.to_dict() for r in ref_suite.evaluate_all(df, age_col=age_col)]

    # 6. Record Biological Knowledge Provenance for this Experiment
    exp_id = f"EXP-{uuid.uuid4().hex[:8].upper()}"
    from bioage.integrations.provenance import get_provenance_tracker
    from bioage.integrations.base import KnowledgeStatus

    prov_tracker = get_provenance_tracker()
    prov_tracker.record(
        experiment_id=exp_id,
        provider="Ensembl",
        query_type="identifier_resolution",
        status=KnowledgeStatus.LIVE if any(b.get("ensembl_gene_id") for b in top_biomarkers) else KnowledgeStatus.LOCAL_FALLBACK,
        records_count=len(top_biomarkers),
        provider_version="GRCh38 / Ensembl 113",
        request_summary={"biomarkers": [b.get("gene_symbol") for b in top_biomarkers]},
    )
    prov_tracker.record(
        experiment_id=exp_id,
        provider="STRING",
        query_type="ppi_network",
        status=KnowledgeStatus(cyto_export["summary"].get("knowledge_status", "LOCAL_FALLBACK")),
        records_count=cyto_export["summary"].get("n_edges", 0),
        provider_version="v12.0",
        request_summary={"network_source": cyto_export["summary"].get("network_source", "hybrid"), "seeds": len(query_genes)},
    )
    prov_tracker.record(
        experiment_id=exp_id,
        provider="Reactome / Hallmark",
        query_type="pathway_enrichment",
        status=KnowledgeStatus.LOCAL_FALLBACK,
        records_count=len(pathway_results),
        provider_version="Release 91 & Curated Hallmarks",
        request_summary={"pathway_count": len(pathway_results)},
    )
    prov_summary = prov_tracker.get_summary(exp_id)

    # 7. Build Report
    reporter = ResearchReportGenerator()
    profile_data = json.loads(dataset.profile_json) if dataset.profile_json else {}

    model_metrics = {
        "mae": model_record.mae,
        "rmse": model_record.rmse,
        "r2": model_record.r2,
        "pearson_r": model_record.pearson_r,
        "spearman_rho": model_record.spearman_rho,
        "n_features": model_record.n_features,
        "training_time_sec": model_record.training_time_sec,
        "sample_count": dataset.n_samples,
    }

    report_data = reporter.build_report_data(
        experiment_id=exp_id,
        dataset_name=dataset.name,
        dataset_profile=profile_data,
        preprocessing_provenance={"dataset": dataset.name, "modality": dataset.detected_modality},
        model_name=model_record.model_type,
        model_metrics=model_metrics,
        acceleration_summary=accel_summary,
        top_biomarkers=top_biomarkers,
        pathway_enrichments=pathway_results,
        network_summary=cyto_export["summary"],
        benchmarks_summary=benchmarks_data,
        external_knowledge_provenance=prov_summary,
    )

    # 6. PDF Export
    pdf_filename = f"{exp_id}_BioAgeX_Report.pdf"
    pdf_path = settings.PROCESSED_DIR / pdf_filename
    export_report_to_pdf(report_data, pdf_path)

    # Save experiment record
    exp_record = ExperimentRecord(
        id=exp_id,
        name=request.experiment_name or f"Run_{model_record.model_type}_{dataset.name}",
        dataset_id=dataset.id,
        model_id=model_record.id,
        model_type=model_record.model_type,
        metrics_json=json.dumps(model_metrics),
        acceleration_summary_json=json.dumps(accel_summary),
        report_json=json.dumps(report_data),
        pdf_path=str(pdf_path),
        reproducibility_hash=report_data["metadata"]["reproducibility_hash"],
    )
    db.add(exp_record)
    db.commit()

    return ReportResponseSchema(
        experiment_id=exp_id,
        reproducibility_hash=report_data["metadata"]["reproducibility_hash"],
        pdf_url=f"/api/v1/reports/download/{pdf_filename}",
        report_data=report_data,
    )


@router.get("/download/{filename}")
def download_pdf_report(filename: str):
    """Serves the generated PDF report."""
    safe_name = Path(filename).name
    file_path = settings.PROCESSED_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    return FileResponse(file_path, media_type="application/pdf", filename=safe_name)
