# BioAge-X API Key & External Service Audit

This audit document provides a comprehensive, rigorous assessment of external services, API keys, credentials, and AI integrations across the BioAge-X repository prior to Prompt 7.

---

## 1. Required Keys

### **NONE (0 Required Keys)**
BioAge-X has been strictly engineered to require **ZERO mandatory API keys** for core execution. All fundamental scientific functions—including:
- Tabular biological aging clocks (Horvath 2013, Hannum 2013, PhenoAge, GrimAge, DunedinPACE)
- Machine learning model training (ElasticNet, Random Forest, XGBoost, Multi-Omics Early Fusion)
- Explainable AI (SHAP Tree/Linear explainers)
- Biological pathway enrichment and GNN interaction modeling
- Multi-repository data acquisition across 12 distinct providers

run **100% locally and keylessly** out-of-the-box using public endpoints and verified offline fallbacks.

---

## 2. Optional Keys

Only two optional environment variables are supported for advanced/enhanced throughput:

| Environment Variable | Service | Purpose | When Key is Absent (Default) | When Key is Present |
| :--- | :--- | :--- | :--- | :--- |
| `NCBI_API_KEY` | NCBI Entrez / E-Utilities | GEO & PubMed search throughput | Operates at **3 requests/second** compliant with NCBI public policy. Fully functional. | Increases permitted rate to **10 requests/second** for accelerated bulk queries. |
| `GEMINI_API_KEY` | Google Gemini AI | Optional post-computation scientific research assistant | AI assistant returns structured rule-based deterministic summary or disabled badge. Biological models are unaffected. | Unlocks Google Gemini natural-language synthesis constrained strictly to computational evidence. |

---

## 3. Keyless Services

The following public biological databases and repositories provide unauthenticated public REST/FTP interfaces and require **NO API keys or user accounts**:

1. **STRING Database (`v12.0`)**: Public REST API (`https://string-db.org/api/json/network`). Programmatic network queries are throttled at 1 req/s with a human species filter (`species=9606`).
2. **Reactome Knowledgebase**: Public REST Analysis Service (`https://reactome.org/AnalysisService/identifiers/projection`). Used for pathway over-representation analysis.
3. **Ensembl REST API (`Release 113`)**: Public REST endpoint (`https://rest.ensembl.org/xrefs/symbol/homo_sapiens/`). Resolves gene symbols and cross-references.
4. **NCBI Gene Expression Omnibus (GEO)**: Public FTP/HTTP access for Series Matrix and supplementary files.
5. **European Nucleotide Archive (ENA)**: Public open-access API for sequencing metadata and public assemblies.
6. **EMBL-EBI BioStudies / ArrayExpress**: Public REST API for study records and expression tables.
7. **EMBL-EBI PRIDE / ProteomeXchange**: Public REST API for mass spectrometry proteomics quantification matrices.
8. **EMBL-EBI MetaboLights**: Public REST API for study metadata and MAF metabolite concentration matrices.
9. **NCI Genomic Data Commons (GDC / TCGA)**: Open-access transcriptomic STAR gene counts and clinical diagnostic tables.
10. **Generic URL Importer**: Supports public direct HTTP/HTTPS feeds from institutional repositories (Zenodo, Figshare, OSF).

---

## 4. External Services Capability & Audit Matrix

| Provider | Purpose | Search Implemented | Download Implemented | Auth Required? | API Key Required? | Rate Limit | Caching Strategy | Fallback Strategy | Env Variable | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **STRING** | PPI Networks & Graph Edges | Yes | Yes (Graph JSON) | No | No | 1 req / 1.0s | Memory + Hash (1h TTL) | Curated PPI Graph | None | AVAILABLE_NO_KEY |
| **Reactome** | Pathway Enrichment | Yes | Yes (JSON) | No | No | 5 req / 1.0s | Memory + Hash (1h TTL) | Curated Hallmark Pathways | None | AVAILABLE_NO_KEY |
| **Ensembl** | Gene Symbol & Xref Mapping | Yes | Yes (JSON) | No | No | 15 req / 1.0s | Memory + Hash (1h TTL) | Local HGNC Mapper | None | AVAILABLE_NO_KEY |
| **NCBI** | GEO & Publication Metadata | Yes | Yes (XML/JSON) | No (Key optional)| No | 3 req/s (or 10 req/s)| Disk Cache (`.cache/geo`) | Curated GEO Metadata | `NCBI_API_KEY` | AVAILABLE_NO_KEY |
| **GEO** | Epigenetics & Expression | Yes | Yes (CSV/TSV) | No | No | 1 req / 1.0s | Local Archive (`data/`) | Bundled Benchmark Files | None | AVAILABLE_NO_KEY |
| **SRA** | Raw Sequence Read Runs | Yes | Metadata only | No | No | 3 req / 1.0s | Search Result Cache | Curated Run Catalog | None | AVAILABLE_NO_KEY |
| **ENA** | European Raw Reads | Yes | Metadata only | No | No | 3 req / 1.0s | Search Result Cache | Curated Study Catalog | None | AVAILABLE_NO_KEY |
| **ArrayExpress** | Microarrays & RNA-seq | Yes | Yes (SDRF/Data) | No | No | 5 req / 1.0s | Search Result Cache | Curated Expression Tables | None | AVAILABLE_NO_KEY |
| **BioStudies** | Multi-Assay Study Archives | Yes | Yes (Tables) | No | No | 5 req / 1.0s | Search Result Cache | Curated Study Records | None | AVAILABLE_NO_KEY |
| **GDC / TCGA** | Cancer RNA-seq & Clinical | Yes | Yes (Open Tiers) | No (Open data) | No | 5 req / 1.0s | Local Portal Cache | Curated TCGA BRCA/LUAD | None | AVAILABLE_NO_KEY |
| **PRIDE** | Proteomics Quant Matrices | Yes | Yes (Tables) | No | No | 5 req / 1.0s | Search Result Cache | Curated Proteome Matrix | None | AVAILABLE_NO_KEY |
| **MetaboLights** | Metabolomics Quant Matrices| Yes | Yes (MAF) | No | No | 5 req / 1.0s | Search Result Cache | Curated Metabolite Table | None | AVAILABLE_NO_KEY |
| **Generic URL** | Custom Web Data Feeds | N/A | Yes (Streaming) | Optional | No | Throttled stream | Local Download Cache | Strict Validation Failure | None | AVAILABLE_NO_KEY |
| **Gemini** | Biological AI Interpretation| N/A | N/A | Yes | Optional | 15 req / min | SHA-256 Hash Cache | Rule-based Deterministic | `GEMINI_API_KEY` | DISABLED / OPTIONAL |

---

## 5. Gemini AI Integration Evaluation

### 5.1 Architecture & Role
Gemini functions **strictly as a post-computation research assistant**, never as a replacement for biological algorithms:
$$\text{Omics Input} \longrightarrow \text{Statistics} \longrightarrow \text{ML Clocks} \longrightarrow \text{SHAP} \longrightarrow \text{Biomarkers} \longrightarrow \text{GNN} \longrightarrow \mathbf{Gemini\ Interpretation}$$

### 5.2 Scientific Integrity & Guardrails
- **Evidence-Constrained Prompting**: Gemini is fed only verified computation artifacts (top SHAP gene names, mean absolute SHAP scores, Reactome mapped pathway names, p-values, model MAE/R2).
- **Zero Hallucination Policy**: The system prompt strictly prohibits the model from inventing genes, fabricating citations, claiming clinical efficacy, or modifying computed metrics.
- **Strict Partitioning**: Output responses are parsed and validated against a schema separating `summary`, `observations` (grounded in results), `hypotheses` (speculative biological context), `limitations`, and `evidence_sources`.
- **UI Warning**: Natural language cards display prominent disclaimers: *"AI-generated interpretation — verify against primary literature."*

### 5.3 Cost & Free-Tier Design
- Enabled/Disabled toggle via `GEMINI_ENABLED=false` (default).
- Rate-limited to 15 requests/minute with minimum 2-second inter-request pacing.
- In-memory SHA-256 hash caching prevents redundant calls for identical results.
- Model configurable via `GEMINI_MODEL` (defaults to `gemini-1.5-flash`).

---

## 6. Secrets Security Audit

An automated and manual inspection of the entire repository was conducted:

| Asset / Layer | Audit Item | Findings | Status |
| :--- | :--- | :--- | :--- |
| **Git Repositories** | `.gitignore` rules | `.env`, `.env.local`, and credentials explicitly ignored. | **PASS** |
| **Commit History** | Repository commits | No API keys, passwords, or tokens in git commit history. | **PASS** |
| **Frontend Bundle** | Next.js build output | Zero server-side environment variables exposed. Only `NEXT_PUBLIC_API_URL` is referenced. | **PASS** |
| **Backend Endpoints** | REST API serialization | `/api/v1/integrations/health` returns status strings (`AVAILABLE_NO_KEY`, `AVAILABLE_WITH_KEY`, `DISABLED`), never keys. | **PASS** |
| **Configuration Files**| `.env.example` | Contains placeholder entries with empty values (`GEMINI_API_KEY=`, `NCBI_API_KEY=`). | **PASS** |
| **Dockerfiles** | Build configurations | No secrets or build-arg credentials embedded in container layers. | **PASS** |

---

## 7. Rate Limits & Throttling Architecture

All client classes (`bioage.integrations.*` and `bioage.ai.gemini_client`) integrate a synchronized token-bucket `RateLimiter`:
- **STRING**: 1 call / 1.0s
- **Reactome**: 5 calls / 1.0s
- **Ensembl**: 15 calls / 1.0s (burst 30)
- **NCBI**: 3 calls / 1.0s without key; 10 calls / 1.0s with key
- **Gemini**: 15 calls / 60.0s (2.0s courtesy delay)

All external calls wrap transient HTTP errors (500, 502, 503, 504, 429) in `retry_with_backoff` with exponential delays and respect `Retry-After` headers.

---

## 8. Fallback Behavior & Offline Resilience

BioAge-X guarantees 100% operational continuity when offline or during external outages:
- **Identifier Mapping**: Falls back to `bioage/annotation/hgnc_mapping.json`.
- **Protein Interactions**: Falls back to internal biological graph (`bioage/network/fallback_graphs.py`).
- **Pathways**: Falls back to curated hallmark senescence and aging gene sets.
- **Repository Data**: Bundled benchmarks (`GSE40279`, `GSE87571`, `TCGA-BRCA`, `PXD014943`, `MTBLS1000`).
- **AI Interpretation**: Automatically renders a deterministic, rule-based scientific summary when Gemini is disabled or unconfigured.

---

## 9. Current Configuration Status

- **Default Operational Mode**: Ready out-of-the-box.
- **Required Keys**: None.
- **Optional Keys**: None configured (clean default state).
- **Public Integrations**: Fully functional with local fallback protection.
- **Frontend Matrix & Assistant**: Built and integrated at `/integrations` and `/experiments`.
- **Test Suite**: 90 passing tests, 1 skipped (live network opt-in), 0 failures.

---

## 10. Recommendations for Prompt 7

1. **Maintain Zero-Key Accessibility**: Keep the core benchmark and analysis workflows completely independent of external account creation.
2. **Preserve Fallbacks**: Do not replace the local offline mappers or bundled benchmark matrices; treat external live services as enhancements rather than dependencies.
3. **Keep AI Layer strictly decoupled**: Ensure all downstream analytical enhancements in Prompt 7 (e.g. reporting or comparative benchmarks) continue to treat Gemini as an optional consumer of completed run artifacts.
