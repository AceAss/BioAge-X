# BioAge-X Architecture Specification

BioAge-X is organized as a modular computational biology and machine-learning monorepo separating data ingestion, preprocessing, modeling, evaluation, network biology, graph neural networks, reporting, API services, and the web user interface.

## Monorepo Layout

```
BioAge-X/
├── apps/
│   ├── api/             # FastAPI REST service, SQLAlchemy ORM, job execution
│   └── frontend/        # Next.js 14, Tailwind CSS, Cytoscape.js, interactive visualizers
├── bioage/
│   ├── ingestion/       # Format loaders (CSV, TSV, Parquet, H5AD), DatasetProfiler
│   ├── preprocessing/   # Modality pipelines (methylation, transcriptomics, feature selection)
│   ├── models/          # BaseBioAgeModel, ElasticNet, RandomForest, XGBoost, Multi-Omics Fusion
│   ├── evaluation/      # Metrics (MAE, RMSE, R2, Pearson, Spearman) & Age Acceleration
│   ├── explainability/  # SHAP explainer (beeswarm, waterfall, global attribution)
│   ├── network/         # Heterogeneous biological interaction graphs & NetworkX centrality
│   ├── gnn/             # PyTorch / PyG graph learning (GCN, GraphSAGE, GAT)
│   ├── pathways/        # Hypergeometric over-representation analysis against aging hallmarks
│   ├── reporting/       # ResearchReportGenerator & PDF exporter (ReportLab)
│   └── utils/           # Synthetic cohort generator, logging, serialization
├── configs/             # YAML configurations for reproducible runs
├── data/
│   ├── raw/             # Uploaded user datasets
│   ├── processed/       # Preprocessed features, model artifacts (.joblib), PDF reports
│   └── example/         # Demo multi-omics cohort & canonical network edge lists
├── docker/              # Multi-stage Dockerfiles for API and Next.js frontend
├── docs/                # Comprehensive scientific and architectural documentation
├── notebooks/           # Interactive research notebooks
├── scripts/             # Data generation and pipeline benchmark scripts
└── tests/               # Pytest suite covering all modules and API endpoints
```

## System Component Responsibilities

1. **Ingestion & Profiler (`bioage.ingestion`)**:
   - Detects orientation (`samples_by_features` vs `features_by_samples`).
   - Identifies candidate sample ID and chronological age columns.
   - Calculates missingness ratios, duplicate counts, and flags invariant/suspicious features.
   - Outputs a typed, machine-readable `DatasetProfile`.

2. **Preprocessing & Feature Selection (`bioage.preprocessing`)**:
   - **Methylation Pipeline**: Beta-value validation [0, 1], median/mean imputation, variance thresholding, CpG whitelist filtering.
   - **Transcriptomics Pipeline**: Non-negativity check, low-expression filtering, CPM library-size normalization, log1p transformation.
   - **Feature Selection**: Supervised ranking via Mutual Information regression against age or Ridge regularized importance with collinearity reduction ($r > 0.95$).

3. **Predictive Modeling (`bioage.models`)**:
   - Epigenetic clock-style **ElasticNet** with cross-validated $\alpha$ and $L_1$ penalty ratio.
   - Non-linear tree ensembles (**RandomForest** and **XGBoost**) capturing epistasis.
   - **Multi-Omics Fusion** (Early concatenation, Late stacking meta-regressor, and Weighted ensemble).

4. **SHAP Explainability (`bioage.explainability`)**:
   - Tree and analytical Shapley value attributions.
   - Global cohort feature importance rankings.
   - Beeswarm plot data (feature value vs direction of impact).
   - Local sample-level waterfall decompositions ($\text{Base Value} + \sum \phi_i = \text{Predicted Age}$).

5. **Biological Network Analysis (`bioage.network`)**:
   - Heterogeneous interaction graph constructed from biomarker seeds.
   - Node types: Gene, Protein, Pathway, Biological Process.
   - Edge types: interaction, regulation, pathway_membership, association.
   - Metrics: Degree, Betweenness Centrality, PageRank, Louvain/greedy modularity community detection.
   - Export to Cytoscape.js format for interactive browser graph rendering.

6. **Graph Neural Networks (`bioage.gnn`)**:
   - Node-level regression and classification using PyTorch / PyTorch Geometric.
   - Architectures: GCN, GraphSAGE, and GAT.
   - Evaluates inductive generalization on test subgraphs.

7. **Pathway Enrichment (`bioage.pathways`)**:
   - Over-representation analysis (ORA) using the hypergeometric distribution.
   - Curated hallmarks of aging database (Senescence, Telomeres, Epigenetics, mTOR Nutrient Sensing, Mitochondrial ROS, Inflammaging, DNA Repair, Proteostasis).
   - Benjamini-Hochberg FDR correction.

8. **Automated Research Reporting (`bioage.reporting`)**:
   - Assembles QC summaries, benchmark metrics, SHAP rankings, pathway findings, and network topology into a structured JSON report and publication-grade PDF document.
