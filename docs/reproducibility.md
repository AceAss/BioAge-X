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
