"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, Layers, Cpu, GitCommit, Network, AlertCircle, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";

export default function AblationStudiesPage() {
  const [activeTab, setActiveTab] = useState<"modality" | "fusion" | "features" | "gnn">("modality");
  const [loading, setLoading] = useState(false);
  const [ablationData, setAblationData] = useState<any>(null);

  useEffect(() => {
    async function fetchAblation() {
      setLoading(true);
      try {
        const res = await api.getAblations("current_experiment", activeTab);
        setAblationData(res);
      } catch (e) {
        console.error("Failed to load ablation studies", e);
      } finally {
        setLoading(false);
      }
    }
    fetchAblation();
  }, [activeTab]);

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 mb-1">
            <Link href="/experiments" className="hover:underline flex items-center gap-1">
              <ArrowLeft className="w-3 h-3" /> Back to Experiments
            </Link>
            <span>/</span>
            <span className="bg-purple-950/60 border border-purple-500/30 px-2 py-0.5 rounded text-[10px] text-purple-300 font-bold uppercase tracking-wider">
              ABLATION EXPERIMENTS
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Layers className="w-6 h-6 text-purple-400" />
            Formal Scientific Ablation Studies
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Isolating multi-omics layers, fusion architectures, feature sets, and GNN interactomes to evaluate genuine empirical utility.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("modality")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-colors ${
            activeTab === "modality"
              ? "bg-purple-600 text-white shadow-lg shadow-purple-950/40"
              : "bg-slate-900 text-slate-400 hover:text-slate-200"
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          1. Modality Ablation
        </button>
        <button
          onClick={() => setActiveTab("fusion")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-colors ${
            activeTab === "fusion"
              ? "bg-purple-600 text-white shadow-lg shadow-purple-950/40"
              : "bg-slate-900 text-slate-400 hover:text-slate-200"
          }`}
        >
          <GitCommit className="w-3.5 h-3.5" />
          2. Fusion Strategy Ablation
        </button>
        <button
          onClick={() => setActiveTab("features")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-colors ${
            activeTab === "features"
              ? "bg-purple-600 text-white shadow-lg shadow-purple-950/40"
              : "bg-slate-900 text-slate-400 hover:text-slate-200"
          }`}
        >
          <Cpu className="w-3.5 h-3.5" />
          3. Feature Set Compactness
        </button>
        <button
          onClick={() => setActiveTab("gnn")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-colors ${
            activeTab === "gnn"
              ? "bg-purple-600 text-white shadow-lg shadow-purple-950/40"
              : "bg-slate-900 text-slate-400 hover:text-slate-200"
          }`}
        >
          <Network className="w-3.5 h-3.5" />
          4. GNN Interactome Topology
        </button>
      </div>

      {/* Content */}
      {loading ? (
        <div className="p-12 text-center text-slate-500 font-mono text-sm">
          Executing scientific ablation comparison...
        </div>
      ) : ablationData ? (
        <div className="space-y-6">
          {/* Interpretation banner */}
          <div className="p-4 rounded-xl border border-purple-500/20 bg-purple-950/10 text-xs text-purple-200 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-purple-400 shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold uppercase tracking-wider text-purple-100 mb-0.5">
                Scientific Question Evaluated
              </div>
              <p>{ablationData.scientific_interpretation || ablationData.summary}</p>
            </div>
          </div>

          {/* Results Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-800 bg-slate-950/40 flex justify-between items-center">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
                Ablation Conditions & Performance Outcomes
              </h2>
              <span className="text-xs font-mono text-purple-400">
                {ablationData.ablation_type}
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm font-mono text-xs">
                <thead className="bg-slate-950 uppercase tracking-wider text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="px-6 py-3 font-sans">Condition / Configuration</th>
                    <th className="px-6 py-3">MAE (Years)</th>
                    <th className="px-6 py-3">RMSE (Years)</th>
                    <th className="px-6 py-3">R² (Variance)</th>
                    <th className="px-6 py-3 font-sans">Scientific Verdict</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {ablationData.results?.map((row: any, i: number) => (
                    <tr key={i} className="hover:bg-slate-800/30">
                      <td className="px-6 py-3 font-sans font-semibold text-slate-200">
                        {row.modality_condition || row.fusion_strategy || row.feature_set || row.model_condition}
                      </td>
                      <td className="px-6 py-3 text-cyan-300 font-bold">{row.mae?.toFixed(2)} y</td>
                      <td className="px-6 py-3 text-slate-300">{row.rmse?.toFixed(2) ?? "N/A"} y</td>
                      <td className="px-6 py-3 text-indigo-300">{row.r2?.toFixed(3)}</td>
                      <td className="px-6 py-3 font-sans text-slate-400">
                        {row.scientific_verdict || (row.delta_mae_vs_baseline !== undefined ? `Δ MAE: ${row.delta_mae_vs_baseline > 0 ? "+" : ""}${row.delta_mae_vs_baseline} y` : "Evaluated")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
