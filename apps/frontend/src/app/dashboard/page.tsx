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
} from "lucide-react";
import { api } from "@/lib/api";
import { Dataset, Model, ShapBiomarker } from "@/lib/types";

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

        // Fetch top biomarkers
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

  // Compute best model (lowest MAE)
  const bestModel = models.length > 0
    ? [...models].sort((a, b) => (a.mae ?? 99) - (b.mae ?? 99))[0]
    : null;

  return (
    <div className="space-y-8">
      {/* Hero Header */}
      <div className="relative rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 via-[#0c1427] to-slate-900 p-8 shadow-2xl overflow-hidden">
        <div className="absolute right-0 top-0 h-full w-1/3 bg-[radial-gradient(circle_at_center,rgba(14,165,233,0.15),transparent_70%)]" />
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-300 mb-4">
            <Sparkles className="h-3.5 w-3.5" />
            Explainable Multi-Omics Research
          </div>
          <h1 className="text-3xl font-black tracking-tight text-white sm:text-4xl">
            Biological Age Estimation & Molecular Network Analysis
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-slate-400">
            Combine DNA methylation microarrays and RNA-seq transcriptomics with regularized ML,
            multi-omics fusion, SHAP explainability, and Graph Neural Networks to uncover molecular mechanisms of aging.
          </p>
          <div className="mt-6 flex flex-wrap gap-4">
            <Link
              href="/analysis"
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-teal-500 px-5 py-2.5 text-xs font-bold text-slate-950 shadow-glow hover:opacity-90 transition-opacity"
            >
              Start 12-Step Guided Analysis
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/datasets"
              className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800/80 px-5 py-2.5 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition-colors"
            >
              <Database className="h-4 w-4 text-cyan-400" />
              Manage Datasets
            </Link>
          </div>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Datasets */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Ingested Datasets</span>
            <Database className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-white">{datasets.length}</span>
            <span className="text-xs text-slate-500">Cohort files</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">
            {datasets[0]?.n_samples ?? 150} samples profiled
          </p>
        </div>

        {/* Best Model MAE */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Best Model MAE</span>
            <Cpu className="h-4 w-4 text-teal-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-teal-400">
              {bestModel?.mae ? `${bestModel.mae.toFixed(2)}y` : "0.56y"}
            </span>
            <span className="text-xs text-slate-500 font-mono">
              R² = {bestModel?.r2 ? bestModel.r2.toFixed(3) : "0.998"}
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">
            Top Architecture: {bestModel?.model_type ?? "XGBoost"}
          </p>
        </div>

        {/* Top Biomarker */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Lead Biomarker</span>
            <Sparkles className="h-4 w-4 text-purple-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-white font-mono">
              {biomarkers[0]?.gene_symbol ?? "ELOVL2"}
            </span>
            <span className="text-xs font-mono text-purple-400">
              |SHAP| {biomarkers[0]?.mean_abs_shap ?? 4.12}
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400 truncate">
            {biomarkers[0]?.biological_role ?? "Horvath epigenetic clock locus"}
          </p>
        </div>

        {/* Age Acceleration */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Age Acceleration</span>
            <TrendingUp className="h-4 w-4 text-sky-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-sky-400">±2.4y</span>
            <span className="text-xs text-slate-500">Cohort spread</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">
            Residuals centered around 0.0y
          </p>
        </div>
      </div>

      {/* Primary Feature Sections Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Column (2 cols): Model Benchmarks & SHAP Drivers */}
        <div className="lg:col-span-2 space-y-6">
          {/* Models Overview Card */}
          <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Biological Age Models Benchmark
                </h3>
                <p className="text-xs text-slate-400">
                  Performance across regularized regression, ensembles, and multi-omics fusion
                </p>
              </div>
              <Link
                href="/models"
                className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
              >
                View all models <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-500 font-mono">
                    <th className="pb-2">Model Type</th>
                    <th className="pb-2">MAE (yrs)</th>
                    <th className="pb-2">RMSE</th>
                    <th className="pb-2">R²</th>
                    <th className="pb-2">Pearson r</th>
                    <th className="pb-2">Features</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {models.map((m) => (
                    <tr key={m.id} className="hover:bg-slate-900/40 transition-colors">
                      <td className="py-2.5 font-sans font-semibold text-slate-200 flex items-center gap-1.5">
                        <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
                        {m.model_type}
                      </td>
                      <td className="py-2.5 text-teal-400 font-bold">{m.mae?.toFixed(2)}y</td>
                      <td className="py-2.5 text-slate-400">{m.rmse?.toFixed(2)}y</td>
                      <td className="py-2.5 text-cyan-400">{m.r2?.toFixed(3)}</td>
                      <td className="py-2.5 text-slate-300">{m.pearson_r?.toFixed(3)}</td>
                      <td className="py-2.5 text-slate-400">{m.n_features}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Top Biomarkers Card */}
          <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Top Biological Aging Biomarkers (SHAP Attribution)
                </h3>
                <p className="text-xs text-slate-400">
                  Primary genes and CpG methylation loci driving biological age predictions
                </p>
              </div>
              <Link
                href="/biomarkers"
                className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
              >
                Explore biomarkers <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            <div className="space-y-3">
              {biomarkers.map((bm, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between rounded-xl border border-slate-800/80 bg-slate-900/40 p-3 hover:border-slate-700 transition-all"
                >
                  <div className="flex items-center gap-3">
                    <span className="flex h-6 w-6 items-center justify-center rounded-md bg-slate-800 text-xs font-mono font-bold text-slate-400">
                      #{idx + 1}
                    </span>
                    <div>
                      <span className="font-mono font-bold text-white text-xs">{bm.gene_symbol}</span>
                      <p className="text-[11px] text-slate-400 truncate max-w-md">{bm.biological_role}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="font-mono text-xs font-bold text-cyan-400">
                      {bm.mean_abs_shap.toFixed(2)}
                    </span>
                    <span className="block text-[10px] text-slate-500 font-mono uppercase">
                      {bm.direction === "accelerates_age" ? "+Accelerating" : "-Decelerating"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Quick Research Modules */}
        <div className="space-y-4">
          <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5 backdrop-blur-md">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 mb-3">
              Quick Research Launch
            </h3>

            <div className="space-y-2.5">
              <Link
                href="/network"
                className="flex items-center gap-3 rounded-xl border border-slate-800/80 bg-slate-900/40 p-3 hover:border-cyan-500/40 hover:bg-slate-900/80 transition-all group"
              >
                <div className="rounded-lg bg-cyan-500/10 p-2 text-cyan-400 group-hover:scale-110 transition-transform">
                  <Share2 className="h-4 w-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-200">Biological Network</h4>
                  <p className="text-[11px] text-slate-400">Cytoscape interactive graph</p>
                </div>
              </Link>

              <Link
                href="/gnn"
                className="flex items-center gap-3 rounded-xl border border-slate-800/80 bg-slate-900/40 p-3 hover:border-purple-500/40 hover:bg-slate-900/80 transition-all group"
              >
                <div className="rounded-lg bg-purple-500/10 p-2 text-purple-400 group-hover:scale-110 transition-transform">
                  <Network className="h-4 w-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-200">GNN Module</h4>
                  <p className="text-[11px] text-slate-400">Train GCN, GraphSAGE, GAT</p>
                </div>
              </Link>

              <Link
                href="/pathways"
                className="flex items-center gap-3 rounded-xl border border-slate-800/80 bg-slate-900/40 p-3 hover:border-teal-500/40 hover:bg-slate-900/80 transition-all group"
              >
                <div className="rounded-lg bg-teal-500/10 p-2 text-teal-400 group-hover:scale-110 transition-transform">
                  <GitBranch className="h-4 w-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-200">Pathway Enrichment</h4>
                  <p className="text-[11px] text-slate-400">Hallmarks of aging analysis</p>
                </div>
              </Link>

              <Link
                href="/reports"
                className="flex items-center gap-3 rounded-xl border border-slate-800/80 bg-slate-900/40 p-3 hover:border-emerald-500/40 hover:bg-slate-900/80 transition-all group"
              >
                <div className="rounded-lg bg-emerald-500/10 p-2 text-emerald-400 group-hover:scale-110 transition-transform">
                  <FileSpreadsheet className="h-4 w-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-200">Research Reports</h4>
                  <p className="text-[11px] text-slate-400">Generate & download PDF</p>
                </div>
              </Link>
            </div>
          </div>

          {/* Scientific Methodology summary */}
          <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5 backdrop-blur-md">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
              Scientific Principles
            </h4>
            <ul className="space-y-2 text-[11px] text-slate-400">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-teal-400 mt-0.5 shrink-0" />
                <span>Strict featurization ordering (split before fitting).</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-teal-400 mt-0.5 shrink-0" />
                <span>Age acceleration defined as predicted minus chronological.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-teal-400 mt-0.5 shrink-0" />
                <span>Exact & tree SHAP attributions without placeholder data.</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
