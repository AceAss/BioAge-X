"""Evaluation module for BioAge-X."""
from bioage.evaluation.metrics import ModelMetrics, evaluate_predictions
from bioage.evaluation.acceleration import (
    compute_age_acceleration,
    summarize_acceleration_cohort,
    SCIENTIFIC_DISCLAIMER,
)

from bioage.evaluation.cross_validation import DataLeakageDetector, BioAgeCrossValidator

__all__ = [
    "ModelMetrics",
    "evaluate_predictions",
    "compute_age_acceleration",
    "summarize_acceleration_cohort",
    "SCIENTIFIC_DISCLAIMER",
    "DataLeakageDetector",
    "BioAgeCrossValidator",
]
