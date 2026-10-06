"use client";

import React, { useEffect, useState } from "react";
import {
  Scale,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  BookOpen,
  ArrowRight,
  TrendingDown,
  Layers,
  Sparkles,
} from "lucide-react";
import { ResearchQuestionPanel } from "@/components/ui/ResearchQuestionPanel";
import Link from "next/link";

interface BenchmarkItem {
  name: string;
  category: string;
  strategy: string;
  modality: string;
  status: string;
  available_features_count: number;
  required_features_count: number;
  missing_features_count: number;
  coverage_pct: number;
  mae?: number;
  rmse?: number;
  r2?: number;
  pearson_r?: number;
  spearman_rho?: number;
  sample_count?: number;
  mean_acceleration?: number;
  missing_features_sample?: string[];
  citation?: string;
  notes?: string;
}

interface BenchmarkResponse {
  dataset_id: string;
  dataset_name: string;
  research_question: string;
  sample_count: number;
  age_target_column: string;
  best_performing_approach: string;
  scientific_synthesis: string;
  results: BenchmarkItem[];
}

export default function BenchmarksPage() {
  const [datasets, setDatasets] = useState<any[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [strictCoverage, setStrictCoverage] = useState<boolean>(false);
  const [compatibilityData, setCompatibilityData] = useState<any>(null);
  const [compatibilityLoading, setCompatibilityLoading] = useState<boolean>(false);

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/datasets");
      if (res.ok) {
        const data = await res.json();
        setDatasets(data);
        if (data.length > 0) {
          setSelectedDatasetId(data[0].id);
          fetchCompatibility(data[0].id);
        }
      }
    } catch (e) {
      console.warn("Could not fetch datasets list:", e);
    }
  };

  const fetchCompatibility = async (dsId: string) => {
    if (!dsId) return;
    setCompatibilityLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/benchmarks/compatibility/${encodeURIComponent(dsId)}`);
      if (res.ok) {
        const data = await res.json();
        setCompatibilityData(data);
      }
    } catch (e) {
      console.warn("Could not fetch clock compatibility:", e);
    } finally {
      setCompatibilityLoading(false);
    }
  };

  const runBenchmark = async () => {
    if (!selectedDatasetId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8000/api/v1/benchmarks/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_id: selectedDatasetId,
          strict_coverage: strictCoverage,
        }),
      });

      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || "Benchmark execution failed.");
      }

      const data: BenchmarkResponse = await res.json();
      setBenchmarkData(data);
    } catch (err: any) {
      setError(err.message || "Failed to execute benchmark evaluation.");
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string, coverage: number) => {
    if (status === "AVAILABLE") {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
          <CheckCircle2 className="h-3 w-3 text-emerald-400" /> Available ({coverage}%)
        </span>
      );
    }
    if (status === "PARTIAL_COVERAGE") {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/30">
          <AlertTriangle className="h-3 w-3 text-amber-400" /> Partial ({coverage}%)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-300 border border-rose-500/30">
        <XCircle className="h-3 w-3 text-rose-400" /> Unavailable ({coverage}%)
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 bg-cyan-950/60 border border-cyan-800/60 px-2 py-0.5 rounded-full">
              Phase 1: BioAge
            </span>
            <span className="text-xs text-slate-500">Benchmark Module</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Epigenetic & Multi-Omics Benchmarks
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Compare BioAge-X single-modality and multi-omics architectures directly against established reference clocks (Horvath 2013, Hannum 2013, PhenoAge 2018).
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-3">
          <select
            value={selectedDatasetId}
            onChange={(e) => {
              setSelectedDatasetId(e.target.value);
              fetchCompatibility(e.target.value);
            }}
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none"
          >
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.n_samples} samples)
              </option>
            ))}
          </select>

          <button
            onClick={runBenchmark}
            disabled={loading || !selectedDatasetId}
            className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 px-3.5 py-1.5 text-xs font-semibold text-white shadow-md shadow-cyan-900/20 disabled:opacity-50 transition-all"
          >
            {loading ? <RotateCcw className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
            <span>Run Benchmark Suite</span>
          </button>
        </div>
      </div>

      {/* Research Question Panel */}
      <ResearchQuestionPanel
        phase="Phase 1: BioAge"
        question="Does multi-omics integration improve biological-age prediction compared with individual molecular modalities and established biological-age clocks?"
        hypothesis="Integrating DNA methylation with transcriptomics and phenotypic covariates captures complementary biological aging processes, reducing prediction error and yielding biologically coherent age acceleration."
        dataSummary="Target cohort methylation beta values, mRNA gene transcripts, clinical covariates, and reference CpG loci."
        methodsSummary="Cross-validated ElasticNet, Random Forest, Multi-Omics Early & Late Fusion, Weighted Ensemble, and mathematical reference clocks (Horvath 2013, Hannum 2013, PhenoAge 2018)."
        interpretation={benchmarkData?.scientific_synthesis}
        limitations="Reference clock evaluations strictly report feature coverage. Missing probe values are never fabricated. Discrepancies may arise from array platform differences (27K vs 450K vs EPIC) and tissue composition."
      />

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-4 text-xs text-rose-300">
          <div className="flex items-center gap-2 font-semibold">
            <AlertTriangle className="h-4 w-4 text-rose-400" />
            Benchmark Error
          </div>
          <p className="mt-1 text-slate-300">{error}</p>
        </div>
      )}

      {/* KPI Cards if Benchmark is Run */}
      {benchmarkData && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Best Performing Approach</span>
            <div className="text-sm font-bold text-cyan-400 mt-1 truncate">
              {benchmarkData.best_performing_approach}
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">Ranked by lowest cohort MAE</div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Lowest Prediction Error</span>
            <div className="text-xl font-bold text-emerald-400 mt-1">
              {Math.min(
                ...benchmarkData.results.filter((r) => r.mae !== null && r.mae !== undefined).map((r) => r.mae as number)
              ).toFixed(2)}{" "}
              <span className="text-xs font-normal text-slate-400">years MAE</span>
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">Average absolute error vs chronological age</div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Highest Variance Explained</span>
            <div className="text-xl font-bold text-purple-400 mt-1">
              {Math.max(
                ...benchmarkData.results.filter((r) => r.r2 !== null && r.r2 !== undefined).map((r) => r.r2 as number)
              ).toFixed(3)}{" "}
              <span className="text-xs font-normal text-slate-400">R²</span>
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">Coefficient of determination</div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Evaluated Approaches</span>
            <div className="text-xl font-bold text-slate-200 mt-1">
              {benchmarkData.results.length}{" "}
              <span className="text-xs font-normal text-slate-400">models & clocks</span>
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">Single-omics, multi-omics, & reference clocks</div>
          </div>
        </div>
      )}

      {/* Main Benchmark Comparison Table */}
      <div className="rounded-xl border border-slate-800 bg-[#0d131f]/90 shadow-md backdrop-blur-md overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3 bg-slate-900/50">
          <div className="flex items-center gap-2">
            <Scale className="h-4 w-4 text-cyan-400" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Standardized Model & Clock Benchmark Comparison
            </h2>
          </div>
          {benchmarkData && (
            <span className="text-[11px] text-slate-400">
              Cohort: <strong className="text-slate-200">{benchmarkData.dataset_name}</strong> ({benchmarkData.sample_count} samples)
            </span>
          )}
        </div>

        {/* Tissue Context & Awareness Warning Banner */}
        <div className="mx-4 mb-3 p-3 rounded-lg border border-indigo-500/20 bg-indigo-950/20 text-[11px] text-indigo-300 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-indigo-200 uppercase tracking-wider block mb-0.5">
              Tissue-Aware Benchmark Guidance
            </span>
            <span>
              Reference clocks have specific tissue calibration scopes (e.g. <strong>Horvath</strong> = Pan-Tissue 51 cell types; <strong>Hannum</strong> = Whole Blood; <strong>PhenoAge</strong> = Whole Blood surrogate). Applying whole-blood clocks to solid or in vitro cell cultures introduces systematic calibration bias.
            </span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                <th className="py-2.5 px-3">Model / Reference Clock</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">Modality</th>
                <th className="py-2.5 px-3">Dataset Coverage</th>
                <th className="py-2.5 px-3">MAE (years)</th>
                <th className="py-2.5 px-3">RMSE</th>
                <th className="py-2.5 px-3">R²</th>
                <th className="py-2.5 px-3">Pearson r</th>
                <th className="py-2.5 px-3">Features Used</th>
                <th className="py-2.5 px-3">Methodology Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {!benchmarkData ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-slate-500">
                    <Scale className="h-8 w-8 mx-auto mb-2 text-slate-600 opacity-60" />
                    <p className="font-medium text-slate-400">No benchmark results generated yet.</p>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Select an ingested dataset and click &ldquo;Run Benchmark Suite&rdquo; above.
                    </p>
                  </td>
                </tr>
              ) : (
                benchmarkData.results.map((row, idx) => {
                  const isReference = row.category.includes("Reference");
                  return (
                    <tr
                      key={idx}
                      className={
                        isReference
                          ? "bg-slate-950/40 hover:bg-slate-900/60 transition-colors"
                          : "hover:bg-slate-800/30 transition-colors"
                      }
                    >
                      <td className="py-2.5 px-3 font-semibold text-slate-200 whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          {isReference ? (
                            <BookOpen className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                          ) : (
                            <Layers className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                          )}
                          <span>{row.name}</span>
                        </div>
                      </td>
                      <td className="py-2.5 px-3 text-slate-400 whitespace-nowrap text-[11px]">
                        {row.category}
                      </td>
                      <td className="py-2.5 px-3 whitespace-nowrap">
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                          {row.modality}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 whitespace-nowrap">
                        {getStatusBadge(row.status, row.coverage_pct)}
                      </td>
                      <td className="py-2.5 px-3 font-semibold whitespace-nowrap">
                        {row.mae !== null && row.mae !== undefined ? (
                          <span className={row.mae < 4.0 ? "text-emerald-400" : "text-slate-300"}>
                            {row.mae.toFixed(2)} yrs
                          </span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400 whitespace-nowrap">
                        {row.rmse !== null && row.rmse !== undefined ? row.rmse.toFixed(2) : "—"}
                      </td>
                      <td className="py-2.5 px-3 font-semibold whitespace-nowrap">
                        {row.r2 !== null && row.r2 !== undefined ? (
                          <span className={row.r2 > 0.8 ? "text-purple-400" : "text-slate-300"}>
                            {row.r2.toFixed(3)}
                          </span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-slate-300 whitespace-nowrap">
                        {row.pearson_r !== null && row.pearson_r !== undefined ? row.pearson_r.toFixed(3) : "—"}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400 whitespace-nowrap text-[11px]">
                        {row.available_features_count} / {row.required_features_count}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400 max-w-xs text-[11px] truncate" title={row.notes || row.citation}>
                        {row.notes || row.citation || "Standard regularized prediction"}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Clock Compatibility Engine Inspector */}
      {compatibilityData && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Scale className="w-4 h-4 text-cyan-400" />
                Epigenetic Clock Compatibility &amp; Coverage Audit
              </h3>
              <p className="text-[11px] text-slate-400">
                Audits probe coverage against 1st, 2nd, and 3rd generation clocks without fabricating missing CpGs.
              </p>
            </div>
            <span className="text-[10px] font-mono text-cyan-300 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
              {compatibilityData.dataset_summary?.evaluated_modality?.toUpperCase()} MODALITY
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 pt-2">
            {Object.entries(compatibilityData.clocks || {}).map(([key, c]: [string, any]) => {
              const statusColor =
                c.status === "FULL_COVERAGE"
                  ? "border-emerald-500/40 bg-emerald-950/20 text-emerald-300"
                  : c.status === "PARTIAL_COVERAGE"
                  ? "border-amber-500/40 bg-amber-950/20 text-amber-300"
                  : c.status === "NOT_APPLICABLE"
                  ? "border-purple-500/40 bg-purple-950/20 text-purple-300"
                  : "border-rose-500/40 bg-rose-950/20 text-rose-300";

              return (
                <div
                  key={key}
                  className={`p-3 rounded-lg border flex flex-col justify-between text-xs space-y-2 ${statusColor}`}
                >
                  <div>
                    <div className="text-[10px] uppercase font-bold text-slate-400">{c.generation}</div>
                    <div className="font-bold text-white text-xs">{c.clock_name}</div>
                    <div className="font-mono text-[10px] mt-1">
                      {c.available_count} / {c.required_count} ({c.coverage_pct}%)
                    </div>
                  </div>
                  <div>
                    <span className="text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider bg-slate-900/80">
                      {c.status.replace("_", " ")}
                    </span>
                    <p className="text-[10px] text-slate-400 mt-1 line-clamp-2" title={c.reason}>
                      {c.reason}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Reference Clocks Information Reference Cards (1st, 2nd & 3rd Gen) */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5 space-y-2">
          <div className="flex items-center gap-1.5 text-amber-400 font-semibold text-[11px] uppercase tracking-wider">
            <BookOpen className="h-3.5 w-3.5" />
            Horvath (2013)
          </div>
          <span className="text-[9px] font-bold text-slate-500 uppercase">1st Gen Pan-Tissue</span>
          <p className="text-[10px] text-slate-400 leading-relaxed">
            353 CpG probes across 51 human tissues and cell types. Anti-log transformation for pediatric calibration.
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5 space-y-2">
          <div className="flex items-center gap-1.5 text-teal-400 font-semibold text-[11px] uppercase tracking-wider">
            <BookOpen className="h-3.5 w-3.5" />
            Hannum (2013)
          </div>
          <span className="text-[9px] font-bold text-slate-500 uppercase">1st Gen Whole Blood</span>
          <p className="text-[10px] text-slate-400 leading-relaxed">
            71 CpG markers trained directly on circulating leukocyte DNAm; calibrated specifically for whole blood cohorts.
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5 space-y-2">
          <div className="flex items-center gap-1.5 text-cyan-400 font-semibold text-[11px] uppercase tracking-wider">
            <BookOpen className="h-3.5 w-3.5" />
            PhenoAge (2018)
          </div>
          <span className="text-[9px] font-bold text-slate-500 uppercase">2nd Gen Phenotypic</span>
          <p className="text-[10px] text-slate-400 leading-relaxed">
            513 CpGs trained on composite clinical phenotypic mortality risk from 10 blood chemistry biomarkers.
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5 space-y-2">
          <div className="flex items-center gap-1.5 text-rose-400 font-semibold text-[11px] uppercase tracking-wider">
            <BookOpen className="h-3.5 w-3.5" />
            GrimAge (2019)
          </div>
          <span className="text-[9px] font-bold text-slate-500 uppercase">3rd Gen Surrogate</span>
          <p className="text-[10px] text-slate-400 leading-relaxed">
            1,030 CpGs surrogate of 7 plasma proteins (GDF15, PAI-1, etc.) &amp; pack-years smoking; powerful mortality predictor.
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5 space-y-2">
          <div className="flex items-center gap-1.5 text-violet-400 font-semibold text-[11px] uppercase tracking-wider">
            <BookOpen className="h-3.5 w-3.5" />
            DunedinPACE (2022)
          </div>
          <span className="text-[9px] font-bold text-slate-500 uppercase">3rd Gen Longitudinal</span>
          <p className="text-[10px] text-slate-400 leading-relaxed">
            173 longitudinal pace-of-aging CpGs tracking multi-system physiological decline rate across repeated visits.
          </p>
        </div>
      </div>

      {/* Navigation Handoff to Next Step */}
      <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-[#090d16] p-4">
        <div>
          <div className="text-xs font-semibold text-slate-200">Next Step in Phase 1 Research</div>
          <div className="text-[11px] text-slate-400">
            Investigate feature attributions using SHAP explainability and inspect candidate molecular biomarkers.
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/explainability"
            className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 px-3.5 py-1.5 text-xs font-medium text-slate-200 transition-colors"
          >
            <span>SHAP Explainability</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
          <Link
            href="/biomarkers"
            className="flex items-center gap-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 px-3.5 py-1.5 text-xs font-medium text-white transition-colors shadow-md shadow-cyan-950"
          >
            <span>Candidate Biomarkers</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
}
