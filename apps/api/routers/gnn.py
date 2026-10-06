"""
Graph Neural Networks router for BioAge-X API.
Trains GCN, GraphSAGE, and GAT models on biological interaction networks.
"""

from fastapi import APIRouter, HTTPException
from apps.api.core.config import settings
from apps.api.schemas.api_schemas import GNNTrainRequest, GNNResponseSchema
from bioage.network.interaction_graph import BiologicalInteractionGraph
from bioage.gnn.graph_dataset import BioAgeGraphDataset
from bioage.gnn.models import BioAgeGCN, BioAgeGraphSAGE, BioAgeGAT
from bioage.gnn.trainer import GraphTrainer, GraphEvaluator, GNN_SCIENTIFIC_DISCLAIMER
from bioage.utils.logger import get_logger

logger = get_logger("apps.api.routers.gnn")
router = APIRouter(prefix="/gnn", tags=["Graph Neural Networks"])


@router.post("/train", response_model=GNNResponseSchema)
def train_gnn(request: GNNTrainRequest):
    """Trains a Graph Neural Network (GCN, GraphSAGE, GAT) on the molecular network."""
    biomarkers = request.biomarkers or [
        "ELOVL2", "FHL2", "CDKN2A", "TP53", "SIRT1", "IL6", "TNF", "FOXO3",
        "MTOR", "TERT", "SOD2", "GDF15", "KLOTHO", "AKT1", "ATM", "GSTP1"
    ]

    edge_file = settings.EXAMPLE_DIR / "aging_network_edges.csv"
    edge_path = edge_file if edge_file.exists() else None

    # Construct biological graph
    bio_graph = BiologicalInteractionGraph()
    bio_graph.build_from_biomarkers(biomarkers, edge_list_path=edge_path, include_pathways=True)

    if bio_graph.graph.number_of_nodes() < 4:
        raise HTTPException(status_code=400, detail="Insufficient nodes in graph to train GNN.")

    dataset = BioAgeGraphDataset.from_interaction_graph(bio_graph)
    in_dim = dataset.x.size(1)

    arch = request.architecture
    if arch == "GCN":
        model = BioAgeGCN(in_features=in_dim, hidden_dim=32, out_features=1)
    elif arch == "GraphSAGE":
        model = BioAgeGraphSAGE(in_features=in_dim, hidden_dim=32, out_features=1)
    elif arch == "GAT":
        model = BioAgeGAT(in_features=in_dim, hidden_dim=32, out_features=1)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported architecture '{arch}'.")

    trainer = GraphTrainer(model, dataset, lr=request.lr)
    trainer.train(epochs=request.epochs)

    eval_results = GraphEvaluator.evaluate(model, dataset)

    return GNNResponseSchema(
        model_architecture=arch,
        test_mse=eval_results["test_mse"],
        test_mae=eval_results["test_mae"],
        test_r2=eval_results["test_r2"],
        top_predicted_nodes=eval_results["top_predicted_nodes"],
        disclaimer=GNN_SCIENTIFIC_DISCLAIMER,
    )


@router.get("/benchmark")
def run_gnn_benchmark(
    task: str = "regression",
    architecture: str = "GCN",
    epochs: int = 40,
    lr: float = 0.01,
):
    """
    Executes a reproducible benchmark on the 180+ node synthetic interactome.
    Explicitly labeled SYNTHETIC GRAPH BENCHMARK with task-aware metrics.
    """
    from bioage.gnn.benchmark import create_large_graph_benchmark, train_and_evaluate_benchmark

    if task not in ("regression", "classification"):
        raise HTTPException(status_code=400, detail="task must be either 'regression' or 'classification'.")
    if architecture not in ("GCN", "GraphSAGE", "GAT"):
        raise HTTPException(status_code=400, detail=f"Unsupported architecture '{architecture}'.")

    dataset = create_large_graph_benchmark(n_nodes=180, task_type=task, seed=42)
    results = train_and_evaluate_benchmark(
        dataset=dataset,
        architecture=architecture,
        epochs=epochs,
        lr=lr,
        task_type=task,
        seed=42,
    )
    return results


@router.post("/signals-graph")
def create_graph_from_phase1_signals(
    payload: dict,
):
    """
    Constructs a topological GNN dataset directly from Phase 1 candidate biomarkers
    and SHAP feature attribution weights.
    """
    from bioage.gnn.benchmark import build_gnn_from_phase1_signals

    candidates = payload.get("candidate_biomarkers", [])
    if not candidates:
        raise HTTPException(status_code=400, detail="candidate_biomarkers list required.")

    edge_file = settings.EXAMPLE_DIR / "aging_network_edges.csv"
    edge_path = str(edge_file) if edge_file.exists() else None

    dataset = build_gnn_from_phase1_signals(
        candidate_biomarkers=candidates,
        edge_list_path=edge_path,
    )
    return {
        "status": "success",
        "benchmark_label": getattr(dataset, "benchmark_type", "BIOLOGICAL PRIOR GRAPH"),
        "nodes_count": dataset.num_nodes,
        "edges_count": dataset.num_edges // 2,
        "feature_dim": dataset.x.size(1),
        "node_ids": dataset.node_ids[:20],
        "feature_names": dataset.feature_names,
    }

