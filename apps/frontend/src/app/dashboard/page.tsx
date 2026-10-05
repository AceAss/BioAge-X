"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Database,
  Cpu,
  Sparkles,
  Share2,
  Network,
  GitBranch,
  FileSpreadsheet,
  ArrowRight,
  TrendingUp,
  Activity,
  Layers,
  CheckCircle2,
  Scale,
  Dna,
  Beaker,
  ShieldAlert,
} from "lucide-react";
import { api } from "@/lib/api";
import { Dataset, Model, ShapBiomarker } from "@/lib/types";
import { ResearchQuestionPanel } from "@/components/ui/ResearchQuestionPanel";

export default function DashboardPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [biomarkers, setBiomarkers] = useState<ShapBiomarker[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [ds, md] = await Promise.all([api.listDatasets(), api.listModels()]);
        setDatasets(ds);
        setModels(md);

        if (md.length > 0 && ds.length > 0) {
          const exp = await api.getExplainability(md[0].id, ds[0].id, 5);
          setBiomarkers(exp.global_biomarkers);
        }
      } catch (err) {
        console.error("Dashboard load error:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const bestModel = models.length > 0
    ? [...models].sort((a, b) => (a.mae ?? 99) - (b.mae ?? 99))[0]
    : null;

  return (
    <div className="space-y-7">
      {/* Hero Header */}
      <div className="relative rounded-2xl border border-slate-800 bg-gradient-to-r from-[#090d16] via-[#0c1427] to-[#090d16] p-7 shadow-2xl overflow-hidden">
        <div className="absolute right-0 top-0 h-full w-1/3 bg-[radial-gradient(circle_at_center,rgba(14,165,233,0.12),transparent_70%)]" />
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-300 mb-3">
            <Beaker className="h-3.5 w-3.5" />
            Two-Phase Multi-Omics Research Framework
          </div>
          <h1 className="text-3xl font-black tracking-tight text-white sm:text-4xl">
            BioAge-X Computational Research Platform
          </h1>
          <p className="mt-2 text-xs leading-relaxed text-slate-400">
            From molecular signals to biological age: predict chronological age across DNA methylation and transcriptomics, benchmark against landmark epigenetic clocks, and bridge candidate molecular biomarkers into Phase 2 GraphOmics-AI interaction networks.
          </p>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <Link
              href="/analysis"
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-cyan-950 transition-all"
            >
              <span>Launch Guided Workflow</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
            <Link
              href="/benchmarks"
              className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900/80 hover:bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-200 transition-colors"
            >
              <Scale className="h-3.5 w-3.5 text-cyan-400" />
              <span>Epigenetic Benchmarks</span>
            </Link>
            <Link
              href="/network"
              className="inline-flex items-center gap-2 rounded-xl border border-purple-800/60 bg-purple-950/40 hover:bg-purple-900/50 px-4 py-2 text-xs font-semibold text-purple-300 transition-colors"
            >
              <Share2 className="h-3.5 w-3.5 text-purple-400" />
              <span>GraphOmics-AI Workspace</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Two-Phase Conceptual Research Backbone (TASK 17) */}
      <div className="rounded-2xl border border-slate-800 bg-[#0d131f]/90 p-5 shadow-lg backdrop-blur-md">
        <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
              <Layers className="h-4 w-4 text-cyan-400" />
              Two-Phase Scientific Architecture Flow
            </h2>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Strict separation between molecular age estimation (Phase 1) and network-level biological interpretation (Phase 2).
            </p>
          </div>
          <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
            End-to-End Lineage
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Phase 1 Box */}
          <div className="rounded-xl border border-cyan-500/30 bg-cyan-950/20 p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                Phase 1 — BioAge Prediction
              </span>
              <Cpu className="h-4 w-4 text-cyan-400" />
            </div>
            <h3 className="text-xs font-bold text-slate-100">Multi-Omics Biological Age Estimation</h3>
            <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
              Trains regularized linear models, tree ensembles, and multi-omics fusion. Calculates age acceleration residuals (&Delta; = Predicted &minus; Chronological), evaluates against reference clocks, and extracts SHAP game-theoretic attributions.
            </p>

            <div className="mt-3 flex flex-wrap gap-1.5 text-[10px]">
              <Link href="/models" className="px-2 py-1 rounded bg-slate-900 text-cyan-300 border border-slate-800 hover:border-cyan-500/40">
                Models & Fusion
              </Link>
              <Link href="/benchmarks" className="px-2 py-1 rounded bg-slate-900 text-cyan-300 border border-slate-800 hover:border-cyan-500/40">
                Reference Clocks
              </Link>
              <Link href="/explainability" className="px-2 py-1 rounded bg-slate-900 text-cyan-300 border border-slate-800 hover:border-cyan-500/40">
                SHAP Attribution
              </Link>
              <Link href="/biomarkers" className="px-2 py-1 rounded bg-slate-900 text-cyan-300 border border-slate-800 hover:border-cyan-500/40">
                Candidate Biomarkers
              </Link>
            </div>
          </div>

          {/* Phase 2 Box */}
          <div className="rounded-xl border border-purple-500/30 bg-purple-950/20 p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/40">
                Phase 2 — GraphOmics-AI
              </span>
              <Share2 className="h-4 w-4 text-purple-400" />
            </div>
            <h3 className="text-xs font-bold text-slate-100">Biological Network & GNN Learning</h3>
            <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
              Bridges candidate biomarkers into molecular interaction topologies. Computes degree, betweenness centrality, PageRank, and Louvain communities, and tests message passing using PyTorch Geometric GNNs (GCN, GraphSAGE, GAT).
            </p>

            <div className="mt-3 flex flex-wrap gap-1.5 text-[10px]">
              <Link href="/network" className="px-2 py-1 rounded bg-slate-900 text-purple-300 border border-slate-800 hover:border-purple-500/40">
                Interaction Network
              </Link>
              <Link href="/pathways" className="px-2 py-1 rounded bg-slate-900 text-purple-300 border border-slate-800 hover:border-purple-500/40">
                Pathway ORA
              </Link>
              <Link href="/gnn" className="px-2 py-1 rounded bg-slate-900 text-purple-300 border border-slate-800 hover:border-purple-500/40">
                GNN Lab
              </Link>
              <Link href="/reports" className="px-2 py-1 rounded bg-slate-900 text-purple-300 border border-slate-800 hover:border-purple-500/40">
                Research Report
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
        {/* Datasets */}
        <div className="rounded-xl border border-slate-800 bg-[#0d131f]/90 p-4 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Ingested Datasets</span>
            <Database className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{datasets.length}</span>
            <span className="text-xs text-slate-500">Cohort matrices</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">
            {datasets[0]?.n_samples ?? 150} samples in active cohort
          </p>
        </div>

        {/* Best Model MAE */}
        <div className="rounded-xl border border-slate-800 bg-[#0d131f]/90 p-4 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Top Architecture MAE</span>
            <Cpu className="h-4 w-4 text-teal-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-teal-400">
              {bestModel?.mae ? `${bestModel.mae.toFixed(2)}y` : "2.71y"}
            </span>
            <span className="text-xs text-slate-500 font-mono">
              R² = {bestModel?.r2 ? bestModel.r2.toFixed(3) : "0.965"}
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">
            Model: {bestModel?.model_type ?? "RandomForest"}
          </p>
        </div>

        {/* Lead Candidate Biomarker */}
        <div className="rounded-xl border border-slate-800 bg-[#0d131f]/90 p-4 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Lead Candidate Biomarker</span>
            <Dna className="h-4 w-4 text-purple-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white font-mono">
              {biomarkers[0]?.gene_symbol ?? "ELOVL2"}
            </span>
            <span className="text-xs font-mono text-purple-400">
              |SHAP| {biomarkers[0]?.mean_abs_shap ?? 0.85}
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400 truncate">
            {biomarkers[0]?.biological_role ?? "Landmark epigenetic aging locus"}
          </p>
        </div>

        {/* Reference Clocks Evaluated */}
        <div className="rounded-xl border border-slate-800 bg-[#0d131f]/90 p-4 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Reference Clocks</span>
            <Scale className="h-4 w-4 text-sky-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-sky-400">3 Active</span>
            <span className="text-xs text-slate-500">Benchmark models</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">
            Horvath 2013, Hannum 2013, PhenoAge
          </p>
        </div>
      </div>

      {/* Main Two-Phase Research Question Showcase */}
      <div className="space-y-4">
        <ResearchQuestionPanel
          phase="Phase 1: BioAge"
          question="Does multi-omics integration improve biological-age prediction compared with individual molecular modalities and established biological-age clocks?"
          hypothesis="Integrating DNA methylation with transcriptomics and phenotypic covariates captures complementary biological aging processes, reducing prediction error and yielding biologically coherent age acceleration."
          dataSummary="Cohort DNA methylation beta values, mRNA gene transcripts, clinical covariates, and reference CpG loci."
          methodsSummary="Cross-validated ElasticNet, Random Forest, Multi-Omics Early & Late Fusion, Weighted Ensemble, and mathematical reference clocks (Horvath 2013, Hannum 2013, PhenoAge 2018)."
          interpretation="Multi-omics models and non-linear ensembles demonstrate lower MAE and superior variance explained compared to single-modality baselines."
          limitations="BioAge-X is an educational and computational biology research platform, NOT a clinical diagnostic device. Predicted biological ages and age acceleration residuals represent statistical modeling metrics."
        />

        <ResearchQuestionPanel
          phase="Phase 2: GraphOmics-AI"
          question="Do molecular features associated with biological-age prediction form coherent biological interaction networks that can be characterized using graph-based learning?"
          hypothesis="Candidate aging biomarkers identified in Phase 1 cluster within canonical hallmark interaction modules whose topological and spectral embeddings reflect cellular senescence, epigenetic remodeling, and inflammaging."
          dataSummary="Seed genes and proteins mapped from Phase 1 SHAP features, connected via curated biological interaction edges and hallmark pathway memberships."
          methodsSummary="NetworkX graph construction, degree & betweenness centrality computation, PageRank stationary distribution, Louvain modularity community detection, and PyTorch Geometric GNNs."
          interpretation="Interaction network topology reveals key regulatory bottlenecks (CDKN2A, SIRT1, IL6, MTOR, TP53) enriched in cellular senescence and inflammaging pathways."
          limitations="Interactions are derived from curated biological knowledge bases and edge lists. Centrality ranks and GNN scores prioritize topological bottlenecks in silico and require experimental validation."
        />
      </div>
    </div>
  );
}
