"""
Full End-to-End Pipeline Verification Script for BioAge-X.
Runs ingestion, profiling, preprocessing, training (ElasticNet, RF, XGBoost, Fusion),
SHAP explainability, pathway enrichment, interaction graph construction, GNN training,
and PDF report generation.
"""

import sys
from pathlib import Path

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
from bioage.models.fusion import MultiOmicsEarlyFusion, MultiOmicsLateFusion
from bioage.evaluation.metrics import evaluate_predictions
from bioage.evaluation.acceleration import compute_age_acceleration, summarize_acceleration_cohort
from bioage.explainability.shap_engine import BioAgeShapExplainer
from bioage.pathways.enrichment import PathwayEnrichmentAnalyzer
from bioage.network.interaction_graph import BiologicalInteractionGraph
from bioage.gnn.graph_dataset import BioAgeGraphDataset
from bioage.gnn.models import BioAgeGCN
from bioage.gnn.trainer import GraphTrainer, GraphEvaluator
from bioage.reporting.report_generator import ResearchReportGenerator
from bioage.reporting.pdf_export import export_report_to_pdf
from bioage.utils.logger import get_logger

logger = get_logger("scripts.run_benchmark")


def main():
    logger.info("=== STARTING BIOAGE-X END-TO-END PIPELINE BENCHMARK ===")
    
    # 1. Ingestion & Profiling
    loader = DatasetLoader()
    demo_file = root_dir / "data" / "example" / "demo_multiomics.csv"
    df, profile = loader.load_file(demo_file)
    logger.info(f"Loaded: {profile.n_samples} samples, {profile.n_features} features, Age col: {profile.age_column}")

    # Extract target y and covariates
    y = df["chronological_age"]
    covariates = df[["sex", "smoking_status", "bmi"]]

    # 2. Preprocessing & Feature Selection
    # Split into methylation and transcriptomics feature spaces
    meth_cols = [c for c in df.columns if c.startswith("cg")]
    trans_cols = [c for c in df.columns if c.startswith("GENE_")]

    meth_pre = MethylationPreprocessor(min_variance=0.001)
    df_meth_clean, meth_prov = meth_pre.fit_transform(df[meth_cols])

    trans_pre = TranscriptomicsPreprocessor(min_variance=0.01)
    df_trans_clean, trans_prov = trans_pre.fit_transform(df[trans_cols])

    df_features = df_meth_clean.join(df_trans_clean)
    selector = FeatureSelector(max_features=40, method="mutual_info")
    X_selected = selector.fit_transform(df_features, y)
    logger.info(f"Selected {X_selected.shape[1]} features (top: {selector.selected_features_[:5]})")

    # 3. Model Training & Comparison
    models = {
        "ElasticNet": BioAgeElasticNet(),
        "RandomForest": BioAgeRandomForest(n_estimators=100),
        "XGBoost": BioAgeXGBoost(n_estimators=100),
        "EarlyFusion": MultiOmicsEarlyFusion(),
    }

    metrics_results = {}
    fitted_models = {}

    for name, model in models.items():
        model.fit(X_selected, y)
        preds = model.predict(X_selected)
        metrics = evaluate_predictions(y.values, preds, n_features=X_selected.shape[1], training_time_sec=model.training_time_sec_)
        metrics_results[name] = metrics.to_dict()
        fitted_models[name] = model
        logger.info(f"[{name}] MAE: {metrics.mae:.2f} yrs | R2: {metrics.r2:.3f} | Pearson r: {metrics.pearson_r:.3f}")

    # Best model selection based on MAE
    best_model_name = min(metrics_results.keys(), key=lambda k: metrics_results[k]["mae"])
    best_model = fitted_models[best_model_name]
    best_preds = best_model.predict(X_selected)

    # 4. Biological Age & Age Acceleration
    df_accel = compute_age_acceleration(y, best_preds, sample_ids=list(df.index), covariates_df=covariates)
    accel_summary = summarize_acceleration_cohort(df_accel)
    logger.info(f"Age Acceleration summary: mean={accel_summary['mean_acceleration']} yrs, "
                f"Accelerated={accel_summary['accelerated_count']}, Decelerated={accel_summary['decelerated_count']}")

    # 5. SHAP Explainability
    explainer = BioAgeShapExplainer(best_model)
    explainer.explain(X_selected, sample_ids=list(df.index))
    global_biomarkers = explainer.get_global_importance(top_k=15)
    beeswarm_sample = explainer.get_beeswarm_data(top_k=8)
    waterfall_sample = explainer.get_waterfall_explanation(sample_idx=0, top_k=6)
    logger.info(f"Top Biomarker: {global_biomarkers[0]['feature']} ({global_biomarkers[0]['mean_abs_shap']})")

    # 6. Pathway Enrichment
    query_genes = [bm["gene_symbol"] for bm in global_biomarkers]
    pw_analyzer = PathwayEnrichmentAnalyzer()
    pathway_results = pw_analyzer.analyze(query_genes)
    logger.info(f"Top Enriched Pathway: {pathway_results[0]['pathway_name']} (p={pathway_results[0]['p_value']:.2e})")

    # 7. Biological Interaction Graph
    bio_graph = BiologicalInteractionGraph()
    bio_graph.build_from_biomarkers(query_genes, edge_list_path=root_dir / "data" / "example" / "aging_network_edges.csv")
    cyto_export = bio_graph.to_cytoscape_json()
    logger.info(f"Network: {cyto_export['summary']['n_nodes']} nodes, {cyto_export['summary']['n_edges']} edges")

    # 8. GNN Training & Evaluation
    gnn_dataset = BioAgeGraphDataset.from_interaction_graph(bio_graph)
    gcn_model = BioAgeGCN(in_features=4, hidden_dim=32, out_features=1)
    trainer = GraphTrainer(gcn_model, gnn_dataset, lr=0.01)
    train_history = trainer.train(epochs=40)
    gnn_eval = GraphEvaluator.evaluate(gcn_model, gnn_dataset)
    logger.info(f"GNN Test MSE: {gnn_eval['test_mse']} | R2: {gnn_eval['test_r2']}")

    # 9. Research Report & PDF Export
    reporter = ResearchReportGenerator()
    report_data = reporter.build_report_data(
        experiment_id="EXP-BENCHMARK-001",
        dataset_name="demo_multiomics.csv",
        dataset_profile=profile.to_dict(),
        preprocessing_provenance={"methylation": meth_prov, "transcriptomics": trans_prov, "selection": selector.provenance_},
        model_name=best_model_name,
        model_metrics=metrics_results[best_model_name],
        acceleration_summary=accel_summary,
        top_biomarkers=global_biomarkers,
        pathway_enrichments=pathway_results,
        network_summary=cyto_export["summary"],
        gnn_summary=gnn_eval,
    )

    pdf_out = root_dir / "data" / "processed" / "BioAgeX_Benchmark_Report.pdf"
    export_report_to_pdf(report_data, pdf_out)
    logger.info(f"PDF report exported to: {pdf_out}")
    logger.info("=== PIPELINE BENCHMARK SUCCESSFUL ===")


if __name__ == "__main__":
    main()
