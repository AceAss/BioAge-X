"""
Unit and integration tests for Epigenetic Clock Benchmarking and Biomarker-to-Biology Bridge.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from bioage.benchmarks.clocks import HorvathClock, HannumClock, PhenoAgeClock, ReferenceClockBenchmarkSuite
from bioage.benchmarks.multi_omics_evaluator import MultiOmicsBenchmarkComparator
from bioage.explainability.biomarker_bridge import BiomarkerToBiologyBridge
from starlette.testclient import TestClient
from apps.api.main import app

root_dir = Path(__file__).resolve().parent.parent


def test_horvath_anti_log_transform():
    clock = HorvathClock()
    # Test developmental age (<20) and adult age (>20) transformations
    for age in [5.0, 15.0, 20.0, 35.0, 65.0, 80.0]:
        f_val = clock.horvath_trafo(age)
        f_inv = float(clock.horvath_anti_trafo(np.array([f_val]))[0])
        assert abs(age - f_inv) < 1e-4, f"Horvath f/f_inv mismatch for age {age}"


def test_hannum_benchmark_evaluation():
    pub_file = root_dir / "data" / "public" / "GSE40279_Hannum_Blood_Benchmark.csv"
    if not pub_file.exists():
        pytest.skip("Public benchmark file not found")

    df = pd.read_csv(pub_file)
    hannum = HannumClock()
    cov = hannum.inspect_coverage(df)
    assert cov["status"] == "AVAILABLE"
    assert cov["coverage_pct"] >= 95.0

    res = hannum.evaluate_on_dataset(df, age_col="chronological_age")
    assert res.status == "AVAILABLE"
    assert res.mae is not None and res.mae < 15.0
    assert res.pearson_r is not None and res.pearson_r > 0.90


def test_honest_missing_probe_reporting():
    # Synthetic small dataframe missing almost all Horvath probes
    df_sparse = pd.DataFrame({
        "chronological_age": [30, 45, 60],
        "cg16867657": [0.3, 0.5, 0.7],
        "cg06639320": [0.2, 0.4, 0.6],
    })

    suite = ReferenceClockBenchmarkSuite()
    results = suite.evaluate_all(df_sparse, age_col="chronological_age")
    
    for r in results:
        # Should not falsely claim full availability or fabricate missing probes
        if r.name.startswith("Horvath"):
            assert r.status in ["PARTIAL_COVERAGE", "UNAVAILABLE"]
            assert r.missing_features_count > 300
            assert len(r.missing_features_sample) > 0


def test_biomarker_to_biology_bridge():
    bridge = BiomarkerToBiologyBridge()
    features = {
        "cg16867657_ELOVL2": 4.5,
        "cg06639320_FHL2": 3.8,
        "CDKN2A": 3.2,
        "SIRT1": 2.5,
    }
    candidates = bridge.build_candidate_biomarkers(features, top_n=4)
    assert len(candidates) == 4
    assert candidates[0].gene_symbol == "ELOVL2"
    assert candidates[1].gene_symbol == "FHL2"
    assert candidates[2].gene_symbol == "CDKN2A"

    payload = bridge.generate_phase2_bridge_payload(candidates)
    assert "ELOVL2" in payload["mapped_seed_genes"]
    assert "CDKN2A" in payload["mapped_seed_genes"]
    assert payload["bridge_status"] == "READY_FOR_NETWORK_CONSTRUCTION"


def test_api_benchmark_endpoints():
    client = TestClient(app)
    
    # List supported clocks
    res = client.get("/api/v1/benchmarks/clocks")
    assert res.status_code == 200
    data = res.json()
    clocks = data["reference_clocks"]
    assert len(clocks) >= 3
    clock_names = [c["name"] for c in clocks]
    assert any("Horvath" in n for n in clock_names)
    assert any("Hannum" in n for n in clock_names)

    # Public datasets listing
    pub_res = client.get("/api/v1/datasets/public")
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert len(pub_data) >= 1
    assert pub_data[0]["key"] == "gse40279_hannum"
