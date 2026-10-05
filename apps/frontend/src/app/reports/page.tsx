"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { FileSpreadsheet, Download, RefreshCw, CheckCircle2, AlertCircle, Shield } from "lucide-react";

export default function ReportsPage() {
  const [reportData, setReportData] = useState<any>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  useEffect(() => {
    loadLatestReport();
  }, []);

  async function loadLatestReport() {
    try {
      const [datasets, models] = await Promise.all([api.listDatasets(), api.listModels()]);
      if (datasets.length > 0 && models.length > 0) {
        setIsGenerating(true);
        const rep = await api.generateReport(datasets[0].id, models[0].id, "BioAgeX_Cohort_Synthesis");
        setReportData(rep.report_data);
        setPdfUrl(rep.pdf_url);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-black text-white">Automated Scientific Research Reports</h1>
          <p className="text-xs text-slate-400 mt-1">
            Synthesized multi-omics research report compiling QC, benchmark metrics, SHAP biomarkers, and biological networks into a publication-grade PDF.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {pdfUrl && (
            <a
              href={pdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 px-5 py-2.5 text-xs font-bold text-slate-950 shadow-[0_0_20px_rgba(16,185,129,0.3)] hover:opacity-90 transition-opacity"
            >
              <Download className="h-4 w-4" />
              Download Scientific PDF
            </a>
          )}

          <button
            onClick={loadLatestReport}
            disabled={isGenerating}
            className="flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800 px-4 py-2.5 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 text-cyan-400 ${isGenerating ? "animate-spin" : ""}`} />
            {isGenerating ? "Generating..." : "Re-synthesize"}
          </button>
        </div>
      </div>

      {reportData && (
        <div className="space-y-6">
          {/* Document Header Card */}
          <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-4 mb-4">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-teal-400 font-semibold">
                  Official Research Document
                </span>
                <h2 className="text-lg font-bold text-white mt-0.5">{reportData.title}</h2>
                <p className="text-xs text-slate-400">{reportData.subtitle}</p>
              </div>

              <div className="text-right text-[11px] font-mono text-slate-400">
                <div>Date: {reportData.metadata?.generated_at}</div>
                <div>
                  Reproducibility Hash:{" "}
                  <code className="text-cyan-400">{reportData.metadata?.reproducibility_hash}</code>
                </div>
              </div>
            </div>

            {/* Executive Summary Stats */}
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 pt-2">
              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
                <span className="text-[10px] text-slate-400 uppercase font-mono">Cohort Samples</span>
                <p className="text-xl font-bold font-mono text-white mt-1">
                  {reportData.executive_summary?.sample_count}
                </p>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
                <span className="text-[10px] text-slate-400 uppercase font-mono">Model MAE</span>
                <p className="text-xl font-bold font-mono text-teal-400 mt-1">
                  {reportData.executive_summary?.model_mae_years?.toFixed(2)} yrs
                </p>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
                <span className="text-[10px] text-slate-400 uppercase font-mono">Top Biomarker</span>
                <p className="text-xl font-bold font-mono text-purple-400 mt-1">
                  {reportData.executive_summary?.top_biomarker}
                </p>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
                <span className="text-[10px] text-slate-400 uppercase font-mono">Top Pathway</span>
                <p className="text-xs font-bold text-cyan-400 mt-2 truncate">
                  {reportData.executive_summary?.top_pathway}
                </p>
              </div>
            </div>
          </div>

          {/* Model Performance & QC */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 mb-3">
                1. Dataset Quality Control Summary
              </h3>
              <div className="space-y-2 text-xs font-mono text-slate-300">
                <div>Dataset: <span className="text-white">{reportData.metadata?.dataset_name}</span></div>
                <div>Orientation: <span className="text-cyan-400">{reportData.dataset_qc?.orientation}</span></div>
                <div>Missing Fraction: <span className="text-teal-400">{(reportData.dataset_qc?.missing_fraction * 100).toFixed(2)}%</span></div>
                <div>Modality: <span className="text-purple-400">{reportData.dataset_qc?.detected_modality}</span></div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 mb-3">
                2. Model Performance Benchmarks
              </h3>
              <div className="space-y-2 text-xs font-mono text-slate-300">
                <div>Evaluated Model: <span className="text-white font-bold">{reportData.metadata?.model_name}</span></div>
                <div>Mean Absolute Error (MAE): <span className="text-teal-400 font-bold">{reportData.model_performance?.mae?.toFixed(2)} yrs</span></div>
                <div>R² Score: <span className="text-cyan-400 font-bold">{reportData.model_performance?.r2?.toFixed(3)}</span></div>
                <div>Pearson Correlation (r): <span className="text-slate-300">{reportData.model_performance?.pearson_r?.toFixed(3)}</span></div>
              </div>
            </div>
          </div>

          {/* Scientific Limitations */}
          <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md space-y-3">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
              <Shield className="h-4 w-4 text-cyan-400" />
              Scientific Scope & Methodological Disclaimers
            </h3>
            <ul className="space-y-2 text-xs text-slate-400">
              {reportData.scientific_limitations?.map((lim: string, idx: number) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-cyan-400 font-mono">•</span>
                  <span>{lim}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
