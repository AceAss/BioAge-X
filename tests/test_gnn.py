"""Unit tests for Graph Neural Networks (GCN, GraphSAGE, GAT)."""

import pytest
import torch
from bioage.network.interaction_graph import BiologicalInteractionGraph
from bioage.gnn.graph_dataset import BioAgeGraphDataset
from bioage.gnn.models import BioAgeGCN, BioAgeGraphSAGE, BioAgeGAT
from bioage.gnn.trainer import GraphTrainer, GraphEvaluator


@pytest.fixture
def graph_dataset():
    biomarkers = ["TP53", "CDKN2A", "SIRT1", "FOXO3", "MTOR", "IL6"]
    graph = BiologicalInteractionGraph()
    graph.build_from_biomarkers(biomarkers, edge_list_path=None, include_pathways=True)
    return BioAgeGraphDataset.from_interaction_graph(graph)


def test_gcn_training(graph_dataset):
    model = BioAgeGCN(in_features=graph_dataset.x.size(1), hidden_dim=16, out_features=1)
    trainer = GraphTrainer(model, graph_dataset, lr=0.01)
    history = trainer.train(epochs=10)

    assert len(history["train_loss"]) == 10
    eval_res = GraphEvaluator.evaluate(model, graph_dataset)
    assert "test_mse" in eval_res
    assert len(eval_res["top_predicted_nodes"]) > 0


def test_graphsage_and_gat(graph_dataset):
    sage = BioAgeGraphSAGE(in_features=graph_dataset.x.size(1), hidden_dim=16, out_features=1)
    out_sage = sage(graph_dataset.x, graph_dataset.edge_index)
    assert out_sage.shape == (graph_dataset.x.size(0), 1)

    gat = BioAgeGAT(in_features=graph_dataset.x.size(1), hidden_dim=16, out_features=1)
    out_gat = gat(graph_dataset.x, graph_dataset.edge_index)
    assert out_gat.shape == (graph_dataset.x.size(0), 1)


def test_large_graph_benchmark_creation_and_regression():
    from bioage.gnn.benchmark import create_large_graph_benchmark, train_and_evaluate_benchmark

    ds = create_large_graph_benchmark(n_nodes=100, task_type="regression", seed=42)
    assert ds.num_nodes == 100
    assert ds.num_edges > 200
    assert ds.benchmark_type == "SYNTHETIC GRAPH BENCHMARK"
    assert ds.x.size(1) == 5

    res = train_and_evaluate_benchmark(ds, architecture="GCN", epochs=15, seed=42)
    assert res["benchmark_label"] == "SYNTHETIC GRAPH BENCHMARK"
    assert res["evaluation_metrics"]["task_type"] == "regression"
    assert "r2" in res["evaluation_metrics"]
    assert "mse" in res["evaluation_metrics"]
    assert res["graph_statistics"]["nodes"] == 100
    assert len(res["top_predicted_nodes"]) == 10


def test_large_graph_benchmark_classification():
    from bioage.gnn.benchmark import create_large_graph_benchmark, train_and_evaluate_benchmark

    ds_clf = create_large_graph_benchmark(n_nodes=80, task_type="classification", seed=123)
    assert ds_clf.task_type == "classification"

    res_clf = train_and_evaluate_benchmark(ds_clf, architecture="GraphSAGE", epochs=15, seed=123)
    assert res_clf["evaluation_metrics"]["task_type"] == "classification"
    assert "accuracy" in res_clf["evaluation_metrics"]
    assert "macro_f1" in res_clf["evaluation_metrics"]
    assert "r2" not in res_clf["evaluation_metrics"]  # Appropriate metric chosen: no R² for classification!


def test_gnn_from_phase1_signals():
    from bioage.gnn.benchmark import build_gnn_from_phase1_signals, train_and_evaluate_benchmark

    candidate_signals = [
        {"gene_symbol": "ELOVL2", "mean_abs_shap": 3.45},
        {"gene_symbol": "FHL2", "mean_abs_shap": 2.80},
        {"gene_symbol": "CDKN2A", "mean_abs_shap": 2.15},
        {"gene_symbol": "TP53", "mean_abs_shap": 1.95},
        {"gene_symbol": "SIRT1", "mean_abs_shap": 1.50},
    ]

    p1_ds = build_gnn_from_phase1_signals(candidate_signals, network_source="local")
    assert p1_ds.benchmark_type == "PHASE_1_DERIVED_INTERACTOME"
    assert p1_ds.num_nodes >= 5

    res = train_and_evaluate_benchmark(p1_ds, architecture="GAT", epochs=10)
    assert res["graph_statistics"]["nodes"] >= 5
    assert len(res["top_predicted_nodes"]) > 0
