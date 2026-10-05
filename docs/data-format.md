# BioAge-X Data Format Specification

BioAge-X supports ingestion of tabular multi-omics datasets formatted as **CSV**, **TSV**, **Parquet**, or **H5AD (AnnData)**.

## 1. Supported Orientations

The platform automatically detects both standard biological matrix orientations:

### Preferred: Samples as Rows (`samples_by_features`)

| sample_id | chronological_age | sex | cg16867657_ELOVL2 | cg06639320_FHL2 | GENE_CDKN2A | GENE_SIRT1 |
|:---|:---|:---|:---|:---|:---|:---|
| BIOAGE_001 | 54.2 | Female | 0.782 | 0.651 | 8.94 | 5.21 |
| BIOAGE_002 | 31.8 | Male | 0.312 | 0.380 | 4.12 | 8.45 |

### Transposed: Features as Rows (`features_by_samples`)

| Probe_ID | Sample_01 | Sample_02 | Sample_03 |
|:---|:---|:---|:---|
| cg16867657 | 0.782 | 0.312 | 0.654 |
| cg06639320 | 0.651 | 0.380 | 0.521 |
| CDKN2A | 8.94 | 4.12 | 6.80 |

*When `features_by_samples` orientation is detected, BioAge-X automatically transposes the matrix so samples are rows for downstream machine learning.*

## 2. Recognized Columns & Identifiers

- **Sample Identifier**: Detected by names such as `sample_id`, `sampleid`, `id`, `gsm`, `tcga_id`, or `subject_id`.
- **Chronological Age**: Detected by names such as `chronological_age`, `age`, `age_years`, or `chron_age`. Target must be numeric.
- **DNA Methylation Probes**: Illumina 450K/EPIC probe IDs starting with `cg` (e.g. `cg16867657`, `cg06639320`). Beta values should fall in $[0.0, 1.0]$.
- **Gene Expression**: HUGO gene symbols (e.g. `CDKN2A`, `TP53`, `SIRT1`, `IL6`) or prefixed with `GENE_`.
- **Phenotypic Covariates**: Categorical or continuous variables such as `sex`, `smoking_status`, `bmi`, `tissue_type`.
