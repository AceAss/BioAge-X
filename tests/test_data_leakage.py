"""
Regression tests for data leakage prevention in BioAge-X Phase 1.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from bioage.evaluation.cross_validation import DataLeakageDetector, BioAgeCrossValidator
from bioage.preprocessing.methylation import MethylationPreprocessor
from bioage.preprocessing.feature_selection import FeatureSelector

root_dir = Path(__file__).resolve().parent.parent


def test_detect_target_in_features():
    # If chronological age is accidentally left in X
    df = pd.DataFrame({
        "chronological_age": [30.0, 50.0, 70.0],
        "cg16867657": [0.2, 0.5, 0.8],
    })
    audit = DataLeakageDetector.audit_features(df, df["chronological_age"])
    assert not audit["is_leakage_free"]
    assert any("chronological_age" in issue for issue in audit["issues"])


def test_detect_split_overlap():
    train_idx = np.array([0, 1, 2, 3, 4])
    test_idx = np.array([4, 5, 6])  # Sample 4 overlaps!
    audit = DataLeakageDetector.audit_splits(train_idx, test_idx)
    assert audit["has_split_overlap"]
    assert audit["overlapping_sample_count"] == 1
    assert 4 in audit["overlapping_indices"]


def test_preprocessing_fit_on_train_only():
    # Verify that test data cannot alter training imputation parameters
    train_df = pd.DataFrame({
        "cg16867657": [0.2, 0.4, np.nan],  # train median = 0.3
    })
    test_df = pd.DataFrame({
        "cg16867657": [0.9, np.nan, 0.95], # test values much higher
    })

    pre = MethylationPreprocessor(imputation_strategy="median", max_missing_probe_rate=0.50)
    pre.fit(train_df)
    train_imputed_val = pre.impute_values_["cg16867657"]
    assert abs(train_imputed_val - 0.3) < 1e-4

    # Transform test set uses train median, not test median
    transformed_test, _ = pre.transform(test_df)
    assert abs(transformed_test["cg16867657"].iloc[1] - 0.3) < 1e-4


def test_feature_selection_fitted_on_train_only():
    np.random.seed(42)
    n_train = 50
    n_test = 20
    
    # Train labels
    y_train = pd.Series(np.random.uniform(20, 80, n_train))
    # Synthetic feature strongly correlated with y_train
    feat_signal = y_train * 0.1 + np.random.normal(0, 0.1, n_train)
    # Synthetic noise features
    feat_noise = np.random.normal(0, 1, (n_train, 10))
    
    cols = ["sig_feature"] + [f"noise_{i}" for i in range(10)]
    X_train = pd.DataFrame(np.column_stack([feat_signal, feat_noise]), columns=cols)
    
    selector = FeatureSelector(max_features=3, method="mutual_info", random_state=42)
    selector.fit(X_train, y_train)
    assert "sig_feature" in selector.selected_features_

    # Verify transform on test data selects exactly the training features
    X_test = pd.DataFrame(np.random.normal(0, 1, (n_test, 11)), columns=cols)
    X_test_sel = selector.transform(X_test)
    assert list(X_test_sel.columns) == selector.selected_features_


def test_leakage_free_cross_validation_runs():
    demo_file = root_dir / "data" / "example" / "demo_multiomics.csv"
    if not demo_file.exists():
        pytest.skip("Demo dataset not found")

    df = pd.read_csv(demo_file)
    cv = BioAgeCrossValidator(n_splits=3, random_state=42, max_features=15)
    cv_res = cv.evaluate_model(df, model_type="ElasticNet", age_col="chronological_age")

    assert cv_res["validation_strategy"] == "3-Fold Cross-Validation (Leakage-Free)"
    assert cv_res["leak_audit"]["is_leakage_free"]
    assert cv_res["out_of_fold_metrics"]["mae"] < 8.0
    assert cv_res["out_of_fold_metrics"]["r2"] > 0.80
    assert len(cv_res["fold_summary"]["fold_test_maes"]) == 3
