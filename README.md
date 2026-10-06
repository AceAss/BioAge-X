# BioAge-X 🧬⏱️

> **"From molecular signals to biological age."**  
> An explainable multi-omics computational platform that estimates biological age from high-dimensional molecular profiles, benchmarks against canonical reference clocks, and investigates network interactomes associated with cellular senescence.

[![CI](https://github.com/AceAss/BioAge-X/actions/workflows/ci.yml/badge.svg)](https://github.com/AceAss/BioAge-X/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-teal.svg)](https://opensource.org/licenses/Apache-2.0)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2+-ee4c2c)](https://pytorch.org/)
[![Version: v1.0.0](https://img.shields.io/badge/Release-v1.0.0-emerald.svg)](https://github.com/AceAss/BioAge-X/releases)

---

## ⚠️ Important Scientific & Educational Disclaimer

**BioAge-X is strictly an academic computational biology research and discovery platform.**  
It is **NOT a clinical diagnostic system or medical device**. Biological age acceleration estimates reflect mathematical residuals under specific statistical assumptions and do not constitute clinical diagnosis, personalized disease prognosis, or therapeutic advice. All claims are partitioned according to the **BioAge-X Four-Tier Evidence Taxonomy**:
1. **COMPUTATIONAL OUTPUT**: Exact mathematical figures computed by algorithms.
2. **EXTERNAL BIOLOGICAL EVIDENCE**: Facts recorded in verified external databases (STRING, Reactome, Ensembl).
3. **MODEL-DERIVED HYPOTHESIS**: Plausible biological patterns suggested by statistical convergence.
4. **EXPERIMENTAL VALIDATION**: Wet-lab biological confirmations (not established by in silico software alone).

---

## 🔬 The Two-Phase Research Framework

BioAge-X operates a formal two-phase computational biology pipeline:

```
          MOLECULAR DATA (DNAm / RNA-seq / Proteomics / Metabolomics)
                                ↓
        ┌────────────────────────────────────────────────────────┐
        │                        PHASE 1                         │
        │      BIOAGE MULTI-OMICS BIOLOGICAL AGE PREDICTION      │
        └───────────────────────────┬────────────────────────────┘
                                    ↓
            Out-of-Fold Biological Age & Age Acceleration (Δ = ŷ - y)
                                    ↓
            Reference Clock Benchmarking (Horvath / Hannum / PhenoAge)
                                    ↓
            Explainable AI: Exact Shapley Additive Attributions (SHAP)
                                    ↓
            Candidate Aging-Associated Biomarkers (Robustness Score)
                                    ↓
        ┌────────────────────────────────────────────────────────┐
        │                        PHASE 2                         │
        │       GRAPHOMICS-AI BIOLOGICAL NETWORK BIOLOGY         │
        └───────────────────────────┬────────────────────────────┘
                                    ↓
            Ensembl Gene / UniProt Mapping & Coordinate Resolution
                                    ↓
            Human Interactome Construction (STRING DB v12.5 Edges)
                                    ↓
            Pathway Over-Representation (Reactome v97 & Hallmarks)
                                    ↓
            Graph Neural Networks (GNN): Node/Graph Age Learning
                                    ↓
            Topological Perturbation & Biomarker Stability Analysis
```

---

## 🌟 Core Features & Research Modules

### 1. 📥 Universal Biological Data Acquisition (12 Repositories)
Directly queries, streams, validates, and ingests biological datasets from 12 biological repositories:
- **Genomics & Epigenomics**: NCBI GEO (`GSE*`, `GPL*`, `GSM*`), NCBI SRA (`SRR*`), EMBL-EBI ENA (`PRJEB*`).
- **Functional Genomics**: EMBL-EBI ArrayExpress (`E-*`), EMBL-EBI BioStudies (`S-*`).
- **Cancer Multi-Omics**: NCI Genomic Data Commons (GDC / TCGA open-access STAR counts & clinical tables).
- **Proteomics & Metabolomics**: EMBL-EBI PRIDE (`PXD*`), ProteomeXchange, EMBL-EBI MetaboLights (`MTBLS*`).
- **Direct Web & Manifests**: Generic HTTP/HTTPS URL streaming and Multi-Omics YAML/JSON Manifest assemblers.
- **Security & Guardrails**: Defends against ZipSlip directory traversal (`../../`), decompresses safely with 10 GB limits, and flags controlled-access BAM files with `ACCESS RESTRICTED`.

### 2. Tabular Biological Age Models & Epigenetic Clocks
- **Predictive Algorithms**: ElasticNet (with internal $\alpha$-CV), Random Forest, XGBoost, and Multi-Omics Early/Late Fusion.
- **Reference Clocks**: Canonical mathematical implementations of Horvath Pan-Tissue (2013 piecewise anti-log), Hannum Blood (2013 linear scoring), and Levine PhenoAge (2018).
- **3rd-Gen Compatibility Engine**: Formal audits for GrimAge and DunedinPACE returning `PARTIAL_COVERAGE` or `UNAVAILABLE` without ever fabricating missing clinical surrogates or probes.

### 3. Statistical Uncertainty & Research Rigor
- **95% Bootstrap Confidence Intervals**: Empirical bootstrap resamples ($B=1000$) for MAE, RMSE, and $R^2$.
- **Cross-Validation Distributions**: Preserves complete fold-by-fold metrics (`Fold 1` through `Fold K`) to eliminate aggregate score opacity.
- **Age-Bias Analysis**: Stratifies predictions across Young ($<40\text{ y}$), Middle ($40-65\text{ y}$), and Older ($>65\text{ y}$) bins to diagnose regression toward the mean.
- **External Validation**: Dedicated workflow training on Cohort A → testing on Cohort B without model retraining, coupled with Kolmogorov-Smirnov demographic and molecular dataset shift tests.

### 4. Candidate Biomarker & Network Robustness
- **Biomarker Robustness Score**: Mathematical composite: $\text{Score} = 0.40 \cdot \text{FoldFreq} + 0.35 \cdot \text{DirConsistency} + 0.25 \cdot \text{NormSHAP}$. Separates *Highly Stable* features from *Single-Experiment Candidates*.
- **Annotation Provenance**: Strict biological lineage resolution ($\text{CpG} \rightarrow \text{Gene} \rightarrow \text{Ensembl} \rightarrow \text{STRING} \rightarrow \text{Reactome}$). Distinguishes *Direct Mapping* from *Inferred Association* and *No Mapping Available*.
- **Network Perturbation**: Sweeps edge confidence thresholds (400, 700, 900) to quantify topological hub stability.

### 5. Optional Gemini AI Research Assistant
- **Evidence-Constrained**: Operates strictly downstream of computational outputs.
- **Zero Hallucination Policy**: Strictly forbidden from inventing biomarkers, fabricating citations, or altering statistics.
- **Structured Schema**: Partitioned into `summary`, `observations`, `hypotheses`, `limitations`, and `evidence_sources`.
- **Keyless Resilience**: 100% functional without API keys; deterministic rule-based summaries are rendered if disabled.

---

## 🚀 Quick Start

### 1. Backend Setup (Python 3.10 - 3.12)

```bash
# Clone the repository
git clone https://github.com/AceAss/BioAge-X.git
cd BioAge-X

# Install dependencies
pip install -r requirements.txt

# (Optional) Copy environment template - runs 100% keylessly by default!
cp .env.example .env

# Generate synthetic demo cohort and public benchmark
python scripts/generate_demo_data.py
python scripts/create_public_benchmarks.py

# Launch FastAPI backend server (Port 8000)
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup (Node.js 18+)

```bash
cd apps/frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🧪 Testing & Verification

BioAge-X enforces exhaustive automated testing across all scientific and software layers:

```bash
# Run full backend test suite (102 tests)
pytest tests/ -v

# Run Next.js static build check (22 routes)
cd apps/frontend
npm run build
```

---

## 🗺️ Research Workspace Sitemap

| Route | Scientific Purpose |
| :--- | :--- |
| `/dashboard` | Two-Phase executive research overview, hypothesis cards, and KPI metrics |
| `/datasets/explorer` | Universal Biological Data Acquisition across 12 global repositories |
| `/datasets` | Multi-omics matrix ingestion (Demo, GSE40279, Custom Upload) and profiling |
| `/benchmarks` | Reference clock benchmarking (Horvath, Hannum, PhenoAge, GrimAge audit) |
| `/analysis` | 12-Step reproducible research workflow wizard |
| `/models` | Model benchmark comparisons with 95% bootstrap confidence intervals |
| `/explainability` | Exact Shapley additive explanations (SHAP beeswarm and waterfalls) |
| `/biomarkers` | Candidate Aging-Associated Biomarkers directory and Robustness Scores |
| `/network` | Interactive Cytoscape.js biological interactome with STRING database edges |
| `/gnn` | GCN, GraphSAGE, and GAT node/graph regression lab |
| `/pathways` | Reactome pathway over-representation analysis against explicit gene universes |
| `/experiments` | Experiment tracking history with SHA-256 configuration fingerprints |
| `/experiments/compare` | Side-by-side scientific experiment comparison workspace |
| `/experiments/ablation` | Formal ablation studies (Modality, Fusion, Features, GNN Interactome) |
| `/limitations` | Methodological constraints, non-causal boundaries, and tissue specificity |
| `/reports` | 24-Section manuscript-style research reports and publication figure exports |
| `/integrations` | External service health matrix (STRING, Reactome, Ensembl, NCBI, Gemini) |
| `/settings` | System diagnostics, engine health checks, and scientific disclaimers |

---

## 📜 Citation

If you use BioAge-X in your academic research or teaching, please cite:

```bibtex
@software{bioage_x_2026,
  author = {BioAge-X Research Collective},
  title = {BioAge-X: Explainable Multi-Omics Biological Age Estimation & Network Biology Platform},
  year = {2026},
  url = {https://github.com/AceAss/BioAge-X},
  version = {1.0.0}
}
```

---

## 📄 License

BioAge-X is licensed under the [Apache 2.0 License](LICENSE).
