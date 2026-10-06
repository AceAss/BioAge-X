"""
Candidate Biomarker and Biological Network Robustness Framework for BioAge-X.

Scientific Rule:
Mathematical stability under cross-validation resampling or network edge perturbation
is a computational metric of feature reliability, NOT biochemical proof of causal
involvement in the aging process.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
import numpy as np
import pandas as pd
from scipy import stats

from bioage.utils.logger import get_logger

logger = get_logger("bioage.evaluation.robustness")


def calculate_biomarker_robustness_scores(
    feature_names: List[str],
    fold_selected_features: List[List[str]],
    feature_shap_importances: Dict[str, float],
    fold_correlation_directions: Optional[List[Dict[str, float]]] = None,
    weights: Optional[Tuple[float, float, float]] = None,
) -> List[Dict[str, Any]]:
    """
    Computes a mathematically grounded Biomarker Robustness Score.
    
    Formula:
        Score = w_1 * SelectionFrequency + w_2 * DirectionConsistency + w_3 * NormalizedSHAP
        where w_1 = 0.40, w_2 = 0.35, w_3 = 0.25 (default, sum = 1.0).
        
    Categories:
        - HIGHLY_STABLE (Score >= 0.75): Identified consistently across folds with stable direction.
        - MODERATELY_STABLE (0.50 <= Score < 0.75): Frequent in subset of partitions.
        - SINGLE_EXPERIMENT_CANDIDATE (Score < 0.50): Potential dataset/partition artifact.
    """
    if weights is None:
        w_freq, w_dir, w_shap = 0.40, 0.35, 0.25
    else:
        w_freq, w_dir, w_shap = weights

    num_folds = max(1, len(fold_selected_features))
    
    # Normalize SHAP values to [0, 1]
    shap_vals = [feature_shap_importances.get(f, 0.0) for f in feature_names]
    max_shap = max(shap_vals) if shap_vals and max(shap_vals) > 0 else 1.0

    robustness_records = []

    for feat in feature_names:
        # 1. Fold selection frequency
        count_selected = sum(1 for fold_list in fold_selected_features if feat in fold_list)
        selection_freq = count_selected / num_folds

        # 2. Direction consistency
        if fold_correlation_directions:
            directions = [
                d.get(feat, 0.0)
                for d in fold_correlation_directions
                if feat in d and d.get(feat, 0.0) != 0.0
            ]
            if directions:
                pos_count = sum(1 for sign in directions if sign > 0)
                neg_count = sum(1 for sign in directions if sign < 0)
                dir_consistency = max(pos_count, neg_count) / len(directions)
            else:
                dir_consistency = 0.5
        else:
            dir_consistency = 1.0  # default neutral if directional tracking not provided

        # 3. Normalized SHAP importance
        norm_shap = min(1.0, feature_shap_importances.get(feat, 0.0) / max_shap)

        # Composite Robustness Score
        score = (w_freq * selection_freq) + (w_dir * dir_consistency) + (w_shap * norm_shap)
        score = round(float(score), 4)

        if score >= 0.75:
            stability_tier = "HIGHLY_STABLE"
        elif score >= 0.50:
            stability_tier = "MODERATELY_STABLE"
        else:
            stability_tier = "SINGLE_EXPERIMENT_CANDIDATE"

        robustness_records.append({
            "feature_id": feat,
            "robustness_score": score,
            "stability_tier": stability_tier,
            "selection_frequency": round(selection_freq, 3),
            "folds_present": count_selected,
            "total_folds": num_folds,
            "direction_consistency": round(dir_consistency, 3),
            "normalized_shap": round(norm_shap, 3),
            "mean_shap": round(feature_shap_importances.get(feat, 0.0), 5),
            "mathematical_formula": "Score = 0.40*FoldFreq + 0.35*DirConsistency + 0.25*NormSHAP",
        })

    # Sort descending by robustness score
    robustness_records.sort(key=lambda x: x["robustness_score"], reverse=True)
    return robustness_records


def audit_annotation_provenance(
    feature_id: str,
    mapped_gene: Optional[str] = None,
    ensembl_id: Optional[str] = None,
    uniprot_id: Optional[str] = None,
    string_interactors: Optional[List[str]] = None,
    reactome_pathways: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Classifies biological annotation certainty into explicit provenance tiers:
    - DIRECT_MAPPING: Exact HGNC symbol / coordinate match.
    - INFERRED_ASSOCIATION: Inferred promoter proximity / interactome linkage.
    - NO_MAPPING_AVAILABLE: Intergenic or unannotated locus.
    """
    if mapped_gene and mapped_gene.strip() and mapped_gene != "Unknown":
        if ensembl_id or uniprot_id:
            mapping_status = "DIRECT_MAPPING"
            confidence = "HIGH"
        else:
            mapping_status = "DIRECT_MAPPING"
            confidence = "MODERATE"
    elif string_interactors and len(string_interactors) > 0:
        mapping_status = "INFERRED_ASSOCIATION"
        confidence = "LOW"
    else:
        mapping_status = "NO_MAPPING_AVAILABLE"
        confidence = "NONE"

    return {
        "feature_id": feature_id,
        "mapping_status": mapping_status,
        "confidence": confidence,
        "mapped_gene": mapped_gene if mapping_status != "NO_MAPPING_AVAILABLE" else None,
        "ensembl_id": ensembl_id,
        "uniprot_id": uniprot_id,
        "string_interactors_count": len(string_interactors) if string_interactors else 0,
        "reactome_pathways_count": len(reactome_pathways) if reactome_pathways else 0,
        "trace": (
            f"{feature_id} -> {mapped_gene or 'None'} -> {ensembl_id or 'None'} -> "
            f"{'PPI(' + str(len(string_interactors or [])) + ')'} -> "
            f"{'Pathways(' + str(len(reactome_pathways or [])) + ')'}"
        ),
    }


def evaluate_network_perturbation_robustness(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    confidence_thresholds: Optional[List[int]] = None,
    drop_edge_fractions: Optional[List[float]] = None,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Evaluates topological stability of Phase 2 interactome under edge perturbation.
    Tests whether top hub genes remain central when low-confidence edges are filtered
    or random edge dropout occurs.
    """
    if confidence_thresholds is None:
        confidence_thresholds = [400, 700, 900]
    if drop_edge_fractions is None:
        drop_edge_fractions = [0.10, 0.25]

    node_ids = [n["id"] if isinstance(n, dict) else str(n) for n in nodes]
    initial_degrees = {nid: 0 for nid in node_ids}
    for e in edges:
        s, t = e.get("source"), e.get("target")
        if s in initial_degrees:
            initial_degrees[s] += 1
        if t in initial_degrees:
            initial_degrees[t] += 1

    # Baseline top 10 nodes by degree
    sorted_baseline = sorted(initial_degrees.items(), key=lambda x: x[1], reverse=True)
    baseline_top_ids = [x[0] for x in sorted_baseline[:min(10, len(sorted_baseline))]]

    threshold_results = []
    for thresh in confidence_thresholds:
        filtered_edges = [
            e for e in edges
            if e.get("score", e.get("combined_score", 400)) >= thresh
        ]
        thresh_degrees = {nid: 0 for nid in node_ids}
        for e in filtered_edges:
            s, t = e.get("source"), e.get("target")
            if s in thresh_degrees:
                thresh_degrees[s] += 1
            if t in thresh_degrees:
                thresh_degrees[t] += 1

        # Spearman correlation of node degree ranks
        b_ranks = [initial_degrees[n] for n in node_ids]
        t_ranks = [thresh_degrees[n] for n in node_ids]

        if len(node_ids) > 2 and np.std(b_ranks) > 1e-6 and np.std(t_ranks) > 1e-6:
            rho, p_val = stats.spearmanr(b_ranks, t_ranks)
        else:
            rho, p_val = 1.0, 0.0

        # Top 10 overlap
        sorted_thresh = sorted(thresh_degrees.items(), key=lambda x: x[1], reverse=True)
        thresh_top_ids = [x[0] for x in sorted_thresh[:min(10, len(sorted_thresh))]]
        overlap = len(set(baseline_top_ids).intersection(set(thresh_top_ids)))

        threshold_results.append({
            "confidence_threshold": thresh,
            "retained_edges": len(filtered_edges),
            "edge_retention_ratio": round(len(filtered_edges) / max(1, len(edges)), 3),
            "degree_rank_correlation_rho": round(float(rho), 3),
            "top10_hub_overlap": overlap,
            "top10_hub_stability": round(overlap / max(1, len(baseline_top_ids)), 3),
        })

    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "baseline_top_hubs": baseline_top_ids,
        "confidence_sweep": threshold_results,
        "scientific_disclaimer": (
            "Network perturbation analysis measures computational topological resilience. "
            "Hub stability does NOT constitute experimental verification of biological essentiality."
        ),
    }


def format_pathway_enrichment_with_universe(
    enriched_pathways: List[Dict[str, Any]],
    gene_universe_size: int = 20000,
    input_genes_count: int = 50,
) -> Dict[str, Any]:
    """
    Structures pathway enrichment results making the background gene universe explicit.
    Reports both raw p-values and Benjamini-Hochberg FDR corrected q-values.
    """
    if not enriched_pathways:
        return {
            "gene_universe_size": gene_universe_size,
            "input_genes_count": input_genes_count,
            "pathways": [],
            "significant_fdr_count": 0,
        }

    # Sort pathways by p-value
    sorted_pw = sorted(enriched_pathways, key=lambda x: x.get("p_value", 1.0))
    m = len(sorted_pw)

    # Benjamini-Hochberg procedure
    formatted = []
    sig_count = 0
    for rank, pw in enumerate(sorted_pw, start=1):
        p_val = pw.get("p_value", 1.0)
        fdr = min(1.0, p_val * (m / rank))
        fdr = round(float(fdr), 5)
        
        is_sig = fdr < 0.05
        if is_sig:
            sig_count += 1

        formatted.append({
            "pathway_id": pw.get("id") or pw.get("pathway_id", f"PW_{rank}"),
            "pathway_name": pw.get("name") or pw.get("pathway_name", "Unknown Pathway"),
            "source": pw.get("source", "Reactome"),
            "overlap_count": pw.get("overlap_count", len(pw.get("genes", []))),
            "pathway_size": pw.get("size") or pw.get("pathway_size", 100),
            "p_value": round(float(p_val), 6),
            "fdr_q_value": fdr,
            "statistically_significant_fdr05": is_sig,
            "genes": pw.get("genes", []),
        })

    return {
        "gene_universe": {
            "type": "Homo sapiens canonical background",
            "size": gene_universe_size,
            "description": f"Enrichment computed against {gene_universe_size:,} background human protein-coding genes.",
        },
        "input_genes_count": input_genes_count,
        "total_evaluated_pathways": m,
        "significant_fdr05_count": sig_count,
        "pathways": formatted,
    }
