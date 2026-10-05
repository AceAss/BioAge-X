"""
Biological Age & Age Acceleration Analysis for BioAge-X.
Defines:
    age_acceleration = predicted_biological_age - chronological_age
Provides cohort stratification, residual plotting datasets, and educational scientific disclaimers.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from scipy import stats

from bioage.utils.logger import get_logger

logger = get_logger("bioage.evaluation.acceleration")

SCIENTIFIC_DISCLAIMER = (
    "DISCLAIMER: BioAge-X is a computational research and educational platform, "
    "NOT a clinical diagnostic or prognostic tool. Biological age acceleration estimates "
    "reflect molecular discrepancies under specific statistical assumptions and do NOT "
    "constitute clinical proof of pathology, individual disease risk, or mortality."
)


def compute_age_acceleration(
    chronological_age: pd.Series | np.ndarray,
    predicted_bio_age: pd.Series | np.ndarray,
    sample_ids: Optional[List[str]] = None,
    covariates_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Computes biological age and age acceleration for each subject.
    Returns structured DataFrame with sample-level results and categorical strata.
    """
    c_age = np.asarray(chronological_age, dtype=float)
    b_age = np.asarray(predicted_bio_age, dtype=float)
    accel = b_age - c_age

    if sample_ids is None:
        if isinstance(chronological_age, pd.Series):
            sample_ids = [str(idx) for idx in chronological_age.index]
        else:
            sample_ids = [f"Sample_{i+1}" for i in range(len(c_age))]

    df_res = pd.DataFrame({
        "sample_id": sample_ids,
        "chronological_age": np.round(c_age, 2),
        "predicted_bio_age": np.round(b_age, 2),
        "age_acceleration": np.round(accel, 2),
        "acceleration_status": np.where(accel > 1.0, "Accelerated", np.where(accel < -1.0, "Decelerated", "Synchronous")),
    })

    if covariates_df is not None:
        for col in covariates_df.columns:
            if col not in df_res.columns:
                df_res[col] = covariates_df[col].values

    return df_res


def summarize_acceleration_cohort(df_accel: pd.DataFrame) -> Dict[str, Any]:
    """Generates cohort-level statistical summary for age acceleration."""
    accel = df_accel["age_acceleration"].values

    summary = {
        "mean_acceleration": round(float(np.mean(accel)), 2),
        "median_acceleration": round(float(np.median(accel)), 2),
        "std_acceleration": round(float(np.std(accel)), 2),
        "min_acceleration": round(float(np.min(accel)), 2),
        "max_acceleration": round(float(np.max(accel)), 2),
        "accelerated_count": int((df_accel["acceleration_status"] == "Accelerated").sum()),
        "decelerated_count": int((df_accel["acceleration_status"] == "Decelerated").sum()),
        "synchronous_count": int((df_accel["acceleration_status"] == "Synchronous").sum()),
        "disclaimer": SCIENTIFIC_DISCLAIMER,
    }

    # Stratified statistics if demographic columns exist
    stratified: Dict[str, Dict[str, Any]] = {}
    for col in ["sex", "smoking_status"]:
        if col in df_accel.columns:
            stratified[col] = {}
            for val, grp in df_accel.groupby(col):
                stratified[col][str(val)] = {
                    "count": int(len(grp)),
                    "mean_accel": round(float(grp["age_acceleration"].mean()), 2),
                    "std_accel": round(float(grp["age_acceleration"].std()), 2),
                }
    summary["stratified_stats"] = stratified
    return summary
