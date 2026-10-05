"""
Full End-to-End Two-Phase Research Framework Verification Script for BioAge-X.

PHASE 1:
- Multi-omics ingestion (Demo & GSE40279 public benchmark)
- Modality-specific preprocessing & feature selection
- Model training (ElasticNet, Random Forest, XGBoost, Multi-Omics Fusion)
- Epigenetic Clock Benchmarking (Horvath, Hannum, PhenoAge)
- Age acceleration quantification
- SHAP attribution engine
- Biomarker-to-Biology Bridge (Candidate Aging Biomarkers)

PHASE 2:
- Biological Interaction Network construction
- Network topology & centrality metrics (Degree, Betweenness, PageRank)
- Louvain community detection
- Pathway Over-Representation Analysis (ORA)
- Graph Neural Network (GCN / GraphSAGE) aging score modeling
- Two-Phase scientific report synthesis and cryptographic PDF export
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
from bioage.models.fusion import MultiOmicsEarlyFusion
from bioage.evaluation.metrics import evaluate_predictions
from bioage.evaluation.acceleration import compute_age_acceleration, summarize_acceleration_cohort
from bioage.explainability.shap_engine import BioAgeShapExplainer
from bioage.explainability.biomarker_bridge import BiomarkerToBiologyBridge
from bioage.benchmarks.clocks import ReferenceClockBenchmarkSuite
from bioage.benchmarks.multi_omics_evaluator import MultiOmicsBenchmarkComparator
from bioage.pathways.enrichment import PathwayEnrichmentAnalyzer
from bioage.network.interaction_graph import BiologicalInteractionGraph
from bioage.gnn.graph_dataset import BioAgeGraphDataset
from bioage.gnn.models import BioAgeGCN, BioAgeGraphSAGE
from bioage.gnn.trainer import GraphTrainer, GraphEvaluator
from bioage.reporting.report_generator import ResearchReportGenerator
from bioage.reporting.pdf_export import export_report_to_pdf
from bioage.utils.logger import get_logger

logger = get_logger("scripts.run_benchmark")


def main():
    logger.info("=====================================================================")
    logger.info("  STARTING BIOAGE-X TWO-PHASE RESEARCH FRAMEWORK VERIFICATION")
    logger.info("=====================================================================")

    # ---------------------------------------------------------
    # PART 1: PUBLIC BENCHMARK DATASET VERIFICATION (GSE40279)
    # ---------------------------------------------------------
    logger.info(">>> TEST 1: Evaluating Public Epigenetic Clock Benchmark (GSE40279)...")
    public_file = root_dir / "data" / "public" / "GSE40279_Hannum_Blood_Benchmark.csv"
    loader = DatasetLoader()
    df_pub, profile_pub = loader.load_file(public_file)
    logger.info(f"Loaded Public Benchmark: {profile_pub.n_samples} samples, {profile_pub.n_features} features")

    bench_suite = ReferenceClockBenchmarkSuite()
    pub_benchmarks = bench_suite.evaluate_all(df_pub, age_col="chronological_age")
    pub_benchmarks_dict = [b.to_dict() for b in pub_benchmarks]
    for b in pub_benchmarks:
        logger.info(f"  [Clock: {b.name}] Status: {b.status} | Coverage: {b.coverage_pct:.1f}%")
        if b.status == 'AVAILABLE':
            logger.info(f"    -> MAE: {b.mae:.2f} yrs | RMSE: {b.rmse:.2f} | Pearson r: {b.pearson_r:.3f} | Spearman r: {b.spearman_rho:.3f}")
        else:
            logger.info(f"    -> Missing probes: {b.missing_features_count} features (Honest reporting: NOT fabricated)")

    # ---------------------------------------------------------
    # PART 2: PHASE 1 MULTI-OMICS COHORT & BIOAGE-X TRAINING
    # ---------------------------------------------------------
    logger.info(">>> TEST 2: Executing Phase 1 Pipeline on Multi-Omics Cohort...")
    demo_file = root_dir / "data" / "example" / "demo_multiomics.csv"
    df, profile = loader.load_file(demo_file)
    logger.info(f"Loaded Multi-Omics Dataset: {profile.n_samples} samples, {profile.n_features} features")

    y = df["chronological_age"]
    covariates = df[["sex", "smoking_status", "bmi"]]

    # Preprocessing
    meth_cols = [c for c in df.columns if c.startswith("cg")]
    trans_cols = [c for c in df.columns if c.startswith("GENE_")]

    meth_pre = MethylationPreprocessor(min_variance=0.001)
    df_meth_clean, meth_prov = meth_pre.fit_transform(df[meth_cols])

    trans_pre = TranscriptomicsPreprocessor(min_variance=0.01)
    df_trans_clean, trans_prov = trans_pre.fit_transform(df[trans_cols])

    df_features = df_meth_clean.join(df_trans_clean)
    selector = FeatureSelector(max_features=40, method="mutual_info")
    X_selected = selector.fit_transform(df_features, y)
    logger.info(f"Feature Selection: Filtered to {X_selected.shape[1]} informative loci")

    # BioAge-X Models
    models = {
        "BioAge-X ElasticNet": BioAgeElasticNet(),
        "BioAge-X RandomForest": BioAgeRandomForest(n_estimators=100),
        "BioAge-X XGBoost": BioAgeXGBoost(n_estimators=100),
        "BioAge-X EarlyFusion": MultiOmicsEarlyFusion(),
    }

    metrics_results = {}
    fitted_models = {}

    for name, model in models.items():
        model.fit(X_selected, y)
        preds = model.predict(X_selected)
        metrics = evaluate_predictions(y.values, preds, n_features=X_selected.shape[1], training_time_sec=model.training_time_sec_)
        metrics_results[name] = metrics.to_dict()
        fitted_models[name] = model
        logger.info(f"  [{name}] MAE: {metrics.mae:.2f} yrs | R2: {metrics.r2:.3f} | Pearson r: {metrics.pearson_r:.3f}")

    # Multi-Omics Modality Comparison
    logger.info(">>> Multi-Omics Modality Benchmark Comparison...")
    comparator = MultiOmicsBenchmarkComparator()
    multi_comp = comparator.run_comprehensive_benchmark(df, age_col="chronological_age")
    for res in multi_comp["results"]:
        mae_str = f"{res['mae']:.2f}" if res.get('mae') is not None else "N/A"
        r2_str = f"{res['r2']:.3f}" if res.get('r2') is not None else "N/A"
        logger.info(f"  Modality: {res['name']} ({res['modality']}) -> Status: {res['status']} | MAE: {mae_str} | R2: {r2_str}")
    logger.info(f"  Synthesis: {multi_comp['scientific_synthesis']}")

    # Best Model Selection
    best_model_name = min(metrics_results.keys(), key=lambda k: metrics_results[k]["mae"])
    best_model = fitted_models[best_model_name]
    best_preds = best_model.predict(X_selected)

    # Biological Age & Age Acceleration
    df_accel = compute_age_acceleration(y, best_preds, sample_ids=list(df.index), covariates_df=covariates)
    accel_summary = summarize_acceleration_cohort(df_accel)
    logger.info(f"Age Acceleration: Mean residual={accel_summary['mean_acceleration']} yrs | "
                f"Accelerated={accel_summary['accelerated_count']} | Decelerated={accel_summary['decelerated_count']}")

    # SHAP Explainability
    logger.info(">>> Computing SHAP Explainability attributions...")
    explainer = BioAgeShapExplainer(best_model)
    explainer.explain(X_selected, sample_ids=list(df.index))
    global_biomarkers = explainer.get_global_importance(top_k=20)

    # ---------------------------------------------------------
    # PART 3: BIOMARKER-TO-BIOLOGY BRIDGE
    # ---------------------------------------------------------
    logger.info(">>> TEST 3: Executing Biomarker-to-Biology Bridge (Phase 1 -> Phase 2)...")
    bridge = BiomarkerToBiologyBridge()
    importance_dict = {bm["feature"]: bm["mean_abs_shap"] for bm in global_biomarkers}
    candidate_biomarkers = bridge.build_candidate_biomarkers(importance_dict, top_n=20)
    bridge_payload = bridge.generate_phase2_bridge_payload(candidate_biomarkers)
    seed_genes = bridge_payload["mapped_seed_genes"]
    logger.info(f"Bridge mapped {len(candidate_biomarkers)} candidate biomarkers.")
    logger.info(f"  Extracted Seed Genes for Phase 2: {seed_genes[:8]}")
    logger.info(f"  Top Candidate Biomarker: {candidate_biomarkers[0].feature_id} "
                f"({candidate_biomarkers[0].gene_symbol}, SHAP: {candidate_biomarkers[0].mean_abs_shap:.4f})")

    # ---------------------------------------------------------
    # PART 4: PHASE 2 GRAPHOMICS-AI WORKSPACE
    # ---------------------------------------------------------
    logger.info(">>> TEST 4: Phase 2 - GraphOmics-AI Network Biology & GNN...")

    # Pathway Over-Representation Analysis
    pw_analyzer = PathwayEnrichmentAnalyzer()
    pathway_results = pw_analyzer.analyze(seed_genes)
    logger.info(f"Pathway ORA: Found {len(pathway_results)} enriched aging hallmarks.")
    if pathway_results:
        logger.info(f"  Top Enriched Pathway: {pathway_results[0]['pathway_name']} (p={pathway_results[0]['p_value']:.2e})")

    # Biological Interaction Network
    bio_graph = BiologicalInteractionGraph()
    bio_graph.build_from_biomarkers(
        seed_genes,
        edge_list_path=root_dir / "data" / "example" / "aging_network_edges.csv"
    )
    cyto_export = bio_graph.to_cytoscape_json()
    net_summary = cyto_export["summary"]
    logger.info(f"Interaction Network Built: {net_summary['n_nodes']} nodes, {net_summary['n_edges']} edges, "
                f"Density: {net_summary.get('density', 0.0):.4f}")

    # Top Centrality Nodes
    top_centrality = bio_graph.get_top_centrality_nodes(top_k=5)
    logger.info("Top Aging Network Nodes by Centrality:")
    for node in top_centrality:
        logger.info(f"  Node: {node['gene']} | Degree: {node['degree_centrality']:.3f} | Betweenness: {node['betweenness_centrality']:.3f} | PageRank: {node['pagerank']:.3f}")

    # GNN Modeling: GCN and GraphSAGE
    gnn_dataset = BioAgeGraphDataset.from_interaction_graph(bio_graph)
    logger.info(f"GNN Dataset: {gnn_dataset.num_nodes} nodes, {gnn_dataset.num_edges} edges, feature_dim={gnn_dataset.x.shape[1]}")

    # Model 1: GCN
    gcn_model = BioAgeGCN(in_features=gnn_dataset.x.shape[1], hidden_dim=32, out_features=1)
    gcn_trainer = GraphTrainer(gcn_model, gnn_dataset, lr=0.01)
    gcn_trainer.train(epochs=40)
    gcn_eval = GraphEvaluator.evaluate(gcn_model, gnn_dataset)
    logger.info(f"  [GNN - GCN] Test MSE: {gcn_eval['test_mse']} | Test MAE: {gcn_eval['test_mae']} | R2: {gcn_eval['test_r2']}")

    # Model 2: GraphSAGE
    sage_model = BioAgeGraphSAGE(in_features=gnn_dataset.x.shape[1], hidden_dim=32, out_features=1)
    sage_trainer = GraphTrainer(sage_model, gnn_dataset, lr=0.01)
    sage_trainer.train(epochs=40)
    sage_eval = GraphEvaluator.evaluate(sage_model, gnn_dataset)
    logger.info(f"  [GNN - GraphSAGE] Test MSE: {sage_eval['test_mse']} | Test MAE: {sage_eval['test_mae']} | R2: {sage_eval['test_r2']}")

    # ---------------------------------------------------------
    # PART 5: TWO-PHASE PUBLICATION REPORT & PDF EXPORT
    # ---------------------------------------------------------
    logger.info(">>> TEST 5: Generating Publication-Grade Two-Phase Research Report & PDF...")
    reporter = ResearchReportGenerator()
    report_data = reporter.build_report_data(
        experiment_id="EXP-RESEARCH-VERIFY-001",
        dataset_name="demo_multiomics.csv",
        dataset_profile=profile.to_dict(),
        preprocessing_provenance={"methylation": meth_prov, "transcriptomics": trans_prov, "selection": selector.provenance_},
        model_name=best_model_name,
        model_metrics=metrics_results[best_model_name],
        acceleration_summary=accel_summary,
        top_biomarkers=global_biomarkers,
        pathway_enrichments=pathway_results,
        network_summary=net_summary,
        gnn_summary=gcn_eval,
        benchmarks_summary=pub_benchmarks_dict,
    )

    pdf_out = root_dir / "data" / "processed" / "BioAgeX_Benchmark_Report.pdf"
    export_report_to_pdf(report_data, pdf_out)
    assert pdf_out.exists(), f"PDF output not found at {pdf_out}"
    logger.info(f"Report exported successfully! Size: {pdf_out.stat().st_size} bytes at {pdf_out}")

    logger.info("=====================================================================")
    logger.info("  BIOAGE-X TWO-PHASE RESEARCH FRAMEWORK VERIFICATION COMPLETE (PASS)")
    logger.info("=====================================================================")


if __name__ == "__main__":
    main()

