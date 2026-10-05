"""
Tests for SHAP Efficiency and Consistency Axiom in BioAge-X.
Verifies that:
sum(SHAP values) + base_value == model_prediction
for every individual sample across linear and tree models.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from bioage.models.elasticnet import BioAgeElasticNet
from bioage.models.random_forest import BioAgeRandomForest
from bioage.explainability.shap_engine import BioAgeShapExplainer

root_dir = Path(__file__).resolve().parent.parent


def test_elasticnet_shap_efficiency():
    demo_file = root_dir / "data" / "example" / "demo_multiomics.csv"
    if not demo_file.exists():
        pytest.skip("Demo dataset not found")

    df = pd.read_csv(demo_file)
    y = df["chronological_age"]
    cpg_cols = [c for c in df.columns if c.startswith("cg")][:10]
    X = df[cpg_cols].fillna(df[cpg_cols].median())

    model = BioAgeElasticNet()
    model.fit(X, y)
    preds = model.predict(X)

    explainer = BioAgeShapExplainer(model)
    explainer.explain(X, sample_ids=list(df["sample_id"]))

    assert explainer.shap_values_ is not None
    assert explainer.shap_values_.shape == X.shape

    # Test efficiency axiom across all samples: sum(phi_i) + base_value == pred_i
    shap_sums = np.sum(explainer.shap_values_, axis=1) + explainer.base_value_
    max_discrepancy = np.max(np.abs(shap_sums - preds))
    assert max_discrepancy < 1e-4, f"ElasticNet SHAP efficiency violated! Max diff: {max_discrepancy}"


def test_random_forest_shap_efficiency():
    demo_file = root_dir / "data" / "example" / "demo_multiomics.csv"
    if not demo_file.exists():
        pytest.skip("Demo dataset not found")

    df = pd.read_csv(demo_file)
    y = df["chronological_age"]
    cpg_cols = [c for c in df.columns if c.startswith("cg")][:10]
    X = df[cpg_cols].fillna(df[cpg_cols].median())

    model = BioAgeRandomForest(n_estimators=30, random_state=42)
    model.fit(X, y)
    preds = model.predict(X)

    explainer = BioAgeShapExplainer(model)
    explainer.explain(X, sample_ids=list(df["sample_id"]))

    assert explainer.shap_values_ is not None
    # Test efficiency axiom: sum(phi_i) + base_value == pred_i
    shap_sums = np.sum(explainer.shap_values_, axis=1) + explainer.base_value_
    max_discrepancy = np.max(np.abs(shap_sums - preds))
    assert max_discrepancy < 1e-3, f"RandomForest SHAP efficiency violated! Max diff: {max_discrepancy}"


def test_shap_feature_and_sample_alignment():
    demo_file = root_dir / "data" / "example" / "demo_multiomics.csv"
    if not demo_file.exists():
        pytest.skip("Demo dataset not found")

    df = pd.read_csv(demo_file)
    y = df["chronological_age"]
    features = ["cg16867657_ELOVL2", "cg06639320_FHL2", "GENE_CDKN2A", "GENE_SIRT1"]
    avail = [f for f in features if f in df.columns]
    X = df[avail].fillna(df[avail].median())
    sample_ids = [f"SUBJECT_{i}" for i in range(len(df))]

    model = BioAgeElasticNet()
    model.fit(X, y)

    explainer = BioAgeShapExplainer(model)
    explainer.explain(X, sample_ids=sample_ids)

    assert explainer.sample_ids_ == sample_ids
    assert explainer.feature_names == avail
    global_imp = explainer.get_global_importance(top_k=len(avail))
    assert len(global_imp) == len(avail)
    assert all("mean_abs_shap" in item for item in global_imp)
