# BioAge-X Computational Methodology

## 1. Biological Age & Age Acceleration

In chronological regression models, target $y$ represents chronological age in years.
Given molecular feature vector $\mathbf{x}_i$ for subject $i$, the model outputs estimated biological age $\hat{y}_i$.

**Age Acceleration ($\Delta_i$)** is defined as the residual:
$$\Delta_i = \hat{y}_i - y_i$$

- **Accelerated Aging ($\Delta_i > +1.0$ years)**: The subject's molecular profile resembles that of an older individual.
- **Decelerated Aging ($\Delta_i < -1.0$ years)**: The subject's molecular profile exhibits younger characteristics relative to chronological peers.
- **Synchronous Aging ($-1.0 \le \Delta_i \le +1.0$ years)**: Molecular status aligns with chronological age.

*Scientific Note: Biological age acceleration indicates statistical discrepancy between molecular biomarker states and chronological expectations. It does not prove disease incidence or individual clinical outcomes.*

## 2. DNA Methylation Preprocessing

DNA methylation beta values $\beta \in [0.0, 1.0]$ represent the ratio of methylated signal intensity to total intensity:
$$\beta = \frac{M}{M + U + \alpha}$$

1. **Range Validation**: Beta values outside $[0.0, 1.0]$ are clipped or flagged.
2. **Missingness Filter**: Probes with missingness exceeding $10\%$ are discarded.
3. **Imputation**: Median imputation per CpG probe across the cohort.
4. **Variance Filtering**: Probes with variance below threshold (e.g. $\sigma^2 < 0.002$) are excluded.
5. **Optional M-value Transformation**:
   $$M = \log_2\left(\frac{\beta}{1 - \beta}\right)$$

## 3. Transcriptomics Normalization

1. **Non-negativity Validation**: Expression values are checked for valid physical counts or positive normalized levels.
2. **Low-Expression Filtering**: Genes must be expressed ($\ge 1.0$) in at least $10\%$ of cohort samples.
3. **CPM Normalization**: Standardizes sequencing depth across samples:
   $$\text{CPM}_j = \frac{C_j}{\sum_k C_k} \times 10^6$$
4. **Log Transformation**: Variance-stabilizing transformation $\log_2(\text{CPM} + 1)$.

## 4. Multi-Omics Fusion Paradigms

1. **Early Fusion**: Concatenates normalized methylation features and transcriptomic expression into a unified matrix $\mathbf{X} = [\mathbf{X}_{\text{meth}} \,||\, \mathbf{X}_{\text{trans}}]$.
2. **Late Fusion**: Trains independent models on individual modalities ($f_{\text{meth}}(\mathbf{x}_{\text{meth}})$ and $f_{\text{trans}}(\mathbf{x}_{\text{trans}})$), then fits a meta-learner (e.g. Ridge regression) on predictions:
   $$\hat{y} = w_0 + w_1 \hat{y}_{\text{meth}} + w_2 \hat{y}_{\text{trans}}$$
3. **Weighted Ensemble**: Robust weighted average handling missing modalities by normalizing weights over present data streams.

## 5. SHAP (Shapley Additive Explanations)

Shapley values assign each biomarker feature an attribution value $\phi_i$ satisfying efficiency:
$$\sum_{j=1}^M \phi_{i,j} = f(\mathbf{x}_i) - E[f(\mathbf{x})]$$

- **TreeExplainer**: Exact polynomial-time computation for tree ensembles.
- **Global Importance**: Mean absolute SHAP across samples:
  $$I_j = \frac{1}{N} \sum_{i=1}^N |\phi_{i,j}|$$

## 6. Functional Pathway Over-Representation Analysis

For a candidate gene set of size $n$ drawn from a genome universe of $M$ genes, the probability of observing $k$ or more overlaps with a pathway of size $N$ is evaluated via the hypergeometric distribution:
$$P(X \ge k) = \sum_{x=k}^{\min(n, N)} \frac{\binom{N}{x} \binom{M - N}{n - x}}{\binom{M}{n}}$$

P-values are corrected for multiple hypothesis testing using the Benjamini-Hochberg False Discovery Rate (FDR).
