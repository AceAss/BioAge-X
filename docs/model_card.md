# BioAge-X Model Card

## 1. Model Details & Architecture Overview
BioAge-X implements a formal two-phase architecture spanning regularized regression, non-linear ensemble models, and Graph Neural Networks (GNNs):

| Model Name | Class Identifier | Learning Objective | Key Hyperparameters / Assumptions | Primary Strengths |
| :--- | :--- | :--- | :--- | :--- |
| **BioAge ElasticNet** | `BioAgeElasticNet` | $\min_{\beta} \|y - X\beta\|_2^2 + \lambda_1 \|\beta\|_1 + \lambda_2 \|\beta\|_2^2$ | $L_1$ ratio $\in [0.1, 0.9]$, 5-fold internal $\alpha$-CV | High sparsity, strict interpretability, exact linear Shapley values |
| **BioAge Random Forest**| `BioAgeRandomForest` | Ensemble of bagged decision trees | `n_estimators=100`, `max_depth=8`, bootstrap resamples | Captures non-linear thresholds, robust to outlier features |
| **BioAge XGBoost** | `BioAgeXGBoost` | Gradient boosted tree residuals | `learning_rate=0.05`, `max_depth=4`, early stopping | High predictive capacity, fast inference on dense tabular matrices |
| **Multi-Omics Early Fusion**| `BioAgeEarlyFusion` | Joint feature representation | Z-score normalization per modality, weighted regularization | Captures cross-modality molecular correlations |
| **BioAge GCN** | `BioAgeGCN` | $H^{(l+1)} = \sigma(\tilde{D}^{-\frac{1}{2}}\tilde{A}\tilde{D}^{-\frac{1}{2}}H^{(l)}W^{(l)})$ | 2 GraphConv layers, hidden dim=64, Adam lr=0.01 | Exploits protein-protein physical and functional interactomes |
| **BioAge GraphSAGE** | `BioAgeGraphSAGE` | Neighborhood feature aggregation | Mean aggregation, 2 hops, dropout=0.2 | Inductive graph learning, scalable to dense subgraphs |

---

## 2. Intended Use & Target Users
- **Intended Use**:
  - Computational biology research and exploratory biomarker discovery.
  - Benchmarking novel molecular datasets against canonical first-generation epigenetic clocks (Horvath, Hannum, PhenoAge).
  - Investigating biological network topology and protein-protein interactions associated with cellular senescence.
  - Multi-omics ablation studies and dataset shift analysis.
- **Target Users**: Computational biologists, bioinformaticians, biogerontology researchers, and systems biology academic labs.

---

## 3. Non-Intended Use & Prohibited Scenarios
- **NO CLINICAL DIAGNOSES**: BioAge-X is strictly an in silico research tool. It is NOT FDA/EMA approved as a medical diagnostic device or clinical laboratory test.
- **NO THERAPEUTIC CLAIMS**: Age acceleration residuals must not be used to prescribe anti-aging pharmaceuticals, supplements, or medical interventions.
- **NO INDIVIDUAL PROGNOSTICATION**: Statistical predictions should not be communicated to individual patients as clinical healthspan or life expectancy estimates.

---

## 4. Evaluation Methodology & Rigor
- **Data Leakage Prevention**: Feature scaling, median imputation, Mutual Information feature selection, and interactome seed definitions execute **strictly inside training folds**.
- **Cross-Validation**: 5-Fold Stratified Cross-Validation reporting complete fold-by-fold distributions rather than opaque point estimates.
- **Bootstrap Uncertainty**: 95% empirical bootstrap confidence intervals ($B=1000$) quantify statistical parameter uncertainty.
- **Explainability**: Exact Shapley additive explanations verify the efficiency axiom $\sum \phi_i + \mathbb{E}[f(X)] = f(\mathbf{x})$.

---

## 5. Known Failure Modes & Biological Failure Scenarios
1. **Age Range Extrapolation (Age-Bias)**: Models exhibit "regression toward the mean" where young individuals ($<30\text{ yrs}$) receive positive residuals (predicted older) and elderly individuals ($>75\text{ yrs}$) receive negative residuals (predicted younger).
2. **Platform Mismatch**: Evaluated on platforms lacking core training probes (e.g. testing an 450K model on an RNA-seq cohort) triggers an explicit `EXTERNAL_VALIDATION_NOT_AVAILABLE` flag.
3. **Severe Dataset Shift**: Cross-cohort validation between disparate tissue types or demographically skewed populations will exhibit elevated MAE ($>10\text{ yrs}$) due to unmeasured covariate shift.
4. **Interactome Hub Over-Attribution**: Well-studied cancer hubs (e.g. *TP53*, *AKT1*) in public PPI databases may receive disproportionate topological centrality in Phase 2 networks without being uniquely specific to biological aging.
