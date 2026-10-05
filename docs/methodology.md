# BioAge-X Computational Methodology

BioAge-X is a two-phase computational biology research framework bridging molecular age prediction (Phase 1) with systems biology interactomics and graph neural networks (Phase 2).

---

## 1. Two-Phase Research Framework

```
                     MOLECULAR OMICS DATA
                               ↓
         ┌───────────────────────────────────────────┐
         │                  PHASE 1                  │
         │     MULTI-OMICS BIOLOGICAL AGE PREDICTION │
         └─────────────────────┬─────────────────────┘
                               ↓
                   Biological Age Prediction
                               ↓
                   Age Acceleration Residuals
                               ↓
            Epigenetic Clock Benchmarking (Horvath / Hannum / PhenoAge)
                               ↓
                   SHAP Attribution Engine
                               ↓
                 Biomarker-to-Biology Bridge
                               ↓
         ┌───────────────────────────────────────────┐
         │                  PHASE 2                  │
         │       GRAPHOMICS-AI NETWORK BIOLOGY       │
         └─────────────────────┬─────────────────────┘
                               ↓
                     Gene & Protein Mapping
                               ↓
                 Biological Interactome Construction
                               ↓
                Network Centrality & Community Structure
                               ↓
                 Pathway Over-Representation (ORA)
                               ↓
               Graph Neural Networks (GCN / GraphSAGE)
                               ↓
                 Candidate Aging Network Signals
```

---

## 2. Phase 1: Biological Age & Age Acceleration

In chronological regression models, target $y$ represents chronological age in years.
Given a molecular feature vector $\mathbf{x}_i \in \mathbb{R}^d$ for subject $i$, the model outputs predicted biological age $\hat{y}_i$.

### Age Acceleration ($\Delta_i$)
Age acceleration is defined as the mathematical residual:
$$\Delta_i = \hat{y}_i - y_i$$

- **Accelerated Aging ($\Delta_i > +1.0$ years)**: The subject's molecular profile statistically resembles an older individual.
- **Decelerated Aging ($\Delta_i < -1.0$ years)**: The subject's molecular profile exhibits younger characteristics relative to chronological peers.
- **Synchronous Aging ($-1.0 \le \Delta_i \le +1.0$ years)**: Molecular status aligns with chronological expectation.

*Scientific Note: Biological age acceleration indicates statistical discrepancy between molecular biomarker states and chronological expectations under specific statistical assumptions. It does not prove disease diagnosis or individual clinical prognosis.*

---

## 3. Reference Epigenetic Clock Mathematical Formulations

BioAge-X benchmarks trained models against canonical reference epigenetic clocks using exact published coefficients and mathematical transformations:

### A. Horvath Multi-Tissue Clock (2013)
Horvath's pan-tissue clock employs a non-linear piecewise transformation $F(x)$ representing the logarithmically decelerating rate of development in early life followed by linear progression in adult life:

$$F(\text{Age}) = \begin{cases} \log(\text{Age} + 1) - \log(21), & \text{if } \text{Age} \le 20 \\ \frac{\text{Age} - 20}{21}, & \text{if } \text{Age} > 20 \end{cases}$$

Linear predictor score from CpG beta values $\beta_j$:
$$\text{Linear Score } S = \beta_0 + \sum_{j=1}^{353} w_j \beta_j$$

Predicted biological age is recovered using the exact inverse transformation $F^{-1}(S)$:
$$F^{-1}(S) = \begin{cases} 21 \cdot e^S - 1, & \text{if } S < 0 \\ 21 \cdot S + 20, & \text{if } S \ge 0 \end{cases}$$

### B. Hannum Whole Blood Clock (2013)
Hannum's clock models chronological age directly from 71 whole-blood CpG methylation beta values and clinical covariates (Sex, BMI, Cohort Batch):
$$\hat{y}_{\text{Hannum}} = \beta_0 + \sum_{j=1}^{71} w_j \beta_j + w_{\text{gender}} \cdot \text{Sex} + w_{\text{bmi}} \cdot \text{BMI}$$

### C. Levine PhenoAge Clock (2018)
PhenoAge measures mortality-associated phenotypic biological age derived from 513 CpGs weighted by Gompertz proportional hazards parameters:
$$\hat{y}_{\text{PhenoAge}} = \beta_0 + \sum_{j=1}^{513} w_j \beta_j$$

### Coverage Verification & Missing Probe Policy
When input datasets lack required reference probes, BioAge-X:
1. Calculates exact feature overlap: $\text{Coverage \%} = \frac{|\mathcal{F}_{\text{dataset}} \cap \mathcal{F}_{\text{clock}}|}{|\mathcal{F}_{\text{clock}}|} \times 100\%$.
2. Marks clocks as `UNAVAILABLE` or `PARTIAL_COVERAGE` with full probe audit lists.
3. Strictly forbids fabricating imputed values for missing reference loci.

---

## 4. Multi-Omics Preprocessing & Feature Selection

### DNA Methylation Preprocessing
1. **Range Verification**: Ensures CpG beta values $\beta \in [0.0, 1.0]$.
2. **Missingness Pruning**: Drops probes where missing rate $> 10\%$.
3. **Median Imputation**: Cohort median imputation for remaining values.
4. **Variance Filtering**: Discards invariant probes ($\sigma^2 < 0.001$).
5. **Optional M-value Transformation**:
   $$M = \log_2\left(\frac{\beta}{1 - \beta}\right)$$

### Transcriptomics Preprocessing
1. **Non-negativity Verification**: Confirms valid count/abundance values.
2. **Low-Expression Filtering**: Retains genes expressed ($\ge 1.0$) in $\ge 10\%$ of samples.
3. **CPM Normalization**: Standardizes library sequencing depth:
   $$\text{CPM}_j = \frac{C_j}{\sum_k C_k} \times 10^6$$
4. **Variance-Stabilizing Log Transformation**: $\log_2(\text{CPM} + 1)$.

### Supervised Feature Selection
To prevent data leakage, feature selection operates strictly on training partitions:
1. **Mutual Information Regression**:
   $$I(X; Y) = \iint p(x, y) \log \frac{p(x, y)}{p(x)p(y)} \, dx \, dy$$
2. **Collinearity Pruning**: Identifies redundant features with Pearson correlation $|r| > 0.95$ and retains the feature with highest mutual information.

---

## 5. Multi-Omics Fusion Paradigms

1. **Early Fusion**: Concatenates normalized modality matrices into a joint space:
   $$\mathbf{X}_{\text{joint}} = [\mathbf{X}_{\text{meth}} \,||\, \mathbf{X}_{\text{trans}}]$$
2. **Late Fusion**: Fits independent base estimators $f_m(\mathbf{x}_m)$ per modality and trains a meta-learner $\mathcal{M}$:
   $$\hat{y} = \mathcal{M}(f_{\text{meth}}(\mathbf{x}_{\text{meth}}), f_{\text{trans}}(\mathbf{x}_{\text{trans}}))$$
3. **Weighted Ensemble**: Combines modality predictions using inverse-MAE weights:
   $$w_m = \frac{1 / \text{MAE}_m}{\sum_{k} 1 / \text{MAE}_k}, \quad \hat{y} = \sum_m w_m \hat{y}_m$$

---

## 6. SHAP & Biomarker-to-Biology Bridge

### Shapley Additive Explanations (SHAP)
Shapley values allocate additive feature attributions satisfying efficiency:
$$\sum_{j=1}^M \phi_{i,j} = f(\mathbf{x}_i) - \mathbb{E}[f(\mathbf{x})]$$

Global importance ranks candidate features by mean absolute SHAP value:
$$I_j = \frac{1}{N} \sum_{i=1}^N |\phi_{i,j}|$$

### Biomarker-to-Biology Bridge
Candidate features are annotated through a biological knowledge hierarchy:
$$\text{CpG Probe } (cgXXXX) \longrightarrow \text{Target Gene Symbol} \longrightarrow \text{Protein / UniProt} \longrightarrow \text{Interactome Graph } G=(V, E)$$

Terminology distinguishes:
- **Model-Associated Feature**: High computational attribution without biological proof.
- **Candidate Aging-Associated Biomarker**: Feature supported by functional annotation and reproducible across folds.

---

## 7. Phase 2: GraphOmics-AI & Network Analysis

### Biological Interaction Graph $G = (V, E)$
Constructed from candidate biomarker seed entities and high-confidence physical protein-protein interactions (PPI) and curated regulatory pathways:
- Nodes $V$: Genes, proteins, functional pathways.
- Edges $E$: Physical interactions, transcriptional regulation, pathway memberships.

### Network Topology Metrics
1. **Degree Centrality**: $C_D(v) = \frac{\text{deg}(v)}{|V| - 1}$
2. **Betweenness Centrality**:
   $$C_B(v) = \sum_{s \ne v \ne t} \frac{\sigma_{st}(v)}{\sigma_{st}}$$
3. **PageRank**: Stationary distribution under random walk with damping factor $d = 0.85$:
   $$\mathbf{p} = \frac{1 - d}{|V|} \mathbf{1} + d \mathbf{A}^T \mathbf{D}^{-1} \mathbf{p}$$
4. **Louvain Community Detection**: Maximizes modularity $Q$ across interactome partitions.

---

## 8. Graph Neural Networks (GNN)

BioAge-X models aging-associated network signals using message-passing neural networks:

### Graph Convolutional Network (GCN)
Spectral layer-wise propagation:
$$H^{(l+1)} = \sigma\left(\tilde{D}^{-\frac{1}{2}} \tilde{A} \tilde{D}^{-\frac{1}{2}} H^{(l)} W^{(l)}\right)$$
where $\tilde{A} = A + I_N$ is the adjacency matrix with self-loops, and $\tilde{D}_{ii} = \sum_j \tilde{A}_{ij}$.

### GraphSAGE
Inductive neighborhood aggregation:
$$h_v^{(l+1)} = \sigma\left(W^{(l)} \cdot \left[ h_v^{(l)} \,\|\, \text{AGG}\left(\{h_u^{(l)}, \forall u \in \mathcal{N}(v)\}\right) \right]\right)$$

### Objective Function
Supervised regression on node-level aging centrality targets $s_v$:
$$\mathcal{L}_{\text{GNN}} = \frac{1}{|V_{\text{train}}|} \sum_{v \in V_{\text{train}}} (\hat{s}_v - s_v)^2 + \lambda \|W\|_2^2$$

All GNN predictions are explicitly designated as **computational predictions** to distinguish model-derived hypotheses from in vitro/in vivo biological validation.

