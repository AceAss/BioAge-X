"""Unit tests for Evaluation Metrics and Age Acceleration."""

import numpy as np
import pandas as pd
import pytest

from bioage.evaluation.metrics import evaluate_predictions
from bioage.evaluation.acceleration import compute_age_acceleration, summarize_acceleration_cohort


def test_metrics_calculation():
    y_true = np.array([30.0, 40.0, 50.0, 60.0, 70.0])
    y_pred = np.array([31.0, 39.0, 52.0, 58.0, 71.0])

    metrics = evaluate_predictions(y_true, y_pred, n_features=10, training_time_sec=1.5)
    assert metrics.mae == 1.4
    assert metrics.r2 > 0.95
    assert metrics.pearson_r > 0.95
    assert metrics.spearman_rho > 0.95
    assert metrics.n_features == 10


def test_age_acceleration_computation():
    c_age = pd.Series([30.0, 40.0, 50.0])
    b_age = pd.Series([35.0, 38.0, 50.0])

    df_accel = compute_age_acceleration(c_age, b_age)
    assert list(df_accel["age_acceleration"]) == [5.0, -2.0, 0.0]
    assert list(df_accel["acceleration_status"]) == ["Accelerated", "Decelerated", "Synchronous"]

    summary = summarize_acceleration_cohort(df_accel)
    assert summary["accelerated_count"] == 1
    assert summary["decelerated_count"] == 1
    assert summary["synchronous_count"] == 1
    assert "disclaimer" in summary
