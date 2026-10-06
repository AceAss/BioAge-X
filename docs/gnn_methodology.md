# Graph Neural Network (GNN) & Network Biology Methodology

## 1. Overview of Phase 2: GraphOmics-AI

While Phase 1 in BioAge-X quantifies biological aging via statistical and machine learning clocks (ElasticNet, Random Forest, XGBoost, Multi-Omics Early Fusion), Phase 2 grounds these statistical predictions in molecular biological networks.

Graph Neural Networks (GNNs) in BioAge-X operate directly on biological interactomes (protein-protein interaction networks, gene regulatory graphs, and metabolic pathways) where:
- **Nodes** ($\mathcal{V}$) represent genes, proteins, or biological hallmarks of aging.
- **Edges** ($\mathcal{E}$) represent validated physical, functional, or regulatory interactions sourced from STRING-db, Reactome, and curated literature.
- **Node Features** ($\mathbf{X} \in \mathbb{R}^{|\mathcal{V}| \times d}$) encode multi-modal biological signals, including feature importance attributions (SHAP values) derived from Phase 1 models, baseline expression/methylation intensities, network centrality scores, and hallmark membership flags.

---

## 2. Supported GNN Architectures

BioAge-X provides three complementary graph neural network architectures optimized for biological interactomes:

### 2.1 Graph Convolutional Network (GCN) (`BioAgeGCN`)
Applies localized spectral graph convolutions using the symmetric normalized adjacency matrix:
$$\mathbf{H}^{(l+1)} = \sigma \left( \mathbf{\tilde{D}}^{-\frac{1}{2}} \mathbf{\tilde{A}} \mathbf{\tilde{D}}^{-\frac{1}{2}} \mathbf{H}^{(l)} \mathbf{W}^{(l)} \right)$$
where $\mathbf{\tilde{A}} = \mathbf{A} + \mathbf{I}_N$ is the graph adjacency matrix with self-loops, $\mathbf{\tilde{D}}_{ii} = \sum_j \mathbf{\tilde{A}}_{ij}$ is the diagonal degree matrix, $\mathbf{W}^{(l)}$ is the layer weight matrix, and $\sigma(\cdot)$ is the ReLU activation function.

### 2.2 GraphSAGE (`BioAgeGraphSAGE`)
Performs inductive neighborhood representation learning via aggregation:
$$\mathbf{h}_{\mathcal{N}(v)}^{(l+1)} = \text{AGGREGATE}_k \left( \left\{ \mathbf{h}_u^{(l)}, \forall u \in \mathcal{N}(v) \right\} \right)$$
$$\mathbf{h}_v^{(l+1)} = \sigma \left( \mathbf{W}^{(l)} \cdot \left[ \mathbf{h}_v^{(l)} \,\|\, \mathbf{h}_{\mathcal{N}(v)}^{(l+1)} \right] \right)$$
BioAge-X supports mean, pooling, and LSTM aggregation operators. GraphSAGE allows inductive generalization to newly discovered interactome nodes without requiring full-graph retraining.

### 2.3 Graph Attention Network (GAT) (`BioAgeGAT`)
Dynamically weights neighborhood edges using multi-head self-attention coefficients:
$$\alpha_{ij} = \frac{\exp \left( \text{LeakyReLU} \left( \mathbf{a}^\top \left[ \mathbf{W}\mathbf{h}_i \,\|\, \mathbf{W}\mathbf{h}_j \right] \right) \right)}{\sum_{k \in \mathcal{N}(i)} \exp \left( \text{LeakyReLU} \left( \mathbf{a}^\top \left[ \mathbf{W}\mathbf{h}_i \,\|\, \mathbf{W}\mathbf{h}_k \right] \right) \right)}$$
$$\mathbf{h}_i^{(l+1)} = \sigma \left( \sum_{j \in \mathcal{N}(i)} \alpha_{ij} \mathbf{W} \mathbf{h}_j \right)$$
Attention coefficients reveal which molecular partners contribute most strongly to biological age acceleration in specific disease states.

---

## 3. Phase 1 Signal Integration Bridge

To avoid disconnects between Phase 1 tabular predictions and Phase 2 graph models, the `BiomarkerToBiologyBridge` maps top-ranking molecular features into graph seeds:
1. **SHAP Attribution Extraction**: Phase 1 models yield sample-level and global SHAP attribution vectors.
2. **Feature Mapping**: Illumina CpG probe IDs (`cg*`) are mapped to their nearest genomic promoters and host genes via the Ensembl client. HGNC symbols and Ensembl IDs are mapped to canonical STRING identifiers.
3. **Graph Node Injection**: Seed nodes are expanded using the 1st and 2nd degree STRING interactome (with confidence threshold $\ge 0.40$).
4. **Signal Transfer**: Each graph node is initialized with a feature vector $\mathbf{x}_v = [\text{SHAP}_v, \mu_{\text{expr}, v}, \sigma^2_{\text{expr}, v}, C_{\text{betweenness}, v}]$.

---

## 4. Large-Scale Synthetic Graph Benchmark Protocol

### 4.1 Specification and Rigor
To validate GNN convergence on realistic topological structures prior to training on noisy experimental data, BioAge-X includes a formal large-graph benchmark generator (`bioage.gnn.benchmark.create_large_graph_benchmark`):
- **Node Scale**: $N \ge 180$ biologically annotated nodes (spanning primary aging hallmarks: Genomic Instability, Telomere Attrition, Epigenetic Alterations, Loss of Proteostasis, Deregulated Nutrient Sensing, Mitochondrial Dysfunction, Cellular Senescence, Stem Cell Exhaustion, Altered Intercellular Communication).
- **Edge Scale**: $E \ge 700$ directed biological edges generated via small-world and scale-free topology with biological modularity.
- **Labeling Standard**: Must be explicitly tagged with:
  ```json
  "benchmark_type": "SYNTHETIC GRAPH BENCHMARK",
  "biological_grounding": "Simulated multi-hallmark interactome (180+ nodes, 700+ edges) for topological validation"
  ```

### 4.2 Task-Appropriate Evaluation Metrics
BioAge-X strictly differentiates regression and classification evaluation tasks:
- **Node Age Acceleration Regression**:
  - Primary Metric: Mean Squared Error (MSE), Mean Absolute Error (MAE).
  - Goodness of Fit: Coefficient of Determination ($R^2$), Pearson correlation coefficient ($r$).
  - **Forbidden**: Reporting accuracy, F1 score, precision, or recall for continuous regression tasks.
- **Node Hallmark Classification** (e.g., Senescence Driver vs Bystander):
  - Primary Metric: Accuracy, Balanced Accuracy.
  - Multi-class / Imbalanced: Macro-F1 score, Area Under ROC Curve (AUROC), Area Under Precision-Recall Curve (AUPRC).
  - **Forbidden**: Reporting MSE or MAE for discrete categorization tasks.
