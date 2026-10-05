"""
Research Report Generator for BioAge-X.
Synthesizes comprehensive scientific report across dataset QC, models, SHAP, pathways,
network biology, and GNN experimental results.
"""

from datetime import datetime
import hashlib
import json
from typing import Dict, Any, List, Optional

from bioage.utils.logger import get_logger

logger = get_logger("bioage.reporting.generator")


class ResearchReportGenerator:
    """Generates structured scientific research reports for BioAge-X experiments."""

    def build_report_data(
        self,
        experiment_id: str,
        dataset_name: str,
        dataset_profile: Dict[str, Any],
        preprocessing_provenance: Dict[str, Any],
        model_name: str,
        model_metrics: Dict[str, Any],
        acceleration_summary: Dict[str, Any],
        top_biomarkers: List[Dict[str, Any]],
        pathway_enrichments: List[Dict[str, Any]],
        network_summary: Dict[str, Any],
        gnn_summary: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Assembles all scientific findings into a cohesive research document."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Create reproducibility fingerprint
        hash_input = f"{experiment_id}_{dataset_name}_{model_name}_{timestamp}"
        reproducibility_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        report = {
            "title": "BioAge-X Computational Research Report",
            "subtitle": "Explainable Multi-Omics Biological Age Estimation & Network Analysis",
            "metadata": {
                "experiment_id": experiment_id,
                "dataset_name": dataset_name,
                "model_name": model_name,
                "generated_at": timestamp,
                "reproducibility_hash": reproducibility_hash,
                "platform_version": "0.1.0",
            },
            "executive_summary": {
                "sample_count": dataset_profile.get("n_samples", 0),
                "feature_count_used": model_metrics.get("n_features", 0),
                "model_mae_years": model_metrics.get("mae", 0.0),
                "model_r2": model_metrics.get("r2", 0.0),
                "pearson_correlation": model_metrics.get("pearson_r", 0.0),
                "mean_age_acceleration": acceleration_summary.get("mean_acceleration", 0.0),
                "top_biomarker": top_biomarkers[0]["gene_symbol"] if top_biomarkers else "N/A",
                "top_pathway": pathway_enrichments[0]["pathway_name"] if pathway_enrichments else "N/A",
            },
            "dataset_qc": {
                "samples": dataset_profile.get("n_samples", 0),
                "features": dataset_profile.get("n_features", 0),
                "orientation": dataset_profile.get("orientation", "samples_by_features"),
                "missing_fraction": dataset_profile.get("missing_fraction", 0.0),
                "detected_modality": dataset_profile.get("detected_modality", "unknown"),
                "warnings": dataset_profile.get("warnings", []),
            },
            "preprocessing": preprocessing_provenance,
            "model_performance": model_metrics,
            "age_acceleration": acceleration_summary,
            "shap_biomarkers": top_biomarkers[:10],
            "pathway_enrichment": pathway_enrichments[:8],
            "network_topology": network_summary,
            "gnn_results": gnn_summary or {},
            "scientific_limitations": [
                "BioAge-X is an educational and computational biology research platform, NOT a clinical diagnostic tool.",
                "Biological age acceleration represents statistical deviation from chronological norms and does not prove personal disease onset.",
                "Multi-omics datasets in this analysis may be subject to cohort-specific technical batch effects and tissue composition shifts.",
                "Experimental GNN and pathway predictions are hypothesis-generating computational projections.",
            ],
            "reproducibility": {
                "config": config or {},
                "run_hash": reproducibility_hash,
                "environment": "Python 3.12, PyTorch, scikit-learn, XGBoost, NetworkX",
            },
        }

        logger.info(f"Assembled research report for experiment {experiment_id} (hash: {reproducibility_hash})")
        return report
