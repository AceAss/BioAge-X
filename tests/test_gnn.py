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
