# Supported Biological Dataset Formats & Schema Specifications

## 1. Supported File Formats

BioAge-X accepts raw and processed biological matrices across five standard file formats:

| Format | Extension | Typical Biological Content | Parsing Strategy | Memory Footprint |
| :--- | :--- | :--- | :--- | :--- |
| **Comma-Separated Values** | `.csv` | Tabular methylation beta values, expression, clinical metadata | `pandas.read_csv` with chunked preview | Standard |
| **Tab-Separated Values** | `.tsv`, `.txt` | GDC STAR counts, GEO series matrices, PRIDE abundance | `pandas.read_csv(sep='\t')` | Standard |
| **Apache Parquet** | `.parquet` | Large multi-omics matrices (>10,000 features / >10,000 samples) | `pyarrow` / `fastparquet` | High efficiency, compressed columnar |
| **AnnData H5AD** | `.h5ad` | Single-cell RNA-seq, spatial transcriptomics, multi-modal profiles | `anndata.read_h5ad` (or fallback HDF5 inspection) | Ultra-compact hierarchical |
| **Matrix Market Exchange** | `.mtx`, `.mtx.gz` | Sparse single-cell count matrices (Cell Ranger outputs) | `scipy.io.mmread` | Sparse representation |

---

## 2. Matrix Orientation Detection

Biological repositories frequently publish matrices in inverted orientations. BioAge-X automatically inspects and harmonizes matrix orientation:

### 2.1 Standard Orientation: Samples as Rows
- **Rows**: Individual biological subjects or experimental samples (e.g., `GSM1005001`, `TCGA-A1-A0SK`).
- **Columns**: Chronological age, demographic covariates, and molecular features (e.g., `cg16867657`, `ENSG00000197977`).
- **Detection**: Verified when column count corresponds to molecular feature patterns, or row index matches sample naming conventions.

### 2.2 Inverted / Transposed Orientation: Features as Rows
- **Rows**: Molecular probe IDs or gene symbols (e.g., `cg00000029`, `BRCA1`).
- **Columns**: Sample identifiers.
- **Handling**: Inverted matrices are automatically transposed prior to training:
  $$\mathbf{X}_{\text{standard}} = \mathbf{X}_{\text{raw}}^\top$$
  The sample identifier header is extracted as the index, ensuring feature alignment.

---

## 3. Required & Supported Column Naming Conventions

### 3.1 Primary Sample Identifier
- Accepted column headers: `sample_id`, `sample`, `id`, `geo_accession`, `bcr_patient_barcode`, `donor_id`, `subject_id`.

### 3.2 Chronological Age Column
- Accepted column headers (case-insensitive):
  `chronological_age`, `age`, `age_years`, `age_at_index`, `age_at_diagnosis`, `patient_age`.
- **Normalization**:
  - Values $> 200$ (e.g., GDC days at diagnosis) are automatically normalized via $\text{age}_{\text{years}} = \text{age}_{\text{days}} / 365.25$.
  - Values are checked for plausible human biological ranges ($0 \le \text{age} \le 120$).

### 3.3 Molecular Features
- **DNA Methylation**: Illumina probe names matching `^cg\d{7,8}$` or `^ch\.\d+\.\d+[RF]$`. Beta values must fall within the closed interval $[0.0, 1.0]$.
- **Transcriptomics**: Ensembl Gene IDs (`^ENSG\d{11}$`) or official HGNC gene symbols (e.g., `SIRT1`, `FOXO3`, `TP53`, `MTOR`). Expression counts are recommended in TPM, FPKM, or normalized CPM.
- **Proteomics**: UniProt accession codes (e.g., `P04637`) or protein names.
- **Metabolomics**: ChEBI, HMDB IDs, or chemical nomenclature.

---

## 4. Multi-Omics Manifest Schema Specification

When ingesting complex studies where different molecular modalities reside in separate files, BioAge-X supports declarative manifests in YAML or JSON.

### 4.1 YAML Manifest Schema

```yaml
version: "1.0"
dataset_id: "COHORT_AGING_MULTIMODAL_01"
title: "Human Longitudinal Aging Multi-Omics Cohort"
description: "Matched whole-blood DNA methylation, transcriptomics, and serum proteomics"
organism: "Homo sapiens"
merge_strategy: "intersection"  # Options: 'intersection' (recommended) | 'union'

# Primary clinical and demographic table containing target age
clinical:
  path: "clinical_phenotypes.csv"
  sample_id_column: "sample_id"
  age_column: "chronological_age"
  sex_column: "sex"

# Molecular assay layers
layers:
  - modality: "methylation"
    name: "Illumina 450K DNA Methylation"
    path: "dna_methylation_beta_values.csv"
    sample_id_column: "sample_id"
    features_as_rows: false
    preprocessing: "none"

  - modality: "transcriptomics"
    name: "RNA-seq Normalized Counts (TPM)"
    path: "gene_expression_tpm.parquet"
    sample_id_column: "sample_id"
    features_as_rows: false
    preprocessing: "log1p"

  - modality: "proteomics"
    name: "Olink Plasma Proteomics"
    path: "plasma_proteome_npz.tsv"
    sample_id_column: "sample_id"
    features_as_rows: false
    preprocessing: "standardize"
```

### 4.2 Merge Strategy Rules
- **`intersection`**: Retains strictly the subset of samples present in all defined layers:
  $$\mathcal{S}_{\text{cohort}} = \mathcal{S}_{\text{clinical}} \cap \mathcal{S}_{\text{meth}} \cap \mathcal{S}_{\text{rna}} \cap \mathcal{S}_{\text{prot}}$$
  Ensures no missing modality columns for multimodal fusion models.
- **`union`**: Aligns all unique samples across defined layers:
  $$\mathcal{S}_{\text{cohort}} = \mathcal{S}_{\text{clinical}} \cup \mathcal{S}_{\text{meth}} \cup \mathcal{S}_{\text{rna}} \cup \mathcal{S}_{\text{prot}}$$
  Missing modality entries are populated with NaN and handled by downstream imputers or modality-specific sub-networks.
