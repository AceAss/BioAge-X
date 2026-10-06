"""
External Validation and Dataset Shift Analysis Framework for BioAge-X.

Scientific Rule:
True biological generalization requires validation on an independent external cohort
WITHOUT model retraining. When external validation suffers performance degradation,
Dataset Shift Analysis determines whether the decline reflects model fragility
or fundamental biological/demographic divergence between cohorts.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

from bioage.utils.logger import get_logger

logger = get_logger("bioage.evaluation.external_validation")


def analyze_dataset_shift(
    train_df: pd.DataFrame,
    external_df: pd.DataFrame,
    age_col: str = "age",
    train_cohort_name: str = "Training Cohort",
    external_cohort_name: str = "External Cohort",
    shared_features: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Quantifies demographic and molecular distribution shifts between training and external cohorts.
    
    Tests:
    1. Chronological Age Shift: Kolmogorov-Smirnov test and Wasserstein distance.
    2. Shared Feature Shifts: Feature-level mean absolute standardized divergence.
    3. Missingness / Sparsity divergence.
    """
    train_age = train_df[age_col].dropna().values.astype(float)
    ext_age = external_df[age_col].dropna().values.astype(float)

    # 1. Age distribution comparison
    ks_stat, ks_pval = stats.ks_2samp(train_age, ext_age)
    mean_diff_age = float(np.mean(ext_age) - np.mean(train_age))

    age_shift_detected = bool(ks_pval < 0.01)

    # 2. Molecular feature shift on shared columns
    if shared_features is None:
        shared_cols = [c for c in train_df.columns if c in external_df.columns and c != age_col]
    else:
        shared_cols = [c for c in shared_features if c in train_df.columns and c in external_df.columns]

    feature_shifts = []
    large_shift_count = 0

    for col in shared_cols[:50]:  # Top 50 shared features
        tr_vals = train_df[col].dropna().values.astype(float)
        ex_vals = external_df[col].dropna().values.astype(float)

        if len(tr_vals) < 3 or len(ex_vals) < 3:
            continue

        pooled_sd = np.sqrt((np.var(tr_vals, ddof=1) + np.var(ex_vals, ddof=1)) / 2.0)
        cohens_d = float(abs(np.mean(ex_vals) - np.mean(tr_vals)) / (pooled_sd + 1e-8))

        if cohens_d > 0.8:  # Large effect size divergence
            large_shift_count += 1

        feature_shifts.append({
            "feature": col,
            "train_mean": round(float(np.mean(tr_vals)), 4),
            "external_mean": round(float(np.mean(ex_vals)), 4),
            "cohens_d": round(cohens_d, 3),
            "divergence": "HIGH" if cohens_d > 0.8 else ("MODERATE" if cohens_d > 0.5 else "LOW"),
        })

    total_evaluated = len(feature_shifts)
    shift_fraction = large_shift_count / max(1, total_evaluated)

    if shift_fraction > 0.40 or (age_shift_detected and abs(mean_diff_age) > 15.0):
        overall_verdict = "SEVERE_DATASET_SHIFT"
        verdict_msg = (
            f"Significant cohort shift detected between {train_cohort_name} and {external_cohort_name}. "
            "Performance degradation on external validation is expected and primarily reflects biological/demographic divergence."
        )
    elif shift_fraction > 0.15 or age_shift_detected:
        overall_verdict = "MODERATE_DATASET_SHIFT"
        verdict_msg = "Moderate covariate shift observed. Retain caution when interpreting external residuals."
    else:
        overall_verdict = "MINIMAL_SHIFT"
        verdict_msg = "Cohorts display compatible demographic and molecular distributions."

    return {
        "train_cohort": train_cohort_name,
        "external_cohort": external_cohort_name,
        "sample_counts": {
            "train_n": len(train_age),
            "external_n": len(ext_age),
        },
        "age_distribution": {
            "train_age_mean": round(float(np.mean(train_age)), 2),
            "train_age_sd": round(float(np.std(train_age)), 2),
            "train_age_range": [round(float(np.min(train_age)), 1), round(float(np.max(train_age)), 1)],
            "external_age_mean": round(float(np.mean(ext_age)), 2),
            "external_age_sd": round(float(np.std(ext_age)), 2),
            "external_age_range": [round(float(np.min(ext_age)), 1), round(float(np.max(ext_age)), 1)],
            "ks_statistic": round(float(ks_stat), 4),
            "ks_p_value": float(ks_pval),
            "age_shift_detected": age_shift_detected,
            "mean_age_difference_years": round(mean_diff_age, 2),
        },
        "molecular_shift": {
            "shared_features_evaluated": total_evaluated,
            "divergent_features_count": large_shift_count,
            "divergent_fraction": round(shift_fraction, 3),
            "top_divergent_features": sorted(feature_shifts, key=lambda x: x["cohens_d"], reverse=True)[:10],
        },
        "overall_shift_verdict": overall_verdict,
        "shift_interpretation": verdict_msg,
    }


def execute_external_validation(
    trained_model: Any,
    trained_features: List[str],
    external_df: pd.DataFrame,
    age_col: str = "age",
    train_dataset_name: str = "Training Cohort",
    external_dataset_name: str = "External Cohort",
    min_overlap_ratio: float = 0.10,
) -> Dict[str, Any]:
    """
    Executes external cohort validation WITHOUT retraining.
    
    Enforces scientific guardrail:
    If feature overlap is < 10% or external dataset is incompatible,
    returns EXTERNAL_VALIDATION_NOT_AVAILABLE rather than fabricating predictions.
    """
    if external_df is None or len(external_df) == 0:
        return {
            "status": "EXTERNAL_VALIDATION_NOT_AVAILABLE",
            "message": "No external validation cohort supplied or dataset is empty.",
            "metrics": None,
        }

    if age_col not in external_df.columns:
        return {
            "status": "EXTERNAL_VALIDATION_NOT_AVAILABLE",
            "message": f"Target chronological age column '{age_col}' missing in external dataset.",
            "metrics": None,
        }

    # Identify overlapping features
    ext_cols = set(external_df.columns)
    shared_features = [f for f in trained_features if f in ext_cols]
    overlap_ratio = len(shared_features) / max(1, len(trained_features))

    if overlap_ratio < min_overlap_ratio or len(shared_features) < 3:
        return {
            "status": "EXTERNAL_VALIDATION_NOT_AVAILABLE",
            "message": (
                f"Feature overlap between {train_dataset_name} and {external_dataset_name} is only "
                f"{len(shared_features)}/{len(trained_features)} ({overlap_ratio:.1%}). "
                f"Minimum scientific threshold ({min_overlap_ratio:.0%}) not met. "
                "EXTERNAL VALIDATION NOT AVAILABLE FOR CURRENT DATASET."
            ),
            "overlap_ratio": round(overlap_ratio, 3),
            "shared_features_count": len(shared_features),
            "required_features_count": len(trained_features),
            "metrics": None,
        }

    # Prepare external feature matrix
    y_ext = external_df[age_col].dropna().values.astype(float)
    X_ext = pd.DataFrame(index=external_df.index)

    for f in trained_features:
        if f in external_df.columns:
            X_ext[f] = external_df[f].fillna(external_df[f].median()).values
        else:
            # Impute unmeasured features with neutral 0 / median from train if needed
            X_ext[f] = 0.0

    # Ensure clean non-null arrays
    valid_idx = ~np.isnan(y_ext)
    X_ext_clean = X_ext.iloc[valid_idx].values
    y_ext_clean = y_ext[valid_idx]

    if len(y_ext_clean) < 5:
        return {
            "status": "INSUFFICIENT_SAMPLE_SIZE",
            "message": f"External dataset has too few valid samples (N={len(y_ext_clean)}).",
            "metrics": None,
        }

    # Predict biological age without retraining
    try:
        y_pred = trained_model.predict(X_ext_clean)
        residuals = y_pred - y_ext_clean

        mae = float(np.mean(np.abs(residuals)))
        rmse = float(np.sqrt(np.mean(residuals ** 2)))

        if np.std(y_ext_clean) > 1e-6 and np.std(y_pred) > 1e-6:
            r, p_val = stats.pearsonr(y_ext_clean, y_pred)
            spearman_rho, sp_val = stats.spearmanr(y_ext_clean, y_pred)
            r2 = float(r ** 2)
        else:
            r, p_val = 0.0, 1.0
            spearman_rho, sp_val = 0.0, 1.0
            r2 = 0.0

        return {
            "status": "VALIDATED",
            "train_dataset": train_dataset_name,
            "external_dataset": external_dataset_name,
            "sample_count": len(y_ext_clean),
            "features_overlap": {
                "shared_count": len(shared_features),
                "total_trained_features": len(trained_features),
                "overlap_ratio": round(overlap_ratio, 3),
                "missing_features_imputed": len(trained_features) - len(shared_features),
            },
            "metrics": {
                "mae": round(mae, 3),
                "rmse": round(rmse, 3),
                "r2": round(r2, 3),
                "pearson_r": round(float(r), 3),
                "pearson_p_value": float(p_val),
                "spearman_rho": round(float(spearman_rho), 3),
                "mean_bias": round(float(np.mean(residuals)), 3),
                "age_acceleration_sd": round(float(np.std(residuals)), 3),
            },
            "scientific_interpretation": (
                f"Model generalized to external cohort {external_dataset_name} with MAE={mae:.2f} yrs and R²={r2:.3f}. "
                f"Trained on {len(trained_features)} features, {len(shared_features)} directly matched."
            ),
        }
    except Exception as e:
        logger.error(f"External validation execution failed: {e}")
        return {
            "status": "EXECUTION_ERROR",
            "message": f"External validation prediction failed: {str(e)}",
            "metrics": None,
        }
