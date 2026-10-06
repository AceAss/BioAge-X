"""
Formal Scientific Ablation Studies Framework for BioAge-X.

Scientific Rule:
Ablation studies isolate individual components of the multi-omics and computational
pipeline to verify whether each added complexity layer (e.g. adding a second modality,
network graph topology, or GNN message-passing) produces a genuine empirical gain
or merely parameter inflation.
"""

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from bioage.utils.logger import get_logger

logger = get_logger("bioage.evaluation.ablation")


def run_modality_ablation_comparison(
    metrics_by_modality: Dict[str, Dict[str, float]],
) -> Dict[str, Any]:
    """
    Evaluates incremental predictive benefit of multi-omics vs single-modality models.
    Compares:
      - Methylation only
      - Transcriptomics only
      - Multi-Omics (Methylation + Transcriptomics)
      - Multi-Omics + Clinical (if present)
    """
    ordered_modalities = ["Methylation only", "Transcriptomics only", "Multi-Omics (Meth + Trans)", "Multi-Omics + Clinical"]
    available_modalities = [m for m in ordered_modalities if m in metrics_by_modality]

    if not available_modalities:
        available_modalities = list(metrics_by_modality.keys())

    comparisons = []
    baseline_modality = available_modalities[0] if available_modalities else "None"
    baseline_mae = metrics_by_modality.get(baseline_modality, {}).get("mae", 5.0)

    for mod in available_modalities:
        m_data = metrics_by_modality[mod]
        mae = m_data.get("mae", 0.0)
        r2 = m_data.get("r2", 0.0)
        rmse = m_data.get("rmse", np.sqrt(mae * 1.3))

        delta_mae = mae - baseline_mae
        pct_improvement = ((baseline_mae - mae) / baseline_mae * 100.0) if baseline_mae > 0 else 0.0

        comparisons.append({
            "modality_condition": mod,
            "mae": round(float(mae), 3),
            "rmse": round(float(rmse), 3),
            "r2": round(float(r2), 3),
            "delta_mae_vs_baseline": round(float(delta_mae), 3),
            "pct_improvement": round(float(pct_improvement), 2),
            "scientific_verdict": (
                "Synergistic performance gain" if pct_improvement > 10.0
                else ("Marginal change (<10%)" if pct_improvement > 0 else "No incremental gain")
            ),
        })

    return {
        "ablation_type": "MODALITY_ABLATION",
        "baseline_modality": baseline_modality,
        "conditions_evaluated": len(comparisons),
        "results": comparisons,
        "summary": (
            "Modality ablation quantifies whether combining orthogonal omic layers "
            "improves biological age resolution over single-assay benchmarks."
        ),
    }


def run_fusion_ablation_comparison(
    metrics_by_fusion: Dict[str, Dict[str, float]],
) -> Dict[str, Any]:
    """
    Evaluates multi-omics integration strategies:
      - Early Fusion (concatenation at feature level)
      - Late Fusion (averaging independent model predictions)
      - Weighted Ensemble (inverse-variance weighting)
    """
    fusion_types = ["Early Fusion", "Late Fusion", "Weighted Ensemble"]
    results = []

    best_mae = float("inf")
    best_fusion = None

    for f_type in fusion_types:
        if f_type not in metrics_by_fusion:
            continue
        data = metrics_by_fusion[f_type]
        mae = data.get("mae", 0.0)
        rmse = data.get("rmse", 0.0)
        r2 = data.get("r2", 0.0)

        if mae < best_mae:
            best_mae = mae
            best_fusion = f_type

        results.append({
            "fusion_strategy": f_type,
            "mae": round(float(mae), 3),
            "rmse": round(float(rmse), 3),
            "r2": round(float(r2), 3),
            "pearson_r": round(float(data.get("pearson_r", np.sqrt(max(0, r2)))), 3),
        })

    return {
        "ablation_type": "FUSION_ABLATION",
        "optimal_strategy": best_fusion,
        "results": results,
        "scientific_interpretation": (
            f"Ablation identifies {best_fusion} as achieving lowest prediction error (MAE={best_mae:.2f} yrs). "
            "Examines whether cross-modal interactions require joint early representations or late consensus."
        ),
    }


def run_feature_ablation_comparison(
    metrics_by_feature_tier: Dict[str, Dict[str, float]],
) -> Dict[str, Any]:
    """
    Evaluates model compactness vs predictive power:
      - All Candidate Features (e.g. 100 features)
      - Top 50 SHAP Features
      - Top 20 SHAP Features
      - Top 10 Minimal Signature
    """
    results = []
    baseline_mae = None

    for tier, data in metrics_by_feature_tier.items():
        mae = data.get("mae", 0.0)
        if baseline_mae is None:
            baseline_mae = mae

        delta_mae = mae - baseline_mae
        results.append({
            "feature_set": tier,
            "feature_count": data.get("feature_count", 0),
            "mae": round(float(mae), 3),
            "rmse": round(float(data.get("rmse", 0.0)), 3),
            "r2": round(float(data.get("r2", 0.0)), 3),
            "delta_mae_vs_all": round(float(delta_mae), 3),
        })

    return {
        "ablation_type": "FEATURE_ABLATION",
        "results": results,
        "scientific_interpretation": (
            "Feature ablation determines the minimum biomarker signature required to preserve biological clock accuracy."
        ),
    }


def run_gnn_ablation_comparison(
    tabular_baseline_metrics: Dict[str, float],
    gnn_metrics_by_model: Dict[str, Dict[str, float]],
) -> Dict[str, Any]:
    """
    Evaluates the core question of Phase 2:
    Does adding interactome topology (GCN / GraphSAGE) provide an advantage
    over standard tabular ML models (ElasticNet / XGBoost)?
    
    Ablations:
      - Tabular Baseline (No Graph Topology)
      - Graph without Biomarker Signal (Topology only, random node features)
      - Graph + Molecular Node Features (GCN / GraphSAGE with Phase 1 embeddings)
    """
    results = []

    tab_mae = tabular_baseline_metrics.get("mae", 3.8)
    tab_r2 = tabular_baseline_metrics.get("r2", 0.90)

    results.append({
        "model_condition": "Tabular ML Baseline (ElasticNet/RF)",
        "graph_topology_used": False,
        "biomarker_features_used": True,
        "mae": round(float(tab_mae), 3),
        "r2": round(float(tab_r2), 3),
        "type": "BASELINE",
    })

    for model_name, data in gnn_metrics_by_model.items():
        mae = data.get("mae", 0.0)
        r2 = data.get("r2", 0.0)
        has_signal = data.get("has_biomarker_signal", True)

        delta_mae = mae - tab_mae

        results.append({
            "model_condition": f"GNN ({model_name}) - {'With Signal' if has_signal else 'Topology Only'}",
            "graph_topology_used": True,
            "biomarker_features_used": has_signal,
            "mae": round(float(mae), 3),
            "r2": round(float(r2), 3),
            "delta_mae_vs_tabular": round(float(delta_mae), 3),
            "type": "GNN_ABLATION",
        })

    return {
        "ablation_type": "GNN_INTERACTOME_ABLATION",
        "results": results,
        "scientific_interpretation": (
            "GNN interactome ablation directly addresses whether protein-protein interaction topology "
            "refines biological age predictions beyond tabular regularized regression."
        ),
    }
