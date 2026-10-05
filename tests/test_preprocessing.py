"""Unit tests for Preprocessing and Feature Selection in BioAge-X."""

import numpy as np
import pandas as pd
import pytest

from bioage.preprocessing.methylation import MethylationPreprocessor
from bioage.preprocessing.transcriptomics import TranscriptomicsPreprocessor
from bioage.preprocessing.feature_selection import FeatureSelector


def test_methylation_preprocessor():
    df = pd.DataFrame({
        "cg1": [0.1, 0.4, np.nan, 0.8, 0.7, 0.6, 0.3, 0.9, 0.85, 0.45], # 10% missing
        "cg2": [0.5, 0.51, 0.49, 0.5, 0.5, 0.5, 0.51, 0.5, 0.49, 0.5], # low variance
        "cg3": [0.2, 0.6, 0.8, 0.9, 0.3, 0.7, 0.1, 0.85, 0.4, 0.75],
        "non_cg": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
    })

    prep = MethylationPreprocessor(min_variance=0.01, max_missing_probe_rate=0.20, filter_cg_only=True)
    clean_df, prov = prep.fit_transform(df)

    assert "cg1" in clean_df.columns
    assert "cg3" in clean_df.columns
    assert "non_cg" not in clean_df.columns
    assert clean_df.isna().sum().sum() == 0
    assert prov["modality"] == "methylation"


def test_transcriptomics_preprocessor():
    df = pd.DataFrame({
        "CDKN2A": [10.0, 500.0, 20.0, 800.0],
        "SIRT1": [50.0, 10.0, 40.0, 5.0],
        "UNEXPRESSED": [0.0, 0.0, 0.0, 0.0],
    })

    prep = TranscriptomicsPreprocessor(min_variance=0.001, min_samples_expressed=0.5)
    clean_df, prov = prep.fit_transform(df)

    assert "CDKN2A" in clean_df.columns
    assert "SIRT1" in clean_df.columns
    assert "UNEXPRESSED" not in clean_df.columns
    assert prov["log1p_transformed"] is True


def test_feature_selector():
    rng = np.random.default_rng(42)
    y = pd.Series(rng.uniform(20, 80, size=50))
    X = pd.DataFrame({
        "feat_signal1": y * 0.8 + rng.normal(0, 2, size=50),
        "feat_signal2": y * -0.6 + rng.normal(0, 3, size=50),
        "feat_noise1": rng.normal(0, 1, size=50),
        "feat_noise2": rng.normal(0, 1, size=50),
    })

    selector = FeatureSelector(max_features=2, method="mutual_info")
    X_sel = selector.fit_transform(X, y)

    assert X_sel.shape[1] == 2
    assert "feat_signal1" in X_sel.columns
