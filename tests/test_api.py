"""API Integration and End-to-End Tests for BioAge-X."""

import pytest
from starlette.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"healthy", "degraded"}
    assert data["platform"] == "BioAge-X"


def test_load_demo_and_list_datasets():
    # 1. Load demo dataset
    res = client.post("/api/v1/datasets/demo/load")
    assert res.status_code == 200
    data = res.json()
    assert "DS-" in data["id"]
    assert data["n_samples"] > 0
    assert data["n_features"] > 0

    # 2. List datasets
    list_res = client.get("/api/v1/datasets")
    assert list_res.status_code == 200
    datasets = list_res.json()
    assert len(datasets) >= 1


def test_train_and_list_models():
    # Ensure demo dataset loaded
    res_ds = client.post("/api/v1/datasets/demo/load")
    ds_id = res_ds.json()["id"]

    # Train model
    res_train = client.post(
        "/api/v1/models/train",
        json={"dataset_id": ds_id, "model_type": "XGBoost", "hyperparameters": {"n_estimators": 20, "max_depth": 3}},
    )
    assert res_train.status_code == 200
    model_data = res_train.json()
    assert "MDL-" in model_data["id"]
    assert model_data["mae"] is not None
    assert model_data["r2"] is not None

    # List models
    res_list = client.get("/api/v1/models")
    assert res_list.status_code == 200
    models = res_list.json()
    assert len(models) >= 1


def test_network_build():
    res = client.post("/api/v1/network/build", json={"biomarkers": ["TP53", "CDKN2A", "SIRT1"]})
    assert res.status_code == 200
    data = res.json()
    assert len(data["elements"]["nodes"]) >= 3
    assert data["summary"]["n_nodes"] >= 3


def test_pathway_enrichment():
    res = client.post("/api/v1/pathways/enrich", json={"query_genes": ["CDKN2A", "IL6", "TP53"]})
    assert res.status_code == 200
    data = res.json()
    assert len(data["pathways"]) > 0


def test_gnn_train():
    res = client.post(
        "/api/v1/gnn/train",
        json={"architecture": "GCN", "epochs": 10, "lr": 0.01, "biomarkers": ["TP53", "CDKN2A", "SIRT1", "MTOR"]},
    )
    assert res.status_code == 200
    data = res.json()
    assert "test_mse" in data
    assert len(data["top_predicted_nodes"]) > 0


def test_integrations_endpoints():
    # 1. Health
    h_res = client.get("/api/v1/integrations/health")
    assert h_res.status_code == 200
    h_data = h_res.json()
    assert "string" in h_data
    assert "reactome" in h_data
    assert "ensembl" in h_data
    assert "ncbi" in h_data

    # 2. Genes resolve
    res_genes = client.post(
        "/api/v1/integrations/genes/resolve",
        json={"identifiers": ["cg16867657", "CDKN2A", "smoking_status"]},
    )
    assert res_genes.status_code == 200
    rg_data = res_genes.json()
    assert rg_data["total_count"] == 3
    # Check ELOVL2 mapping for cg16867657
    assert any(item["canonical_symbol"] == "ELOVL2" for item in rg_data["resolved"])

    # 3. STRING network
    str_res = client.post(
        "/api/v1/integrations/string/network",
        json={"genes": ["TP53", "CDKN1A"], "network_source": "local"},
    )
    assert str_res.status_code == 200
    assert str_res.json()["total_edges"] > 0

    # 4. Reactome pathways
    pw_res = client.post(
        "/api/v1/integrations/reactome/pathways",
        json={"genes": ["TP53", "CDKN2A"], "pathway_source": "hallmarks"},
    )
    assert pw_res.status_code == 200
    assert len(pw_res.json()["pathways"]) > 0

    # 5. GEO Search & Metadata preview
    geo_res = client.get("/api/v1/integrations/geo/search?query=GSE40279")
    assert geo_res.status_code == 200
    assert geo_res.json()["count"] > 0

    meta_res = client.get("/api/v1/integrations/geo/GSE40279")
    assert meta_res.status_code == 200
    assert meta_res.json()["sample_count"] == 656

    # 6. Cache stats
    c_res = client.get("/api/v1/integrations/cache/stats")
    assert c_res.status_code == 200
    assert "total_records" in c_res.json()

