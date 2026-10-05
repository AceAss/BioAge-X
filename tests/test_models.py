"""Unit tests for Biological Age Models in BioAge-X."""

import numpy as np
import pandas as pd
import pytest

from bioage.models.elasticnet import BioAgeElasticNet
from bioage.models.random_forest import BioAgeRandomForest
from bioage.models.xgboost_model import BioAgeXGBoost
from bioage.models.fusion import MultiOmicsEarlyFusion, MultiOmicsWeightedEnsemble
from bioage.evaluation.metrics import evaluate_predictions


@pytest.fixture
def sample_data():
    rng = np.random.default_rng(42)
    n = 60
    age = pd.Series(rng.uniform(20, 80, size=n), name="age")
    # Features with clear signal
    X = pd.DataFrame({
        "cg_elovl2": (age - 20) / 60 * 0.5 + rng.normal(0, 0.05, size=n),
        "cg_fhl2": (age - 20) / 60 * 0.4 + rng.normal(0, 0.05, size=n),
        "GENE_CDKN2A": (age - 20) / 60 * 4.0 + rng.normal(0, 0.5, size=n),
        "GENE_SIRT1": -(age - 20) / 60 * 3.0 + rng.normal(0, 0.5, size=n),
    })
    return X, age


def test_elasticnet(sample_data):
    X, y = sample_data
    model = BioAgeElasticNet()
    model.fit(X, y)
    preds = model.predict(X)

    assert len(preds) == len(y)
    metrics = evaluate_predictions(y.values, preds)
    assert metrics.r2 > 0.80
    assert metrics.mae < 10.0
    importances = model.get_feature_importance()
    assert len(importances) > 0


def test_random_forest(sample_data):
    X, y = sample_data
    model = BioAgeRandomForest(n_estimators=30, max_depth=5)
    model.fit(X, y)
    preds = model.predict(X)

    metrics = evaluate_predictions(y.values, preds)
    assert metrics.r2 > 0.80


def test_xgboost(sample_data):
    X, y = sample_data
    model = BioAgeXGBoost(n_estimators=30, max_depth=3)
    model.fit(X, y)
    preds = model.predict(X)

    metrics = evaluate_predictions(y.values, preds)
    assert metrics.r2 > 0.80


def test_early_fusion(sample_data):
    X, y = sample_data
    model = MultiOmicsEarlyFusion()
    model.fit(X, y)
    preds = model.predict(X)
    assert len(preds) == len(y)


def test_weighted_ensemble(sample_data):
    X, y = sample_data
    model = MultiOmicsWeightedEnsemble()
    model.fit(X, y)
    preds = model.predict(X)
    assert len(preds) == len(y)
