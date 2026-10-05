"""
Research Report Generator for BioAge-X.
Synthesizes comprehensive scientific report explicitly separated into:
Phase 1: Multi-Omics Biological Age Prediction & Epigenetic Clock Benchmarking
Phase 2: GraphOmics-AI Biological Network Analysis & GNN Experiments
"""

from datetime import datetime
import hashlib
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
        benchmarks_summary: Optional[List[Dict[str, Any]]] = None,
        external_knowledge_provenance: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Assembles all scientific findings into an explicitly phased research document."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Create reproducibility fingerprint
        hash_input = f"{experiment_id}_{dataset_name}_{model_name}_{timestamp}"
        reproducibility_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        # External knowledge provenance
        ext_knowledge = external_knowledge_provenance
        if ext_knowledge is None:
            try:
                from bioage.integrations.provenance import get_provenance_tracker
                ext_knowledge = get_provenance_tracker().get_summary(experiment_id)
            except Exception as e:
                logger.debug(f"Provenance fetch: {e}")
                ext_knowledge = {"total_queries": 0, "status_breakdown": {}, "providers_used": []}

        # Phase 1: BioAge Biological Age Prediction
        phase_1 = {
            "research_question": (
                "Does multi-omics integration improve biological-age prediction compared with "
                "individual molecular modalities and established biological-age clocks?"
            ),
            "hypothesis": (
                "Integrating DNA methylation with transcriptomics and phenotypic covariates captures complementary "
                "biological aging processes, reducing prediction error and yielding biologically coherent age acceleration."
            ),
            "dataset_qc": {
                "dataset_name": dataset_name,
                "samples": dataset_profile.get("n_samples", 0),
                "features": dataset_profile.get("n_features", 0),
                "orientation": dataset_profile.get("orientation", "samples_by_features"),
                "missing_fraction": dataset_profile.get("missing_fraction", 0.0),
                "detected_modality": dataset_profile.get("detected_modality", "unknown"),
                "warnings": dataset_profile.get("warnings", []),
            },
            "preprocessing": preprocessing_provenance,
            "primary_model": {
                "name": model_name,
                "metrics": model_metrics,
            },
            "reference_clock_benchmarks": benchmarks_summary or [],
            "age_acceleration": acceleration_summary,
            "candidate_biomarkers": top_biomarkers[:12],
        }

        # Phase 2: GraphOmics-AI
        phase_2 = {
            "research_question": (
                "Do molecular features associated with biological-age prediction form coherent biological "
                "interaction networks that can be characterized using graph-based learning?"
            ),
            "hypothesis": (
                "Candidate aging biomarkers identified in Phase 1 cluster within canonical hallmark interaction modules "
                "whose topological and spectral embeddings reflect cellular senescence, epigenetic remodeling, and inflammaging."
            ),
            "feature_to_gene_mapping": {
                "mapped_candidate_count": len(top_biomarkers),
                "seed_genes": [b.get("gene_symbol", b.get("feature", "N/A")) for b in top_biomarkers if b.get("gene_symbol")],
            },
            "network_topology": network_summary,
            "pathway_enrichment": pathway_enrichments[:8],
            "gnn_experimental_results": gnn_summary or {
                "status": "Available in GraphOmics-AI Workspace",
                "model_type": "BioAgeGCN / BioAgeGraphSAGE",
                "notice": "Graph neural network training is evaluated as a computational network signal.",
            },
        }

        report = {
            "title": "BioAge-X Computational Research Report",
            "subtitle": "Two-Phase Multi-Omics Biological Age Prediction & GraphOmics-AI Network Analysis",
            "metadata": {
                "experiment_id": experiment_id,
                "dataset_name": dataset_name,
                "model_name": model_name,
                "generated_at": timestamp,
                "reproducibility_hash": reproducibility_hash,
                "platform_version": "0.1.0",
                "disclaimer": "Educational and computational biology research platform only. Not a clinical diagnostic device.",
            },
            "phase_1_bioage": phase_1,
            "phase_2_graphomics": phase_2,
            "external_knowledge_sources": ext_knowledge,
            "scientific_limitations": [
                "BioAge-X is an educational and computational biology research platform, NOT a clinical diagnostic tool.",
                "Biological age acceleration represents statistical deviation from chronological norms and does not prove disease risk.",
                "Multi-omics datasets in this analysis may be subject to cohort-specific technical batch effects and tissue composition shifts.",
                "Experimental GNN and pathway predictions are hypothesis-generating computational projections.",
            ],
            "reproducibility": {
                "config": config or {},
                "run_hash": reproducibility_hash,
                "environment": "Python 3.12, PyTorch Geometric, scikit-learn, XGBoost, NetworkX, ReportLab",
            },
        }

        logger.info(f"Assembled Two-Phase research report for experiment {experiment_id} (hash: {reproducibility_hash})")
        return report
