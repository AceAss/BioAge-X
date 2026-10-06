# Biological Data Repository Connectors: Capability Matrix & Provider Specification

## 1. Universal Repository Coverage

BioAge-X integrates 12 biological data repository connectors spanning genomics, transcriptomics, epigenetics, proteomics, metabolomics, cancer multi-omics, and custom public data feeds.

| Provider Code | Repository Name | Biological Focus | Default Accession Pattern | Search API Status | Download Support | Preprocessing Flag | Restricted Access Guardrail |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GEO` | NCBI Gene Expression Omnibus | Epigenetics (450K/EPIC) & Microarray / RNA-seq | `^GSE\d+`, `^GPL\d+`, `^GSM\d+` | Live / Curated Fallback | Matrix CSV/TSV, Series Matrix | None (Ready for ML) | Public Domain |
| `SRA` | NCBI Sequence Read Archive | Raw Sequencing Reads (DNA/RNA-seq) | `^[SEDR]R[XRAS]\d+`, `^PRJNA\d+` | Live / Curated Fallback | Run Info, SRA Runs | **REQUIRES PREPROCESSING** | Public Domain |
| `ENA` | EMBL-EBI European Nucleotide Archive | Open Raw Reads & Assemblies | `^PRJEB\d+`, `^ERP\d+`, `^ER[XRS]\d+` | Live / Curated Fallback | FASTQ, BAM, Run Tables | **REQUIRES PREPROCESSING** | Public Domain |
| `ArrayExpress`| EMBL-EBI ArrayExpress | Functional Genomics & Gene Expression | `^E-[A-Z]+-\d+` | Live / Curated Fallback | SDRF Metadata, Expression CSV | None (Ready for ML) | Public Domain |
| `BioStudies` | EMBL-EBI BioStudies | Biomolecular & Multi-Modal Studies | `^S-[A-Z]+-\d+`, `^S-BSST\d+` | Live / Curated Fallback | Study Archive, Tables | None (Ready for ML) | Public Domain |
| `GDC` | NCI Genomic Data Commons | Cancer Multi-Omics & Clinical Records | `^TCGA-[A-Z]+`, `^TARGET-[A-Z]+` | Live / Curated Fallback | STAR Counts, Clinical TSV | Age conversion (days -> yrs) | **ACCESS RESTRICTED** (Controlled BAMs) |
| `TCGA` | The Cancer Genome Atlas (Facade) | Pan-Cancer Genomics & Aging Clocks | `^TCGA-[A-Z]+` | Facade over GDC | STAR Counts, Clinical TSV | Age conversion (days -> yrs) | **ACCESS RESTRICTED** (Controlled BAMs) |
| `PRIDE` | EMBL-EBI PRIDE Proteomics | Mass Spectrometry Proteomics | `^PXD\d+`, `^PRD\d+` | Live / Curated Fallback | Quantified Abundance Matrix | None (Quant Matrix) | Public Domain |
| `ProteomeXchange` | ProteomeXchange Consortium | Multi-Repository Proteomics | `^PXD\d+` | Facade over PRIDE | Quantified Abundance Matrix | None (Quant Matrix) | Public Domain |
| `MetaboLights` | EMBL-EBI MetaboLights | Metabolomics & Metabolic Profiling | `^MTBLS\d+` | Live / Curated Fallback | MAF Metabolite Quant Matrix | None (Quant Matrix) | Public Domain |
| `GenericURL` | Public HTTPS/HTTP Importer | Arbitrary Web-Hosted Matrices | `^https?://.*` | Direct URL Parsing | Streaming Stream / Auto-detect | Auto-validated | N/A |
| `Manifest` | Multi-Omics Manifest Importer | Multi-Assay Cohort Definitions | `^.*\.ya?ml$`, `^.*\.json$` | Manifest Parser | Multi-Layer Assembly | Auto-aligned | N/A |

---

## 2. Detailed Provider Specifications

### 2.1 GEO Provider (`bioage.acquisition.providers.geo`)
- **Primary Use Case**: Ingestion of Illumina HumanMethylation450 and MethylationEPIC beta-value matrices and microarray/RNA-seq gene expression matrices.
- **Key Accessions**: `GSE40279` (Hannum whole-blood 450K benchmark), `GSE87571` (Johansson whole-blood 450K), `GSE74193` (Prefrontal cortex brain aging), `GSE107690` (Monocyte epigenetics).
- **Download Modes**: Curated Series Matrix, Supplementary Files, Phenotype Table.
- **Scientific Integrity**: Beta values are checked for valid bounds $[0, 1]$; chronological age is mapped from sample characteristics.
- **NCBI API Key & Rate Limiting (`NCBI_API_KEY`)**:
  - **Keyless (Default)**: Limits requests to **3 requests/second** in compliance with NCBI E-utilities public policy. No account or key is required.
  - **With `NCBI_API_KEY`**: Increases permitted request throughput to **10 requests/second**.
  - **Security**: The key is stored purely on the backend and is never exposed to the frontend or included in API responses.


### 2.2 SRA & ENA Providers (`bioage.acquisition.providers.sra`, `bioage.acquisition.providers.ena`)
- **Primary Use Case**: Discovery and retrieval of raw sequencing read archives (FASTQ, SRA format).
- **Guardrail**: Raw read sequencing files are explicitly tagged with `REQUIRES PREPROCESSING: Raw sequencing reads require quality trimming (FastQC/Trimmomatic), alignment (STAR/Hisat2/Bismark), and quantification (featureCounts/Salmon) before ingestion into biological age models.`
- **Preventing False Claims**: The system refuses to feed raw binary reads directly into tabular regression clocks, preserving scientific honesty.

### 2.3 GDC & TCGA Providers (`bioage.acquisition.providers.gdc`, `bioage.acquisition.providers.tcga`)
- **Primary Use Case**: Cancer transcriptomics and DNA methylation matched to clinical survival, staging, and diagnostic chronological age.
- **Curated Cohorts**: `TCGA-BRCA` (Breast invasive carcinoma, 1098 samples), `TCGA-LUAD` (Lung adenocarcinoma, 585 samples).
- **Access Guardrail**: 
  - Open Access STAR-counts expression matrices and clinical diagnostic data are downloaded freely.
  - High-throughput whole-genome BAMs and germline variant calls are marked **ACCESS RESTRICTED**. Attempts to download without an authenticated dbGaP authorization token raise explicit permission errors rather than fabricating download progress.

### 2.4 PRIDE & ProteomeXchange Providers (`bioage.acquisition.providers.pride`, `bioage.acquisition.providers.proteomexchange`)
- **Primary Use Case**: High-throughput mass spectrometry proteomics datasets investigating plasma and tissue proteomic aging markers.
- **Accessions**: `PXD014943` (Human plasma proteome profiling across the lifespan), `PXD000001` (Benchmark proteomics cohort).
- **Quantification**: Extracts quantified protein abundance tables, identifying UniProt accession numbers and mapping them to HGNC gene symbols for network integration.

### 2.5 MetaboLights Provider (`bioage.acquisition.providers.metabolights`)
- **Primary Use Case**: Untargeted and targeted metabolomics profiling across age cohorts.
- **Accessions**: `MTBLS1000` (Human serum metabolic profiling across adult lifespan), `MTBLS100` (Metabolic alteration profiles).
- **Data Tiers**: Extracts Metabolite Assignment Files (MAF) and normalized concentration matrices with ChEBI and HMDB metabolite identifiers.

### 2.6 Generic URL Provider (`bioage.acquisition.providers.generic_url`)
- **Primary Use Case**: Downloading custom researcher cohorts hosted on institutional servers, AWS S3, Google Cloud Storage, or Zenodo/Figshare repositories.
- **Automatic Validation**: Validates HTTP headers, performs safe chunked streaming, extracts compressed archives, and initiates immediate format inspection via `DatasetValidator`.

### 2.7 Multi-Omics Manifest Importer (`bioage.acquisition.providers.manifest`)
- **Primary Use Case**: Integrating heterogeneous multi-assay cohorts (e.g., matching DNA methylation, transcriptomics, proteomics, and clinical variables across distinct files).
- **Assembly Strategy**: Supports both strict intersection matching (only individuals with all assays) and outer union merging (retaining all individuals).
