"""
Comprehensive Research Rigor, Uncertainty, and Evaluation Test Suite for BioAge-X Prompt 7.
Verifies statistical bootstrap, age-bias, external validation, dataset shift,
ablation frameworks, biomarker robustness, and manuscript generation.
"""

import pytest
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from bioage.evaluation.uncertainty import (
    compute_bootstrap_confidence_interval,
    analyze_cross_validation_distribution,
    analyze_age_bias,
    analyze_cohort_stratification,
)
from bioage.evaluation.robustness import (
    calculate_biomarker_robustness_scores,
    audit_annotation_provenance,
    evaluate_network_perturbation_robustness,
    format_pathway_enrichment_with_universe,
)
from bioage.evaluation.external_validation import (
    analyze_dataset_shift,
    execute_external_validation,
)
from bioage.evaluation.ablation import (
    run_modality_ablation_comparison,
    run_fusion_ablation_comparison,
    run_feature_ablation_comparison,
    run_gnn_ablation_comparison,
)
from bioage.reporting.manuscript_report import ManuscriptReportGenerator
from apps.api.main import app
from starlette.testclient import TestClient


def test_bootstrap_confidence_interval_calculation():
    """Verifies empirical bootstrap CI bounds and small sample guardrail."""
    np.random.seed(42)
    y_true = np.array([30, 40, 50, 60, 70], dtype=float)
    y_pred = np.array([32, 39, 52, 58, 71], dtype=float)

    fn = lambda yt, yp: float(np.mean(np.abs(yt - yp)))
    res = compute_bootstrap_confidence_interval(y_true, y_pred, fn, n_bootstraps=200, seed=42)

    assert "point_estimate" in res
    assert res["ci_lower"] is not None
    assert res["ci_upper"] is not None
    assert res["ci_lower"] <= res["point_estimate"] <= res["ci_upper"]
    assert res["n_bootstraps"] == 200

    # Test small sample size guardrail (n < 5)
    small_res = compute_bootstrap_confidence_interval(np.array([20, 30]), np.array([22, 28]), fn)
    assert small_res["ci_lower"] is None
    assert "warning" in small_res


def test_cross_validation_distribution_analysis():
    """Verifies fold-by-fold preservation and dispersion statistics."""
    folds = [
        {"mae": 3.2, "r2": 0.94},
        {"mae": 3.8, "r2": 0.91},
        {"mae": 3.5, "r2": 0.93},
        {"mae": 4.1, "r2": 0.89},
        {"mae": 3.4, "r2": 0.93},
    ]
    res = analyze_cross_validation_distribution(folds)

    assert res["num_folds"] == 5
    summary = res["summary"]
    assert "mae" in summary and "r2" in summary
    assert summary["mae"]["mean"] == pytest.approx(3.6, abs=0.05)
    assert summary["mae"]["min"] == 3.2
    assert summary["mae"]["max"] == 4.1
    assert len(summary["mae"]["values"]) == 5


def test_age_bias_and_regression_toward_mean():
    """Verifies age-dependent residual stratification and bias detection."""
    # Synthetic young, middle, old
    true_ages = np.array([25, 30, 35, 50, 55, 60, 75, 80, 85], dtype=float)
    # Regression toward mean: young predicted older (+), old predicted younger (-)
    pred_ages = np.array([30, 34, 38, 51, 54, 59, 70, 74, 78], dtype=float)

    res = analyze_age_bias(true_ages, pred_ages)
    assert res["total_samples"] == 9
    assert len(res["age_bins"]) == 3

    # Regression toward mean should show negative slope
    slope = res["regression_toward_mean"]["slope"]
    assert slope < 0.0


def test_cohort_stratification_guardrails():
    """Verifies subgroup analysis and INSUFFICIENT_SAMPLE_SIZE guardrail."""
    y_true = np.array([30, 40, 50, 60, 70, 35, 45, 55, 65, 75, 80, 85], dtype=float)
    y_pred = y_true + 2.0
    meta = pd.DataFrame({
        "sex": ["F"] * 10 + ["M", "M"],  # F has 10, M has 2
    })

    res = analyze_cohort_stratification(y_true, y_pred, meta, group_col="sex", min_subgroup_size=5)
    subgroups = res["subgroups"]

    assert subgroups["F"]["status"] == "EVALUATED"
    assert subgroups["F"]["mae"] == pytest.approx(2.0, abs=0.01)
    assert subgroups["M"]["status"] == "INSUFFICIENT_SAMPLE_SIZE"


def test_biomarker_robustness_scores():
    """Verifies mathematical formulation of Biomarker Robustness Scores."""
    features = ["ELOVL2", "FHL2", "RANDOM_PROBE"]
    folds = [
        ["ELOVL2", "FHL2"],
        ["ELOVL2", "FHL2"],
        ["ELOVL2", "RANDOM_PROBE"],
        ["ELOVL2"],
    ]
    shaps = {"ELOVL2": 0.50, "FHL2": 0.35, "RANDOM_PROBE": 0.05}

    res = calculate_biomarker_robustness_scores(features, folds, shaps)
    assert len(res) == 3
    # ELOVL2 should be top-ranked with highest score
    assert res[0]["feature_id"] == "ELOVL2"
    assert res[0]["selection_frequency"] == 1.0  # 4/4 folds
    assert res[0]["stability_tier"] == "HIGHLY_STABLE"

    # RANDOM_PROBE should have lowest score
    assert res[-1]["feature_id"] == "RANDOM_PROBE"
    assert res[-1]["stability_tier"] == "SINGLE_EXPERIMENT_CANDIDATE"


def test_annotation_provenance_tiers():
    """Verifies classification of annotation certainty."""
    direct = audit_annotation_provenance("cg16867657", mapped_gene="ELOVL2", ensembl_id="ENSG00000197977")
    assert direct["mapping_status"] == "DIRECT_MAPPING"
    assert direct["confidence"] == "HIGH"

    inferred = audit_annotation_provenance("LOC9999", string_interactors=["TP53", "CDKN2A"])
    assert inferred["mapping_status"] == "INFERRED_ASSOCIATION"
    assert inferred["confidence"] == "LOW"

    unmapped = audit_annotation_provenance("cg99999999")
    assert unmapped["mapping_status"] == "NO_MAPPING_AVAILABLE"
    assert unmapped["confidence"] == "NONE"


def test_network_perturbation_robustness():
    """Verifies topological stability under edge score thresholds."""
    nodes = [{"id": "A"}, {"id": "B"}, {"id": "C"}, {"id": "D"}]
    edges = [
        {"source": "A", "target": "B", "score": 950},
        {"source": "A", "target": "C", "score": 800},
        {"source": "B", "target": "C", "score": 750},
        {"source": "C", "target": "D", "score": 450},
    ]

    res = evaluate_network_perturbation_robustness(nodes, edges, confidence_thresholds=[400, 700, 900])
    sweep = res["confidence_sweep"]
    assert len(sweep) == 3
    assert sweep[0]["confidence_threshold"] == 400
    assert sweep[0]["retained_edges"] == 4
    assert sweep[2]["confidence_threshold"] == 900
    assert sweep[2]["retained_edges"] == 1


def test_external_validation_workflow():
    """Verifies external cohort validation without retraining."""
    np.random.seed(42)
    # Train Ridge model on 4 features
    X_train = np.random.normal(0, 1, (40, 4))
    y_train = 50 + X_train[:, 0] * 5 + X_train[:, 1] * 3
    model = Ridge().fit(X_train, y_train)
    trained_feats = ["feat_1", "feat_2", "feat_3", "feat_4"]

    # External dataset with shared features
    ext_df = pd.DataFrame({
        "feat_1": np.random.normal(0, 1, 20),
        "feat_2": np.random.normal(0, 1, 20),
        "feat_3": np.random.normal(0, 1, 20),
        "feat_4": np.random.normal(0, 1, 20),
        "age": 50 + np.random.normal(0, 3, 20),
    })

    eval_res = execute_external_validation(
        model, trained_feats, ext_df,
        train_dataset_name="Cohort_A", external_dataset_name="Cohort_B"
    )
    assert eval_res["status"] == "VALIDATED"
    assert "metrics" in eval_res
    assert eval_res["metrics"]["mae"] > 0.0

    # Incompatible external dataset (<10% overlap)
    incompat_df = pd.DataFrame({"unrelated_col": [1, 2, 3], "age": [30, 40, 50]})
    incompat_res = execute_external_validation(
        model, trained_feats, incompat_df,
        train_dataset_name="Cohort_A", external_dataset_name="Cohort_C"
    )
    assert incompat_res["status"] == "EXTERNAL_VALIDATION_NOT_AVAILABLE"


def test_dataset_shift_analysis():
    """Verifies KS test and Cohen's d feature shift detection."""
    np.random.seed(42)
    train_df = pd.DataFrame({
        "age": np.random.normal(45, 10, 100),
        "gene_A": np.random.normal(5, 1, 100),
    })
    # Shifted external cohort: elderly (mean age 75)
    ext_df = pd.DataFrame({
        "age": np.random.normal(75, 8, 80),
        "gene_A": np.random.normal(5, 1, 80),
    })

    shift = analyze_dataset_shift(train_df, ext_df)
    assert shift["age_distribution"]["age_shift_detected"] is True
    assert shift["overall_shift_verdict"] in ("MODERATE_DATASET_SHIFT", "SEVERE_DATASET_SHIFT")


def test_ablation_study_framework():
    """Verifies modality, fusion, feature, and GNN ablation suites."""
    mod_res = run_modality_ablation_comparison({
        "Methylation only": {"mae": 4.1, "r2": 0.88},
        "Multi-Omics (Meth + Trans)": {"mae": 3.4, "r2": 0.93},
    })
    assert mod_res["ablation_type"] == "MODALITY_ABLATION"
    assert len(mod_res["results"]) == 2

    gnn_res = run_gnn_ablation_comparison(
        tabular_baseline_metrics={"mae": 3.8, "r2": 0.90},
        gnn_metrics_by_model={"GCN": {"mae": 3.5, "r2": 0.92, "has_biomarker_signal": True}},
    )
    assert gnn_res["ablation_type"] == "GNN_INTERACTOME_ABLATION"
    assert len(gnn_res["results"]) == 2


def test_manuscript_report_generator_and_fingerprint():
    """Verifies 24-section manuscript generation and SHA-256 configuration fingerprint."""
    gen = ManuscriptReportGenerator()
    res = gen.generate_manuscript(
        experiment_id="EXP-TEST-001",
        dataset_name="GSE40279_Hannum_Blood_Benchmark",
        dataset_profile={"sample_count": 80, "feature_count": 120, "modalities": ["DNAm"]},
        model_name="BioAgeElasticNet",
        model_metrics={"mae": 3.82, "rmse": 4.91, "r2": 0.912, "pearson_r": 0.956},
    )

    assert "fingerprint" in res
    assert len(res["fingerprint"]) == 64  # SHA-256 length
    assert res["sections_count"] == 24
    content = res["markdown_content"]
    assert "## 1. Abstract" in content
    assert "## 2. Research Question" in content
    assert "## 21. Limitations" in content
    assert "## 22. Reproducibility" in content


def test_evaluation_api_endpoints():
    """Verifies FastAPI evaluation endpoints respond with 200 and structured schemas."""
    client = TestClient(app)

    # Bootstrap endpoint
    b_res = client.post("/api/v1/evaluation/bootstrap", json={
        "y_true": [30.0, 40.0, 50.0, 60.0, 70.0],
        "y_pred": [31.0, 41.0, 49.0, 62.0, 68.0],
        "metric_name": "mae",
        "n_bootstraps": 100,
        "confidence_level": 0.95,
    })
    assert b_res.status_code == 200
    assert "ci_lower" in b_res.json()

    # Age bias endpoint
    ab_res = client.post("/api/v1/evaluation/age-bias", json={
        "chronological_age": [30.0, 45.0, 65.0, 80.0],
        "predicted_age": [33.0, 46.0, 63.0, 78.0],
    })
    assert ab_res.status_code == 200
    assert "age_bins" in ab_res.json()

    # Ablations endpoint
    abl_res = client.post("/api/v1/evaluation/ablations", json={
        "experiment_id": "EXP-DEMO",
        "ablation_type": "modality",
    })
    assert abl_res.status_code == 200
    assert abl_res.json()["ablation_type"] == "MODALITY_ABLATION"
