# BioAge-X Data Card

## 1. Dataset Overview & Scope
BioAge-X processes high-dimensional biological data across genomics, epigenomics (DNA methylation), transcriptomics (RNA-seq / microarrays), proteomics (mass-spec), and metabolomics to model biological age and molecular senescence.

| Dataset Identifier | Primary Modality | Organism / Tissue | Sample Size (N) | Feature Space (P) | Accession / Source | Access Type |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GSE40279** (Hannum Benchmark) | Illumina 450K DNA Methylation | *Homo sapiens* (Whole Blood) | 80 samples | 71 benchmark CpGs | NCBI GEO `GSE40279` | Public Domain |
| **GSE87571** | Illumina 450K DNA Methylation | *Homo sapiens* (Whole Blood) | 729 samples | 450,000 CpGs | NCBI GEO `GSE87571` | Public Domain |
| **TCGA-BRCA** | RNA-seq STAR Counts + Methylation | *Homo sapiens* (Breast Primary) | 1,098 samples | 20,531 transcripts | NCI GDC Portal | Open Tier |
| **PXD014943** | Mass Spectrometry Proteomics | *Homo sapiens* (Human Plasma) | 4,263 samples | 2,925 proteins | EMBL-EBI PRIDE | Public Domain |
| **MTBLS1000** | Targeted/Untargeted Metabolomics | *Homo sapiens* (Human Serum) | 1,200 samples | 630 metabolites | EMBL-EBI MetaboLights | Public Domain |
| **Synthetic Demo Cohort** | In Silico Multi-Omics | Simulated Human Aging | 150 samples | 270 features | `data/example/demo_multiomics.csv` | Bundled Synthetic |

---

## 2. Ingestion & Format Specifications
BioAge-X supports universal orientation detection and multiple serialization formats:
- **Matrix Orientations**: 
  - `samples_by_features`: Standard machine learning layout ($N \times P$).
  - `features_by_samples`: Canonical microarray format ($P \times N$). Automatically transposed with sample/feature ID preservation.
- **File Types**: Delimited text (`CSV`, `TSV`), columnar binary (`Parquet`), and single-cell/annotated matrix (`AnnData H5AD`).
- **Validation Engine**: Pre-ingestion validation executes range checks, missingness profiling, zero-variance probe filtering, and chronological age column auto-discovery.

---

## 3. Preprocessing & Normalization Protocols
- **DNA Methylation Beta Values**:
  - Bound checking: Clipped strictly to biological interval $[0.0, 1.0]$.
  - Probe filtering: Probes with $>10\%$ missingness across the cohort are excluded.
  - Imputation: Median imputation fitted **strictly on training partitions** to guarantee zero data leakage.
- **Transcriptomics**:
  - Expression threshold: Features with $<1.0\text{ CPM}$ in $<10\%$ of samples are pruned.
  - Library-size normalization: Reads normalized to Counts Per Million (CPM).
  - Variance stabilization: Transformed via $\log_2(\text{CPM} + 1)$.

---

## 4. Known Biases & Biological Limitations
1. **Tissue Heterogeneity**: Models calibrated on whole-blood leukocyte composites (such as Hannum) capture immune cell-type shifts that cannot be generalized to neurological or solid organ tissues.
2. **Cross-Sectional Confounding**: Public cohorts represent single-timepoint samples. Observed age differences reflect cross-sectional cohort variance rather than longitudinal individual aging rates.
3. **Array Platform Dropout**: Historical clocks (Horvath 353, PhenoAge 513) require specific 27K/450K probes. Newer EPIC v2 arrays omit certain historical loci; BioAge-X never manufactures missing probes.
4. **Demographic Skew**: Public benchmark cohorts are predominantly European-ancestry adult populations; generalization across global ancestries requires explicit external cohort validation.

---

## 5. Privacy, Ethics & Licensing
- **Public Domain**: Public accessions (GEO, PRIDE, MetaboLights, ENA) adhere to open-access terms of use.
- **Controlled Data Guardrails**: High-throughput whole-genome BAMs and germline variants in GDC enforce `PermissionError: ACCESS RESTRICTED` requiring dbGaP tokens.
- **AI Privacy Guardrail**: User-uploaded raw omics matrices are **NEVER transmitted** to external AI services (Gemini). Only minimal, aggregated summary metrics (MAE, top 5 mapped gene symbols) are shared with the optional assistant.
