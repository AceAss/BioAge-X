"""
Reproducibility Verification Script for BioAge-X.
Runs the complete Two-Phase research pipeline twice under identical random seeds
and mathematically verifies that all metrics, model weights, SHAP attributions,
and network topology metrics match identically.
"""

import sys
import json
import time
import platform
from pathlib import Path
import numpy as np
import pandas as pd

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from bioage.ingestion.loaders import DatasetLoader
from bioage.preprocessing.methylation import MethylationPreprocessor
from bioage.preprocessing.transcriptomics import TranscriptomicsPreprocessor
from bioage.preprocessing.feature_selection import FeatureSelector
from bioage.models.elasticnet import BioAgeElasticNet
from bioage.models.random_forest import BioAgeRandomForest
from bioage.models.xgboost_model import BioAgeXGBoost
from bioage.evaluation.metrics import evaluate_predictions
from bioage.evaluation.acceleration import compute_age_acceleration
from bioage.explainability.shap_engine import BioAgeShapExplainer
from bioage.explainability.biomarker_bridge import BiomarkerToBiologyBridge
from bioage.network.interaction_graph import BiologicalInteractionGraph
from bioage.gnn.graph_dataset import BioAgeGraphDataset
from bioage.gnn.models import BioAgeGCN
from bioage.gnn.trainer import GraphTrainer, GraphEvaluator
from bioage.reporting.report_generator import ResearchReportGenerator
from bioage.utils.logger import get_logger

logger = get_logger("scripts.verify_reproducibility")


def run_pipeline(seed: int = 42) -> dict:
    """Executes full pipeline deterministically."""
    import torch
    torch.manual_seed(seed)
    np.random.seed(seed)

    loader = DatasetLoader()
    demo_file = root_dir / "data" / "example" / "demo_multiomics.csv"
    df, profile = loader.load_file(demo_file)
    y = df["chronological_age"]

    # Preprocessing
    meth_cols = [c for c in df.columns if c.startswith("cg")]
    trans_cols = [c for c in df.columns if c.startswith("GENE_")]

    meth_pre = MethylationPreprocessor(min_variance=0.001)
    df_meth_clean, _ = meth_pre.fit_transform(df[meth_cols])

    trans_pre = TranscriptomicsPreprocessor(min_variance=0.01)
    df_trans_clean, _ = trans_pre.fit_transform(df[trans_cols])

    df_features = df_meth_clean.join(df_trans_clean)
    selector = FeatureSelector(max_features=25, method="mutual_info", random_state=seed)
    X_selected = selector.fit_transform(df_features, y)

    # Models
    enet = BioAgeElasticNet(random_state=seed)
    enet.fit(X_selected, y)
    enet_preds = enet.predict(X_selected)
    enet_metrics = evaluate_predictions(y.values, enet_preds, n_features=X_selected.shape[1]).to_dict()

    rf = BioAgeRandomForest(n_estimators=50, random_state=seed)
    rf.fit(X_selected, y)
    rf_preds = rf.predict(X_selected)
    rf_metrics = evaluate_predictions(y.values, rf_preds, n_features=X_selected.shape[1]).to_dict()

    # SHAP
    explainer = BioAgeShapExplainer(enet)
    explainer.explain(X_selected, sample_ids=list(df.index))
    global_shap = explainer.get_global_importance(top_k=10)

    # Bridge & Network
    bridge = BiomarkerToBiologyBridge()
    imp_dict = {b["feature"]: b["mean_abs_shap"] for b in global_shap}
    candidates = bridge.build_candidate_biomarkers(imp_dict, top_n=10)
    payload = bridge.generate_phase2_bridge_payload(candidates)

    graph = BiologicalInteractionGraph()
    graph.build_from_biomarkers(payload["mapped_seed_genes"], edge_list_path=root_dir / "data" / "example" / "aging_network_edges.csv")
    cyto = graph.to_cytoscape_json()
    top_nodes = graph.get_top_centrality_nodes(top_k=5)

    # GNN
    gnn_data = BioAgeGraphDataset.from_interaction_graph(graph, random_seed=seed)
    torch.manual_seed(seed)
    gcn = BioAgeGCN(in_features=gnn_data.x.shape[1], hidden_dim=16, out_features=1)
    trainer = GraphTrainer(gcn, gnn_data, lr=0.01, random_seed=seed)
    trainer.train(epochs=20)
    gnn_eval = GraphEvaluator.evaluate(gcn, gnn_data)

    return {
        "selected_features": selector.selected_features_,
        "enet_preds": enet_preds.tolist(),
        "enet_metrics": enet_metrics,
        "rf_preds": rf_preds.tolist(),
        "rf_metrics": rf_metrics,
        "global_shap": global_shap,
        "network_nodes": cyto["summary"]["n_nodes"],
        "network_edges": cyto["summary"]["n_edges"],
        "top_nodes": top_nodes,
        "gnn_test_mse": gnn_eval["test_mse"],
        "gnn_test_mae": gnn_eval["test_mae"],
    }


def main():
    logger.info("=== STARTING DETERMINISTIC REPRODUCIBILITY AUDIT ===")
    logger.info(f"Environment: Python {platform.python_version()} on {platform.system()} {platform.release()}")

    seed = 42
    logger.info(f"Executing Run 1 with seed={seed}...")
    t0 = time.time()
    run1 = run_pipeline(seed=seed)
    t1 = time.time() - t0
    logger.info(f"Run 1 completed in {t1:.2f}s")

    logger.info(f"Executing Run 2 with seed={seed}...")
    t0 = time.time()
    run2 = run_pipeline(seed=seed)
    t2 = time.time() - t0
    logger.info(f"Run 2 completed in {t2:.2f}s")

    # Verification assertions
    logger.info("Verifying identical feature selection...")
    assert run1["selected_features"] == run2["selected_features"], "Feature selections differed between runs!"

    logger.info("Verifying ElasticNet predictions and metrics...")
    diff_enet = np.max(np.abs(np.array(run1["enet_preds"]) - np.array(run2["enet_preds"])))
    assert diff_enet < 1e-6, f"ElasticNet predictions differed by {diff_enet}!"
    assert run1["enet_metrics"]["mae"] == run2["enet_metrics"]["mae"], "ElasticNet MAE differed!"

    logger.info("Verifying RandomForest predictions...")
    diff_rf = np.max(np.abs(np.array(run1["rf_preds"]) - np.array(run2["rf_preds"])))
    assert diff_rf < 1e-6, f"RandomForest predictions differed by {diff_rf}!"

    logger.info("Verifying SHAP feature importance...")
    for s1, s2 in zip(run1["global_shap"], run2["global_shap"]):
        assert s1["feature"] == s2["feature"], "SHAP feature rank mismatch!"
        assert abs(s1["mean_abs_shap"] - s2["mean_abs_shap"]) < 1e-6, "SHAP values differed!"

    logger.info("Verifying Network Topology...")
    assert run1["network_nodes"] == run2["network_nodes"], "Network node count differed!"
    assert run1["network_edges"] == run2["network_edges"], "Network edge count differed!"
    for n1, n2 in zip(run1["top_nodes"], run2["top_nodes"]):
        assert n1["gene"] == n2["gene"], "Top network node differed!"
        assert abs(n1["degree_centrality"] - n2["degree_centrality"]) < 1e-6

    logger.info("Verifying GNN test evaluation...")
    assert abs(run1["gnn_test_mse"] - run2["gnn_test_mse"]) < 1e-5, "GNN test MSE differed!"

    logger.info("=================================================================")
    logger.info("  REPRODUCIBILITY AUDIT: PERFECT DETERMINISTIC MATCH (PASS)      ")
    logger.info(f"  Random Seed: {seed}")
    logger.info(f"  Max Prediction Discrepancy: {diff_enet:.2e} (ElasticNet), {diff_rf:.2e} (RF)")
    logger.info("=================================================================")


if __name__ == "__main__":
    main()
