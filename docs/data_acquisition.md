# Universal Biological Data Acquisition Framework

## 1. Overview and Architecture

BioAge-X provides a production-grade, multi-repository biological data acquisition engine capable of discovering, downloading, validating, and ingesting datasets from leading biomedical data repositories. Rather than restricting research workflows to NCBI GEO, the platform abstracts biological repositories into a unified, extensible connector architecture.

```
                          ┌─────────────────────────┐
                          │   Frontend Explorer UI  │
                          │   (/datasets/explorer)  │
                          └────────────┬────────────┘
                                       │ REST / SSE
                                       ▼
                          ┌─────────────────────────┐
                          │   FastAPI Endpoints     │
                          │   /api/v1/data-sources  │
                          │   /api/v1/downloads     │
                          └────────────┬────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
        ┌───────────────────────┐             ┌───────────────────────┐
        │ UniversalResolver     │             │ AcquisitionRegistry   │
        │ - Accession Regex     │             │ - 12 Registered       │
        │ - URL Scheme Routing  │             │   Provider Connectors │
        └───────────┬───────────┘             └───────────┬───────────┘
                    └──────────────────┬──────────────────┘
                                       ▼
                       ┌──────────────────────────────┐
                       │       DatasetProvider        │
                       │  Search / Metadata / Options │
                       └──────────────┬───────────────┘
                                       ▼
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
┌──────────────────┐         ┌───────────────────┐         ┌──────────────────┐
│ DownloadManager  │         │  DatasetValidator │         │ DatasetNormalizer│
│ - Streaming      │         │ - Format / Parse  │         │ - Age harmoniz.  │
│ - Range Resume   │         │ - Feature / Sample│         │ - Probe / Gene ID│
│ - Checksum (SHA) │         │ - Missingness     │         │ - Variance cut   │
│ - Disk Preflight │         │ - Age column det. │         │ - Imputation     │
└────────┬─────────┘         └─────────┬─────────┘         └────────┬─────────┘
         └─────────────────────────────┼────────────────────────────┘
                                       ▼
                       ┌──────────────────────────────┐
                       │ Multi-Omics Manifest / Merge │
                       │ - Sample ID Intersection     │
                       │ - Modality Union / Outer     │
                       └──────────────┬───────────────┘
                                       ▼
                       ┌──────────────────────────────┐
                       │  Processed Data & Ingestion  │
                       │  - Dataset Lineage & Provenance
                       │  - Local Cache & Audit Trail │
                       └──────────────────────────────┘
```

---

## 2. Core Components

### 2.1 Universal Accession & URL Resolver (`bioage/acquisition/resolver.py`)
The `UniversalAccessionResolver` inspects user queries or pasted inputs and dynamically routes them to the correct repository connector:
- **Direct Accessions**: Matches accession regexes across registered providers (e.g., `GSE\d+`, `PRD\d+|PXD\d+`, `MTBLS\d+`, `TCGA-[A-Z]+`, `PRJ[A-Z0-9]+`, `SRX\d+`, `ERR\d+`).
- **Direct URLs**: Recognizes HTTP/HTTPS links pointing to tabular or multi-omics matrices (`.csv`, `.tsv`, `.parquet`, `.h5ad`, `.tar.gz`, `.zip`) and routes them to `GenericURLProvider`.
- **Manifests**: Recognizes `.yaml` and `.json` manifest specifications for multi-omics cohort ingestion.

### 2.2 Provider Registry (`bioage/acquisition/registry.py`)
`AcquisitionRegistry` maintains isolated instances of all registered providers. It supports thread-safe registration, capability querying, accession matching, and filtering by biological modality (transcriptomics, methylation, proteomics, metabolomics, multi-omics).

### 2.3 Streaming Download Engine (`bioage/acquisition/downloader.py`)
`DownloadManager` executes reliable HTTP/HTTPS and FTP downloads with production safety:
- **Chunked Streaming**: 64 KB chunk streaming prevents out-of-memory errors on large matrices.
- **Range-Header Resume**: Automatically resumes interrupted downloads if the remote server supports HTTP `Range`.
- **Disk Preflight Checks**: Verifies that the destination drive has at least 1.5× the required free disk space before initiating transfers.
- **Cryptographic Checksums**: Validates file integrity via SHA-256 or MD5 hashes post-download.
- **Progress Tracking & Callbacks**: Emits real-time progress events (bytes downloaded, total bytes, transfer speed MB/s, ETA) to asynchronous job managers and SSE event streams.

### 2.4 Archive Extraction Security (`bioage/acquisition/extractor.py`)
`SafeExtractor` handles `.zip`, `.tar.gz`, `.tgz`, `.tar.bz2`, and `.gz` archives while defending against security vulnerabilities:
- **ZipSlip Traversal Defense**: Rejects any archive member with paths resolving outside the target directory (e.g., `../../etc/passwd`).
- **Decompression Bomb Protection**: Enforces uncompressed file size quotas (default 10 GB) and compression ratio limits (default 100:1) to prevent resource exhaustion attacks.

### 2.5 Validation Engine (`bioage/acquisition/validator.py`)
`DatasetValidator` executes deep inspection of candidate datasets prior to ingestion:
- **Format Inspection**: Parses CSV, TSV, Parquet, and H5AD structures.
- **Orientation Detection**: Distinguishes between Samples × Features (samples as rows) and Features × Samples (transposed matrices, common in microarray and RNA-seq studies).
- **Target Identification**: Identifies chronological age columns via case-insensitive pattern matching (`age`, `chronological_age`, `age_years`, `age_at_index`, `age_at_diagnosis`).
- **Feature Typing**: Automatically classifies molecular features into DNA methylation CpG probes (`cg\d+`), Ensembl gene IDs (`ENSG\d+`), HGNC gene symbols, protein accessions, or metabolite identifiers.
- **Quality Metrics**: Computes sample counts, feature counts, missingness percentage, and feature variance.

### 2.6 Normalization Pipeline (`bioage/acquisition/normalizer.py`)
`DatasetNormalizer` transforms heterogeneous raw matrices into unified representations:
- **Harmonized Age Units**: Converts days or months (e.g., GDC `age_at_index` in days) to chronological years.
- **Missing Value Handling**: Provides median imputation, KNN imputation, or complete-case filtering.
- **Quality Thresholding**: Filters zero-variance features and applies log2 / log1p transforms where appropriate for count matrices.

### 2.7 Multi-Omics Manifest & Merge Engine (`bioage/acquisition/multi_omics.py`)
`MultiOmicsAssemblyEngine` orchestrates multi-modal cohort integration:
- **Sample Intersection (`intersection`)**: Aligns multi-omics layers by strictly matching common sample identifiers across all assays.
- **Modality Union (`union`)**: Retains all samples across all assays, filling unmeasured modalities with NaN or modal medians, enabling maximal cohort utilization.
- **Schema Validation**: Validates cohort metadata, per-layer file paths, assay modalities, and primary sample key configurations.

---

## 3. Asynchronous Job & SSE Streaming System (`bioage/acquisition/jobs.py`)

BioAge-X decouples long-running dataset downloads and normalization from synchronous HTTP requests:
1. When a client requests a download via `POST /api/v1/downloads`, an asynchronous task is dispatched.
2. The endpoint returns immediately with a unique `job_id` and initial status `PENDING`.
3. The background task streams progress updates through `JobManager`.
4. The client subscribes to `GET /api/v1/downloads/{job_id}/stream` via Server-Sent Events (SSE) to receive real-time JSON frames containing:
   - `status`: `PENDING` | `RUNNING` | `COMPLETED` | `FAILED`
   - `downloaded_bytes` / `total_bytes`
   - `percent_complete`
   - `speed_mbps`
   - `eta_seconds`
   - `current_file`
5. On completion, the dataset is registered with full provenance and is immediately selectable across analysis screens.
