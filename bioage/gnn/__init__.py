"""Graph Neural Networks module for BioAge-X."""
from bioage.gnn.graph_dataset import BioAgeGraphDataset
from bioage.gnn.models import BioAgeGCN, BioAgeGraphSAGE, BioAgeGAT
from bioage.gnn.trainer import GraphTrainer, GraphEvaluator, GNN_SCIENTIFIC_DISCLAIMER
from bioage.gnn.benchmark import (
    create_large_graph_benchmark,
    build_gnn_from_phase1_signals,
    train_and_evaluate_benchmark,
    BENCHMARK_DISCLAIMER,
)

__all__ = [
    "BioAgeGraphDataset",
    "BioAgeGCN",
    "BioAgeGraphSAGE",
    "BioAgeGAT",
    "GraphTrainer",
    "GraphEvaluator",
    "GNN_SCIENTIFIC_DISCLAIMER",
    "create_large_graph_benchmark",
    "build_gnn_from_phase1_signals",
    "train_and_evaluate_benchmark",
    "BENCHMARK_DISCLAIMER",
]
