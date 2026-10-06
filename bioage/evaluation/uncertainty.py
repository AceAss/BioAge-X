"""
Uncertainty and Statistical Evaluation Module for BioAge-X.
Provides bootstrap confidence intervals, fold-level metric distributions,
age-bias analysis, and cohort subgroup stratification.

Scientific Rule:
Model uncertainty (statistical variance across resamplings/folds) is strictly
distinguished from biological uncertainty (unmeasured omic layers, stochastic
cellular drift, or environmental confounders).
"""

from typing import Dict, List, Any, Optional, Tuple, Callable
import numpy as np
import pandas as pd
from scipy import stats

from bioage.utils.logger import get_logger

logger = get_logger("bioage.evaluation.uncertainty")


def compute_bootstrap_confidence_interval(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metric_fn: Callable[[np.ndarray, np.ndarray], float],
    n_bootstraps: int = 1000,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Computes empirical bootstrap confidence intervals for a regression metric.
    
    Args:
        y_true: Array of ground-truth chronological ages.
        y_pred: Array of model-predicted biological ages.
        metric_fn: Function accepting (y_true, y_pred) and returning float metric.
        n_bootstraps: Number of bootstrap iterations (default 1000).
        confidence_level: Desired interval coverage (default 0.95).
        seed: Random seed for deterministic reproducibility.
        
    Returns:
        Dict containing point estimate, CI lower, CI upper, standard error,
        and bootstrap sample distribution statistics.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    n = len(y_true)

    if n < 5:
        return {
            "point_estimate": float(metric_fn(y_true, y_pred)) if n > 0 else 0.0,
            "ci_lower": None,
            "ci_upper": None,
            "std_error": None,
            "confidence_level": confidence_level,
            "n_bootstraps": 0,
            "warning": "Sample size too small for statistical bootstrap (n < 5)",
        }

    rng = np.random.RandomState(seed)
    point_est = float(metric_fn(y_true, y_pred))
    boot_estimates = np.empty(n_bootstraps, dtype=float)

    for i in range(n_bootstraps):
        idx = rng.choice(n, size=n, replace=True)
        boot_estimates[i] = metric_fn(y_true[idx], y_pred[idx])

    alpha = 1.0 - confidence_level
    ci_lower = float(np.percentile(boot_estimates, 100.0 * (alpha / 2.0)))
    ci_upper = float(np.percentile(boot_estimates, 100.0 * (1.0 - alpha / 2.0)))
    se = float(np.std(boot_estimates, ddof=1))

    return {
        "point_estimate": round(point_est, 4),
        "ci_lower": round(ci_lower, 4),
        "ci_upper": round(ci_upper, 4),
        "std_error": round(se, 4),
        "confidence_level": confidence_level,
        "n_bootstraps": n_bootstraps,
        "median_bootstrap": round(float(np.median(boot_estimates)), 4),
        "iqr_bootstrap": round(float(np.percentile(boot_estimates, 75) - np.percentile(boot_estimates, 25)), 4),
    }


def analyze_cross_validation_distribution(
    fold_metrics: List[Dict[str, float]],
) -> Dict[str, Any]:
    """
    Summarizes fold-level evaluation distributions preserving fold-by-fold records.
    Prevents single aggregate score opacity by reporting distributions, dispersion,
    and outlier folds.
    """
    if not fold_metrics:
        return {"folds": [], "summary": {}}

    keys = list(fold_metrics[0].keys())
    summary: Dict[str, Any] = {}

    for k in keys:
        values = [f[k] for f in fold_metrics if k in f and not np.isnan(f[k])]
        if not values:
            continue
        arr = np.array(values, dtype=float)
        summary[k] = {
            "mean": round(float(np.mean(arr)), 4),
            "std": round(float(np.std(arr, ddof=1 if len(arr) > 1 else 0)), 4),
            "median": round(float(np.median(arr)), 4),
            "min": round(float(np.min(arr)), 4),
            "max": round(float(np.max(arr)), 4),
            "iqr": round(float(np.percentile(arr, 75) - np.percentile(arr, 25)), 4),
            "values": [round(float(v), 4) for v in values],
        }

    return {
        "num_folds": len(fold_metrics),
        "fold_records": fold_metrics,
        "summary": summary,
    }


def analyze_age_bias(
    chronological_age: np.ndarray,
    predicted_age: np.ndarray,
    age_bins: Optional[List[Tuple[float, float, str]]] = None,
) -> Dict[str, Any]:
    """
    Analyzes systematic prediction bias across chronological age ranges.
    
    Identifies common biological clock phenomenon of "regression toward the mean"
    where young subjects are over-predicted (positive bias) and elderly subjects
    are under-predicted (negative bias).
    """
    y_true = np.asarray(chronological_age, dtype=float)
    y_pred = np.asarray(predicted_age, dtype=float)
    residuals = y_pred - y_true  # Positive: predicted older, Negative: predicted younger

    if age_bins is None:
        age_bins = [
            (0.0, 40.0, "Young (<40 yrs)"),
            (40.0, 65.0, "Middle-Aged (40-65 yrs)"),
            (65.0, 120.0, "Older Adult (>65 yrs)"),
        ]

    bin_results = []
    for low, high, label in age_bins:
        mask = (y_true >= low) & (y_true < high)
        n_bin = int(np.sum(mask))

        if n_bin < 3:
            bin_results.append({
                "label": label,
                "range": [low, high],
                "sample_count": n_bin,
                "status": "INSUFFICIENT_SAMPLE_SIZE",
                "mean_bias": None,
                "mae": None,
                "rmse": None,
                "r2": None,
            })
            continue

        bin_true = y_true[mask]
        bin_pred = y_pred[mask]
        bin_res = residuals[mask]

        bin_mae = float(np.mean(np.abs(bin_res)))
        bin_rmse = float(np.sqrt(np.mean(bin_res ** 2)))
        bin_bias = float(np.mean(bin_res))

        # Correlation within bin
        if len(bin_true) > 2 and np.std(bin_true) > 1e-6 and np.std(bin_pred) > 1e-6:
            r, p_val = stats.pearsonr(bin_true, bin_pred)
            r2 = float(r ** 2)
        else:
            r2 = 0.0

        bin_results.append({
            "label": label,
            "range": [low, high],
            "sample_count": n_bin,
            "status": "EVALUATED",
            "mean_bias": round(bin_bias, 3),
            "mae": round(bin_mae, 3),
            "rmse": round(bin_rmse, 3),
            "r2": round(r2, 3),
            "std_residual": round(float(np.std(bin_res)), 3),
        })

    # Overall regression toward the mean slope
    # Fit: Residual = alpha + beta * TrueAge
    if len(y_true) > 5 and np.std(y_true) > 1e-6:
        slope, intercept, r_val, p_val, std_err = stats.linregress(y_true, residuals)
        regression_toward_mean_slope = round(float(slope), 4)
        regression_toward_mean_p_val = float(p_val)
    else:
        regression_toward_mean_slope = 0.0
        regression_toward_mean_p_val = 1.0

    return {
        "total_samples": len(y_true),
        "age_bins": bin_results,
        "regression_toward_mean": {
            "slope": regression_toward_mean_slope,
            "p_value": regression_toward_mean_p_val,
            "interpretation": (
                "Statistically significant age bias (regression toward the mean)"
                if regression_toward_mean_p_val < 0.05 and regression_toward_mean_slope < 0
                else "No significant linear age-dependent bias detected"
            ),
        },
    }


def analyze_cohort_stratification(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metadata_df: pd.DataFrame,
    group_col: str,
    min_subgroup_size: int = 10,
) -> Dict[str, Any]:
    """
    Evaluates biological age prediction across phenotypic subgroups (e.g. Sex, Tissue, Batch).
    Enforces scientific guardrail: reports INSUFFICIENT_SAMPLE_SIZE if group N < min_subgroup_size.
    """
    if group_col not in metadata_df.columns:
        return {
            "group_column": group_col,
            "error": f"Metadata column '{group_col}' not found in cohort annotations.",
            "subgroups": {},
        }

    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    groups = metadata_df[group_col].values

    subgroup_analysis: Dict[str, Any] = {}
    unique_groups = pd.Series(groups).dropna().unique()

    for grp in unique_groups:
        grp_str = str(grp)
        mask = (groups == grp)
        n_grp = int(np.sum(mask))

        if n_grp < min_subgroup_size:
            subgroup_analysis[grp_str] = {
                "sample_count": n_grp,
                "status": "INSUFFICIENT_SAMPLE_SIZE",
                "message": f"Subgroup size (N={n_grp}) below scientific threshold ({min_subgroup_size}). Statistics withheld to prevent bias.",
                "mae": None,
                "rmse": None,
                "r2": None,
            }
            continue

        g_true = y_true[mask]
        g_pred = y_pred[mask]
        res = g_pred - g_true

        mae = float(np.mean(np.abs(res)))
        rmse = float(np.sqrt(np.mean(res ** 2)))
        bias = float(np.mean(res))

        if np.std(g_true) > 1e-6 and np.std(g_pred) > 1e-6:
            r, _ = stats.pearsonr(g_true, g_pred)
            r2 = float(r ** 2)
        else:
            r2 = 0.0

        subgroup_analysis[grp_str] = {
            "sample_count": n_grp,
            "status": "EVALUATED",
            "mae": round(mae, 3),
            "rmse": round(rmse, 3),
            "r2": round(r2, 3),
            "mean_bias": round(bias, 3),
            "age_acceleration_std": round(float(np.std(res)), 3),
        }

    return {
        "group_column": group_col,
        "evaluated_subgroups": len([g for g, d in subgroup_analysis.items() if d["status"] == "EVALUATED"]),
        "subgroups": subgroup_analysis,
    }
