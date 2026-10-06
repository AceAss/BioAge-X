"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRightLeft, CheckCircle2, AlertTriangle, ShieldCheck, HelpCircle } from "lucide-react";
import { api } from "@/lib/api";

export default function ExperimentComparisonPage() {
  const [experiments, setExperiments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [expAId, setExpAId] = useState("");
  const [expBId, setExpBId] = useState("");
  const [comparison, setComparison] = useState<any>(null);
  const [comparing, setComparing] = useState(false);

  useEffect(() => {
    async function fetchExperiments() {
      try {
        const res = await api.listExperiments();
        setExperiments(res);
        if (res.length >= 2) {
          setExpAId(res[0].id);
          setExpBId(res[1].id);
        } else if (res.length === 1) {
          setExpAId(res[0].id);
          setExpBId(res[0].id);
        }
      } catch (e) {
        console.error("Failed to load experiments", e);
      } finally {
        setLoading(false);
      }
    }
    fetchExperiments();
  }, []);

  const handleCompare = async () => {
    if (!expAId || !expBId) return;
    setComparing(true);
    try {
      const res = await api.compareExperiments(expAId, expBId);
      setComparison(res);
    } catch (e) {
      console.error("Comparison failed", e);
    } finally {
      setComparing(false);
    }
  };

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
            <span>RESEARCH RIGOR</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <ArrowRightLeft className="w-6 h-6 text-cyan-400" />
            Experiment Comparison Workspace
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Side-by-side scientific evaluation of cohort configurations, regularized regressions, and interactome models.
          </p>
        </div>
      </div>

      {/* Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-slate-900/60 p-6 rounded-xl border border-slate-800">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Experiment A (Baseline / Reference)
          </label>
          <select
            value={expAId}
            onChange={(e) => setExpAId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
          >
            {experiments.map((exp) => (
              <option key={exp.id} value={exp.id}>
                {exp.name} ({exp.model_type} - {exp.id.slice(0, 8)})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Experiment B (Candidate / Comparator)
          </label>
          <select
            value={expBId}
            onChange={(e) => setExpBId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
          >
            {experiments.map((exp) => (
              <option key={exp.id} value={exp.id}>
                {exp.name} ({exp.model_type} - {exp.id.slice(0, 8)})
              </option>
            ))}
          </select>
        </div>

        <div className="md:col-span-2 flex justify-end">
          <button
            onClick={handleCompare}
            disabled={comparing || !expAId || !expBId}
            className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold uppercase tracking-wider rounded-lg transition-colors flex items-center gap-2 shadow-lg shadow-cyan-950/30"
          >
            <ArrowRightLeft className="w-4 h-4" />
            {comparing ? "Evaluating Comparison..." : "Execute Side-by-Side Comparison"}
          </button>
        </div>
      </div>

      {/* Comparison Results */}
      {comparison && (
        <div className="space-y-6 animate-fadeIn">
          {/* Scientific Caveat Banner */}
          <div className="p-4 rounded-xl border border-amber-500/20 bg-amber-950/10 text-xs text-amber-300 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold uppercase tracking-wider text-amber-200 mb-0.5">
                Scientific Rigor & Statistical Qualification
              </div>
              <p>{comparison.scientific_qualification}</p>
            </div>
          </div>

          {/* Metric Comparison Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-800 bg-slate-950/40 flex justify-between items-center">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
                Performance Delta Matrix
              </h2>
              <span className="text-xs font-mono text-cyan-400">
                Better Architecture: {comparison.deltas.better_model}
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-950 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="px-6 py-3">Metric Dimension</th>
                    <th className="px-6 py-3">Experiment A</th>
                    <th className="px-6 py-3">Experiment B</th>
                    <th className="px-6 py-3">Delta (B - A)</th>
                    <th className="px-6 py-3">Interpretation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                  <tr className="hover:bg-slate-800/30">
                    <td className="px-6 py-3 font-sans font-semibold text-slate-300">Architecture</td>
                    <td className="px-6 py-3 text-cyan-400">{comparison.experiment_a.model_type}</td>
                    <td className="px-6 py-3 text-indigo-400">{comparison.experiment_b.model_type}</td>
                    <td className="px-6 py-3 text-slate-500">-</td>
                    <td className="px-6 py-3 font-sans text-slate-400">Model Algorithm</td>
                  </tr>
                  <tr className="hover:bg-slate-800/30">
                    <td className="px-6 py-3 font-sans font-semibold text-slate-300">Mean Absolute Error (MAE)</td>
                    <td className="px-6 py-3 text-slate-200">{comparison.experiment_a.metrics.mae?.toFixed(3) ?? "N/A"} y</td>
                    <td className="px-6 py-3 text-slate-200">{comparison.experiment_b.metrics.mae?.toFixed(3) ?? "N/A"} y</td>
                    <td className="px-6 py-3 font-bold text-cyan-300">
                      {comparison.deltas.delta_mae > 0 ? `+${comparison.deltas.delta_mae}` : comparison.deltas.delta_mae} y
                    </td>
                    <td className="px-6 py-3 font-sans text-slate-400">
                      {comparison.deltas.delta_mae < 0 ? "Experiment B lower error" : "Experiment A lower error"}
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-800/30">
                    <td className="px-6 py-3 font-sans font-semibold text-slate-300">Coefficient of Determination (R²)</td>
                    <td className="px-6 py-3 text-slate-200">{comparison.experiment_a.metrics.r2?.toFixed(3) ?? "N/A"}</td>
                    <td className="px-6 py-3 text-slate-200">{comparison.experiment_b.metrics.r2?.toFixed(3) ?? "N/A"}</td>
                    <td className="px-6 py-3 font-bold text-indigo-300">
                      {comparison.deltas.delta_r2 > 0 ? `+${comparison.deltas.delta_r2}` : comparison.deltas.delta_r2}
                    </td>
                    <td className="px-6 py-3 font-sans text-slate-400">Explained Variance Ratio</td>
                  </tr>
                  <tr className="hover:bg-slate-800/30">
                    <td className="px-6 py-3 font-sans font-semibold text-slate-300">Root Mean Squared Error (RMSE)</td>
                    <td className="px-6 py-3 text-slate-200">{comparison.experiment_a.metrics.rmse?.toFixed(3) ?? "N/A"} y</td>
                    <td className="px-6 py-3 text-slate-200">{comparison.experiment_b.metrics.rmse?.toFixed(3) ?? "N/A"} y</td>
                    <td className="px-6 py-3 text-slate-400">
                      {((comparison.experiment_b.metrics.rmse ?? 0) - (comparison.experiment_a.metrics.rmse ?? 0)).toFixed(3)} y
                    </td>
                    <td className="px-6 py-3 font-sans text-slate-400">Penalizes large outlier residuals</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
