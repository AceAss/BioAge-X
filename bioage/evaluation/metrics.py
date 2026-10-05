"""
Model Evaluation Metrics for BioAge-X.
Computes MAE, RMSE, R2, Pearson correlation, Spearman correlation,
feature counts, and training durations for rigorous benchmark comparisons.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Tuple
import numpy as np
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from bioage.utils.logger import get_logger

logger = get_logger("bioage.evaluation.metrics")


@dataclass
class ModelMetrics:
    """Standardized metrics container for biological age models."""
    mae: float
    rmse: float
    r2: float
    pearson_r: float
    pearson_pvalue: float
    spearman_rho: float
    spearman_pvalue: float
    n_features: int
    training_time_sec: float
    sample_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def evaluate_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_features: int = 0,
    training_time_sec: float = 0.0,
) -> ModelMetrics:
    """Calculates comprehensive benchmark metrics between chronological age and predicted age."""
    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)

    # Check for NaN / length match
    valid_mask = (~np.isnan(y_true_arr)) & (~np.isnan(y_pred_arr))
    y_t = y_true_arr[valid_mask]
    y_p = y_pred_arr[valid_mask]

    n_samples = len(y_t)
    if n_samples < 2:
        raise ValueError(f"Insufficient valid samples ({n_samples}) for metric computation.")

    mae = float(mean_absolute_error(y_t, y_p))
    rmse = float(np.sqrt(mean_squared_error(y_t, y_p)))
    r2 = float(r2_score(y_t, y_p))

    # Pearson correlation
    pearson_res = stats.pearsonr(y_t, y_p)
    pearson_r = float(pearson_res.statistic)
    pearson_p = float(pearson_res.pvalue)

    # Spearman rank correlation
    spearman_res = stats.spearmanr(y_t, y_p)
    spearman_rho = float(spearman_res.statistic)
    spearman_p = float(spearman_res.pvalue)

    metrics = ModelMetrics(
        mae=round(mae, 3),
        rmse=round(rmse, 3),
        r2=round(r2, 4),
        pearson_r=round(pearson_r, 4),
        pearson_pvalue=round(pearson_p, 6),
        spearman_rho=round(spearman_rho, 4),
        spearman_pvalue=round(spearman_p, 6),
        n_features=n_features,
        training_time_sec=round(training_time_sec, 3),
        sample_count=n_samples,
    )

    logger.info(
        f"Evaluation: MAE={metrics.mae:.2f} yrs, RMSE={metrics.rmse:.2f} yrs, "
        f"R2={metrics.r2:.3f}, Pearson_r={metrics.pearson_r:.3f}"
    )
    return metrics
