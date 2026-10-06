"""
BioAge-X Evaluation Package.
Houses research-grade uncertainty estimation, robustness scoring,
dataset shift analysis, external validation, and ablation studies.
"""

from bioage.evaluation.uncertainty import (
    compute_bootstrap_confidence_interval,
    analyze_cross_validation_distribution,
    analyze_age_bias,
    analyze_cohort_stratification,
)
from bioage.evaluation.robustness import (
    calculate_biomarker_robustness_scores,
    audit_annotation_provenance,
    evaluate_network_perturbation_robustness,
    format_pathway_enrichment_with_universe,
)
from bioage.evaluation.external_validation import (
    analyze_dataset_shift,
    execute_external_validation,
)
from bioage.evaluation.ablation import (
    run_modality_ablation_comparison,
    run_fusion_ablation_comparison,
    run_feature_ablation_comparison,
    run_gnn_ablation_comparison,
)

__all__ = [
    "compute_bootstrap_confidence_interval",
    "analyze_cross_validation_distribution",
    "analyze_age_bias",
    "analyze_cohort_stratification",
    "calculate_biomarker_robustness_scores",
    "audit_annotation_provenance",
    "evaluate_network_perturbation_robustness",
    "format_pathway_enrichment_with_universe",
    "analyze_dataset_shift",
    "execute_external_validation",
    "run_modality_ablation_comparison",
    "run_fusion_ablation_comparison",
    "run_feature_ablation_comparison",
    "run_gnn_ablation_comparison",
]
