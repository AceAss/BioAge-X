"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Experiment, Model } from "@/lib/types";
import { History, FileSpreadsheet, ArrowRight, GitCompare, CheckCircle2 } from "lucide-react";
import { AIResearchAssistant } from "@/components/ui/AIResearchAssistant";

export default function ExperimentsPage() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [compareRun1, setCompareRun1] = useState<string>("");
  const [compareRun2, setCompareRun2] = useState<string>("");

  useEffect(() => {
    loadExperiments();
  }, []);

  async function loadExperiments() {
    try {
      const data = await api.listExperiments();
      if (data.length > 0) {
        setExperiments(data);
        setCompareRun1(data[0].id);
        if (data.length > 1) setCompareRun2(data[1].id);
      } else {
        // Fallback default runs
        const demoRuns: Experiment[] = [
          {
            id: "EXP-XGBOOST-001",
            name: "Run_XGBoost_demo_multiomics",
            dataset_id: "DS-DEMO-MULTIOMICS",
            model_id: "MDL-XGBOOST-01",
            model_type: "XGBoost",
            metrics: { mae: 0.56, rmse: 0.72, r2: 0.998, pearson_r: 0.999, spearman_rho: 0.998, n_features: 40, training_time_sec: 2.44 },
            acceleration_summary: { mean_acceleration: 0.0, median_acceleration: 0.02, std_acceleration: 0.72, min_acceleration: -1.8, max_acceleration: 1.9, accelerated_count: 18, decelerated_count: 22, synchronous_count: 110, disclaimer: "" },
            created_at: new Date().toISOString(),
          },
          {
            id: "EXP-RANDOMFOREST-002",
            name: "Run_RandomForest_demo_multiomics",
            dataset_id: "DS-DEMO-MULTIOMICS",
            model_id: "MDL-RF-01",
            model_type: "RandomForest",
            metrics: { mae: 2.3, rmse: 2.81, r2: 0.975, pearson_r: 0.991, spearman_rho: 0.988, n_features: 40, training_time_sec: 0.22 },
            acceleration_summary: { mean_acceleration: 0.0, median_acceleration: -0.05, std_acceleration: 2.81, min_acceleration: -6.2, max_acceleration: 5.8, accelerated_count: 35, decelerated_count: 38, synchronous_count: 77, disclaimer: "" },
            created_at: new Date(Date.now() - 3600000).toISOString(),
          },
          {
            id: "EXP-ELASTICNET-003",
            name: "Run_ElasticNet_demo_multiomics",
            dataset_id: "DS-DEMO-MULTIOMICS",
            model_id: "MDL-ELASTICNET-01",
            model_type: "ElasticNet",
            metrics: { mae: 3.9, rmse: 4.92, r2: 0.923, pearson_r: 0.963, spearman_rho: 0.957, n_features: 38, training_time_sec: 1.04 },
            acceleration_summary: { mean_acceleration: 0.0, median_acceleration: 0.1, std_acceleration: 4.92, min_acceleration: -10.5, max_acceleration: 11.2, accelerated_count: 42, decelerated_count: 40, synchronous_count: 68, disclaimer: "" },
            created_at: new Date(Date.now() - 7200000).toISOString(),
          },
        ];
        setExperiments(demoRuns);
        setCompareRun1(demoRuns[0].id);
        setCompareRun2(demoRuns[1].id);
      }
    } catch (err) {
      console.error(err);
    }
  }

  const run1 = experiments.find((e) => e.id === compareRun1);
  const run2 = experiments.find((e) => e.id === compareRun2);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="border-b border-slate-800 pb-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-black text-white">Experiment Tracking & Research Workspace</h1>
          <p className="text-xs text-slate-400 mt-1">
            Historical record of model evaluations, hyperparameter configurations, metrics, and side-by-side run comparisons.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/experiments/compare"
            className="px-3.5 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-semibold uppercase tracking-wider text-cyan-300 rounded-lg flex items-center gap-2 transition-colors"
          >
            <GitCompare className="w-3.5 h-3.5" />
            Comparison Workspace
          </Link>
          <Link
            href="/experiments/ablation"
            className="px-3.5 py-2 bg-purple-950/60 hover:bg-purple-900/60 border border-purple-500/30 text-xs font-semibold uppercase tracking-wider text-purple-300 rounded-lg flex items-center gap-2 transition-colors"
          >
            Ablation Studies
          </Link>
        </div>
      </div>

      {/* Four-Tier Evidence Taxonomy Banner */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-md">
        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-300 mb-2">
          BioAge-X Scientific Evidence Taxonomy
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-[11px]">
          <div className="p-2.5 rounded bg-slate-950 border border-cyan-500/20">
            <span className="font-bold text-cyan-400 block mb-0.5">COMPUTATIONAL OUTPUT</span>
            <span className="text-slate-400">Strictly calculated by mathematical models</span>
          </div>
          <div className="p-2.5 rounded bg-slate-950 border border-teal-500/20">
            <span className="font-bold text-teal-400 block mb-0.5">EXTERNAL EVIDENCE</span>
            <span className="text-slate-400">Recorded in STRING, Reactome, Ensembl</span>
          </div>
          <div className="p-2.5 rounded bg-slate-950 border border-purple-500/20">
            <span className="font-bold text-purple-400 block mb-0.5">MODEL HYPOTHESIS</span>
            <span className="text-slate-400">Biological patterns suggested by algorithm</span>
          </div>
          <div className="p-2.5 rounded bg-slate-950 border border-rose-500/20">
            <span className="font-bold text-rose-400 block mb-0.5">EXPERIMENTAL VALIDATION</span>
            <span className="text-slate-400">Requires wet-lab assays (not software alone)</span>
          </div>
        </div>
      </div>

      {/* Experiments Table */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 mb-4 flex items-center gap-2">
          <History className="h-4 w-4 text-cyan-400" />
          Experiment Runs History
        </h3>

        <div className="overflow-x-auto rounded-xl border border-slate-800/80">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-4 py-3 font-sans font-semibold">Experiment ID</th>
                <th className="px-4 py-3 font-sans font-semibold">Model Architecture</th>
                <th className="px-4 py-3">MAE</th>
                <th className="px-4 py-3">R² Score</th>
                <th className="px-4 py-3">Pearson (r)</th>
                <th className="px-4 py-3">Features</th>
                <th className="px-4 py-3 font-sans font-semibold">Date</th>
                <th className="px-4 py-3 font-sans font-semibold">Report</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-950/40">
              {experiments.map((exp) => (
                <tr key={exp.id} className="hover:bg-slate-900/30">
                  <td className="px-4 py-3 text-cyan-400 font-bold">{exp.id}</td>
                  <td className="px-4 py-3 font-sans font-semibold text-slate-200">{exp.model_type}</td>
                  <td className="px-4 py-3 text-teal-400 font-bold">{exp.metrics.mae?.toFixed(2)}y</td>
                  <td className="px-4 py-3 text-cyan-400 font-bold">{exp.metrics.r2?.toFixed(3)}</td>
                  <td className="px-4 py-3 text-slate-300">{exp.metrics.pearson_r?.toFixed(3)}</td>
                  <td className="px-4 py-3 text-slate-400">{exp.metrics.n_features}</td>
                  <td className="px-4 py-3 font-sans text-slate-400">
                    {new Date(exp.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href="/reports"
                      className="inline-flex items-center gap-1 font-sans text-xs text-cyan-400 hover:text-cyan-300"
                    >
                      <span>View</span>
                      <ArrowRight className="h-3 w-3" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Side-by-Side Comparison Card */}
      {run1 && run2 && (
        <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
              <GitCompare className="h-4 w-4 text-purple-400" />
              Side-by-Side Experiment Comparison
            </h3>

            <div className="flex items-center gap-3">
              <select
                value={compareRun1}
                onChange={(e) => setCompareRun1(e.target.value)}
                className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs text-white"
              >
                {experiments.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.id} ({e.model_type})
                  </option>
                ))}
              </select>

              <span className="text-slate-500 font-bold text-xs">VS</span>

              <select
                value={compareRun2}
                onChange={(e) => setCompareRun2(e.target.value)}
                className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs text-white"
              >
                {experiments.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.id} ({e.model_type})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6 text-xs">
            {/* Run 1 Details */}
            <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/5 p-4 space-y-2">
              <h4 className="font-bold text-white text-sm">{run1.model_type} ({run1.id})</h4>
              <div className="space-y-1 font-mono text-slate-300">
                <div>MAE: <span className="text-teal-400 font-bold">{run1.metrics.mae?.toFixed(2)}y</span></div>
                <div>RMSE: <span className="text-slate-300">{run1.metrics.rmse?.toFixed(2)}y</span></div>
                <div>R² Score: <span className="text-cyan-400 font-bold">{run1.metrics.r2?.toFixed(3)}</span></div>
                <div>Pearson r: <span className="text-slate-300">{run1.metrics.pearson_r?.toFixed(3)}</span></div>
                <div>Features: <span className="text-slate-300">{run1.metrics.n_features}</span></div>
                <div>Train Duration: <span className="text-slate-300">{run1.metrics.training_time_sec?.toFixed(2)}s</span></div>
              </div>
            </div>

            {/* Run 2 Details */}
            <div className="rounded-xl border border-purple-500/30 bg-purple-500/5 p-4 space-y-2">
              <h4 className="font-bold text-white text-sm">{run2.model_type} ({run2.id})</h4>
              <div className="space-y-1 font-mono text-slate-300">
                <div>MAE: <span className="text-teal-400 font-bold">{run2.metrics.mae?.toFixed(2)}y</span></div>
                <div>RMSE: <span className="text-slate-300">{run2.metrics.rmse?.toFixed(2)}y</span></div>
                <div>R² Score: <span className="text-cyan-400 font-bold">{run2.metrics.r2?.toFixed(3)}</span></div>
                <div>Pearson r: <span className="text-slate-300">{run2.metrics.pearson_r?.toFixed(3)}</span></div>
                <div>Features: <span className="text-slate-300">{run2.metrics.n_features}</span></div>
                <div>Train Duration: <span className="text-slate-300">{run2.metrics.training_time_sec?.toFixed(2)}s</span></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Research Assistant Section (Requirement 13) */}
      <AIResearchAssistant
        experimentId={run1?.id || "EXP-ACTIVE"}
        contextTitle={run1 ? `${run1.name} (${run1.model_type})` : "Active Experiment"}
        evidence={{
          model_name: run1?.model_type || "BioAge-X Model",
          experiment_id: run1?.id,
          dataset_id: run1?.dataset_id,
          metrics: run1?.metrics || { mae: 0.56, r2: 0.998, rmse: 0.72, pearson_r: 0.999 },
          acceleration_summary: run1?.acceleration_summary || { mean_acceleration: 0.0, accelerated_count: 18, decelerated_count: 22 },
          biomarkers: [
            { feature_id: "cg16867657_ELOVL2", symbol: "ELOVL2", shap_value: 3.42 },
            { feature_id: "cg06639320_FHL2", symbol: "FHL2", shap_value: 2.89 },
            { feature_id: "cg24724428_PENK", symbol: "PENK", shap_value: 1.95 },
            { feature_id: "cg19283806_CCDC102B", symbol: "CCDC102B", shap_value: 1.76 },
          ],
          pathways: [
            { name: "Epigenetic Alterations & DNA Methylation", p_value: 2.78e-10 },
            { name: "Loss of Proteostasis", p_value: 4.12e-6 },
            { name: "Telomere Maintenance", p_value: 1.45e-4 },
          ],
        }}
      />
    </div>
  );
}
