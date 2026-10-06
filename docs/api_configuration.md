# BioAge-X External API & Service Configuration Guide

This document specifies the operational configuration, authentication requirements, rate limits, caching mechanisms, fallback behaviors, and security protocols for all external biological repositories and computational services integrated into BioAge-X.

---

## 1. Quick Reference: Service & Credential Matrix

| Provider / Service | Primary Purpose | Authentication | Credential Status | Env Variable | Default Rate Limit | Caching Mechanism | Fallback Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **STRING** | Protein-protein interaction networks | None (Public REST) | **NOT REQUIRED** | None | 1 req / 1.0s | In-memory + Hash (1h TTL) | Curated PPI Graph Fallback |
| **Reactome** | Pathway enrichment analysis | None (Public REST) | **NOT REQUIRED** | None | 5 req / 1.0s | In-memory + Hash (1h TTL) | Curated Pathway Sets |
| **Ensembl** | Gene symbol & cross-reference resolution | None (Public REST) | **NOT REQUIRED** | None | 15 req / 1.0s (burst 30) | In-memory + Hash (1h TTL) | HGNC Local Offline Mapper |
| **NCBI E-Utilities** | GEO metadata & publication search | Optional | **OPTIONAL** | `NCBI_API_KEY` | 3 req/s (no key) / 10 req/s (with key) | Disk cache (`.cache/geo/`) | Curated GEO Study Manifests |
| **GEO** | Epigenetic & transcriptomic datasets | None (Public FTP/HTTP)| **NOT REQUIRED** | None | Courtesy pacing (1s) | Disk cache (`data/external/`) | Curated benchmark matrices |
| **SRA / ENA** | Raw read archive search & metadata | None (Public REST) | **NOT REQUIRED** | None | 3 req / 1.0s | Provider Search Cache | Curated Run Info Manifests |
| **ArrayExpress / BioStudies** | Functional genomics & study metadata | None (Public REST) | **NOT REQUIRED** | None | 5 req / 1.0s | Provider Search Cache | Curated Expression Tables |
| **GDC / TCGA** | Open cancer transcriptomics & clinical data | None (Open endpoints) | **NOT REQUIRED** (Open data) | None | 5 req / 1.0s | GDC Portal Cache | Curated TCGA Cohorts (BRCA/LUAD) |
| **PRIDE / ProteomeXchange** | Mass-spectrometry proteomics | None (Public REST) | **NOT REQUIRED** | None | 5 req / 1.0s | PRIDE Search Cache | Curated Proteome Matrix |
| **MetaboLights** | Serum & tissue metabolomics | None (Public REST) | **NOT REQUIRED** | None | 5 req / 1.0s | MetaboLights Cache | Curated MAF Abundance Table |
| **Generic URL Importer**| Custom laboratory HTTP/HTTPS data feeds| Optional HTTP Basic | **NOT REQUIRED** (Public) | None | Connection pacing | Streaming chunk cache | Validator Rejection |
| **Google Gemini AI**| Optional biological research interpretation | API Key | **OPTIONAL** | `GEMINI_API_KEY` | 15 req/min (Free Tier) | In-memory SHA-256 cache | Deterministic Rule-Based Summary |

---

## 2. Detailed Service Specifications

### 2.1 STRING Database (v12.0)
- **Purpose**: Retrieval of functional and physical protein-protein interaction (PPI) networks to construct graph representations for Graph Neural Networks (GNNs).
- **Endpoint**: Versioned stable REST endpoint: `https://string-db.org/api/json/network`
- **Authentication**: Keyless public access. STRING does not mandate user accounts or API keys for programmatic batch queries.
- **Required Parameters**:
  - `identifiers`: List of mapped HGNC gene symbols (e.g., `ELOVL2`, `FHL2`, `PENK`).
  - `species`: Fixed to `9606` (Homo sapiens).
  - `caller_identity`: `bioage_x_v1` (responsible user-agent identification).
- **Throttling & Batching**: Maximum 1 request per second (`RateLimiter(calls=1, period=1.0)`). Batch size capped at 50 identifiers per call to prevent unbounded network growth.
- **Provenance Recorded**: STRING database release version (`v12.0`), retrieval timestamp (UTC), confidence threshold (`required_score=400`), and raw interaction count.
- **Offline Fallback**: Pre-indexed internal biological graph containing canonical human senescence and aging interactors (`bioage/network/fallback_graphs.py`).

### 2.2 Reactome Pathway Knowledgebase
- **Purpose**: Over-representation analysis (ORA) mapping candidate age-associated biomarkers to biological pathways (e.g., Cellular Senescence, DNA Double-Strand Break Repair, Telomere Maintenance).
- **Endpoint**: `https://reactome.org/AnalysisService/identifiers/projection`
- **Authentication**: Keyless public access. No API key required.
- **Rate Limits**: 5 requests per second courtesy limit.
- **Provenance Recorded**: Reactome release version, timestamp, entities mapped, and statistical p-values.
- **Offline Fallback**: Curated hallmark aging pathway sets bundled with the BioAge-X distribution.

### 2.3 Ensembl REST API
- **Purpose**: Resolution of gene identifiers across Ensembl Gene IDs, HGNC symbols, NCBI Gene IDs, and UniProt accessions.
- **Endpoint**: `https://rest.ensembl.org/xrefs/symbol/homo_sapiens/`
- **Authentication**: Keyless public access. No API key required.
- **Rate Limits**: 15 requests/second with burst support up to 30 requests/second. Complies with Ensembl's `Retry-After` HTTP headers upon 429 status codes.
- **Offline Fallback**: Curated static mapping table (`bioage/annotation/hgnc_mapping.json`).

### 2.4 NCBI E-Utilities & GEO
- **Purpose**: Discovery, search, and metadata parsing for Gene Expression Omnibus (GEO) accessions and PubMed literature references.
- **Endpoint**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`
- **Authentication**: **OPTIONAL API KEY**.
  - **Without API Key**: The service automatically limits requests to **3 requests per second** in strict adherence to NCBI public usage guidelines.
  - **With API Key (`NCBI_API_KEY`)**: The service increases throughput to **10 requests per second**.
- **Configuration**: Set `NCBI_API_KEY=<your_ncbi_key>` in `.env`.
- **Frontend Exposure**: Strictly isolated. The key is never returned by any REST API endpoint or passed to the browser.
- **Offline Fallback**: Local curated catalog of GEO aging datasets (`GSE40279`, `GSE87571`, `GSE74193`, etc.) and bundled Series Matrix files.

### 2.5 Multi-Omics Repository Providers (ENA, BioStudies, PRIDE, MetaboLights, GDC)
- **ENA / SRA**: Keyless public REST access. SRA runs and FASTQ files trigger an explicit `REQUIRES PREPROCESSING` flag to prevent feeding unaligned reads into tabular clocks.
- **ArrayExpress / BioStudies**: Keyless public REST access for expression matrices and SDRF files.
- **PRIDE / ProteomeXchange**: Keyless public REST access for quantified peptide/protein tables.
- **MetaboLights**: Keyless public REST access for MAF metabolite concentration matrices.
- **GDC / TCGA**:
  - Open-access transcriptomic STAR-counts and clinical diagnostic data: Keyless public access.
  - Controlled-access data (raw whole-genome BAMs, germline variants): Throws `PermissionError: ACCESS RESTRICTED` requiring dbGaP tokens. BioAge-X never falsely marks controlled data as downloaded.

### 2.6 Google Gemini AI Research Assistant
- **Purpose**: Optional post-computation scientific interpretation layer for experiment metrics, SHAP feature rankings, and pathway enrichment.
- **Endpoint**: Google Generative AI API (`gemini-1.5-flash` by default).
- **Authentication**: **OPTIONAL API KEY**.
- **Environment Variables**:
  - `GEMINI_API_KEY`: API key obtained from Google AI Studio.
  - `GEMINI_MODEL`: Model identifier (defaults to `gemini-1.5-flash`).
  - `GEMINI_ENABLED`: Explicit boolean flag (`true` or `false`). Defaults to `false`.
- **Safety Architecture**:
  - Gemini executes **exclusively after** all biological calculations, statistics, ML models, and GNNs complete.
  - Evidence-constrained prompt forcing strict grounding on supplied experiment artifacts.
  - Strict JSON schema separating `summary`, `observations`, `hypotheses`, `limitations`, and `evidence_sources`.
  - Zero hallucinations allowed: The model is forbidden from inventing biomarkers, creating fake statistics, or modifying computed outputs.
- **Cost / Free-Tier Management**:
  - If `GEMINI_ENABLED=false` or no key is provided, the entire scientific pipeline continues without interruption.
  - In-memory SHA-256 caching ensures identical queries do not trigger repeated API calls.
  - Throttled to 15 requests per minute with courtesy delays.

---

## 3. Secrets Security & Isolation Policy

BioAge-X adheres to a zero-secrets-leakage design:

1. **Git Isolation**:
   - `.env`, `.env.local`, and all variations are explicitly ignored by `.gitignore`.
   - `.env.example` contains only template definitions with empty values.
2. **Frontend Isolation**:
   - No secret environment variables use the `NEXT_PUBLIC_` prefix.
   - The frontend communicates only with the backend API (`http://localhost:8000/api/v1`).
   - The health endpoint (`/api/v1/integrations/health`) returns status enumerations (`AVAILABLE_NO_KEY`, `AVAILABLE_WITH_KEY`, `DISABLED`), never secrets or masked tokens.
3. **Log & Response Sanitization**:
   - API logging middleware and error handlers redact sensitive headers and environment variables.

---

## 4. Setting Up Your Environment

To configure your environment:

1. Copy the template file:
   ```bash
   cp .env.example .env
   ```
2. For basic operation, **no modifications are needed**. BioAge-X will function immediately using public keyless APIs and offline fallbacks.
3. (Optional) To enable higher NCBI throughput:
   ```env
   NCBI_API_KEY=your_ncbi_api_key_here
   ```
4. (Optional) To enable the Gemini AI Research Assistant:
   ```env
   GEMINI_ENABLED=true
   GEMINI_API_KEY=your_google_ai_studio_key_here
   GEMINI_MODEL=gemini-1.5-flash
   ```
