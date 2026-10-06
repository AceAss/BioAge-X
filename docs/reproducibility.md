# BioAge-X Reproducibility Guidelines

Reproducibility is a foundational pillar of the BioAge-X research platform. Every experiment, model artifact, and generated PDF report carries a cryptographic fingerprint.

## 1. Experiment Fingerprinting

When an experiment is executed, BioAge-X calculates a SHA-256 reproducibility hash derived from:
- Dataset ID and matrix dimensions
- Preprocessing hyperparameters (variance threshold, imputation, normalizations)
- Selected feature subset names
- Model algorithm and hyperparameters
- Execution timestamp and package versions

This hash is stamped on the exported PDF research report and saved in the SQLite/PostgreSQL `experiments` table.

## 2. Deterministic Execution

- All stochastic algorithms (Random Forest, XGBoost, GNN training, train/val/test masking) accept a configurable `random_state` (default: 42).
- Data splits are deterministic.
- Model artifacts are serialized with `joblib` into `data/processed/{model_id}.joblib` for identical inference across environments.

## 3. Configuration via YAML

Pipelines can be fully reproduced from external configuration files stored in `configs/`:
- `configs/default_config.yaml`
- `configs/methylation_pipeline.yaml`
- `configs/transcriptomics_pipeline.yaml`
- `configs/model_benchmarks.yaml`

## 4. Dataset Lineage & Acquisition Provenance

Every dataset acquired through the Universal Data Acquisition layer receives a permanent `DatasetProvenanceRecord`:
- Source repository name and accession identifier
- Direct retrieval URL and timestamp (ISO 8601 UTC)
- Cryptographic SHA-256 / MD5 checksum of downloaded archive or matrix
- Original study citation and publication reference
- Preprocessing history (orientation transposition, age unit harmonization, imputation)

## 5. Automated Reproducibility Audit Script

BioAge-X provides a dedicated automated reproducibility test suite:
```bash
python scripts/verify_reproducibility.py
```
This script executes two independent, end-to-end runs across preprocessing, feature selection, ElasticNet, RandomForest, SHAP explainability, biological network construction, and GNN training, asserting numerical equivalence:
$$\max |\hat{y}^{(1)} - \hat{y}^{(2)}| < 1.0 \times 10^{-12}$$
Ensuring bit-exact scientific determinism across computational environments.
