"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  WorkflowStepper,
  WORKFLOW_STEPS,
} from "@/components/workflow/WorkflowStepper";
import { api } from "@/lib/api";
import { Dataset, Model, ModelMetrics, ShapBiomarker } from "@/lib/types";
import {
  Play,
  CheckCircle2,
  Cpu,
  Sparkles,
  Share2,
  FileSpreadsheet,
  ArrowRight,
  RefreshCw,
  Sliders,
  Database,
  Layers,
} from "lucide-react";

export default function AnalysisWorkflowPage() {
  const [currentStep, setCurrentStep] = useState<number>(3);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [modality, setModality] = useState<string>("multimodal");
  const [imputationStrategy, setImputationStrategy] = useState<string>("median");
  const [featureSelectionMethod, setFeatureSelectionMethod] = useState<string>("mutual_info");
  const [maxFeatures, setMaxFeatures] = useState<number>(40);
  const [modelType, setModelType] = useState<string>("XGBoost");
  
  // Execution states
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [latestAnalysis, setLatestAnalysis] = useState<any>(null);
  const [latestModel, setLatestModel] = useState<Model | null>(null);
  const [reportResult, setReportResult] = useState<any>(null);

  useEffect(() => {
    api.listDatasets().then((ds) => {
      setDatasets(ds);
      if (ds.length > 0) {
        setSelectedDatasetId(ds[0].id);
      }
    });
  }, []);

  async function handleRunFullPipeline() {
    if (!selectedDatasetId) return;
    setIsExecuting(true);
    try {
      // 1. Run Preprocessing & Feature Selection
      setCurrentStep(4);
      const ana = await api.runAnalysis(selectedDatasetId, {
        modality,
        imputation_strategy: imputationStrategy,
        min_variance: 0.001,
        max_features: maxFeatures,
        feature_selection_method: featureSelectionMethod,
      });
      setLatestAnalysis(ana);

      // 2. Train Model
      setCurrentStep(6);
      const trained = await api.trainModel(selectedDatasetId, modelType, {}, ana.id);
      setLatestModel(trained);

      // 3. Generate Report
      setCurrentStep(12);
      const rep = await api.generateReport(selectedDatasetId, trained.id, `Guided_Run_${modelType}`);
      setReportResult(rep);
    } catch (err) {
      console.error("Pipeline run error:", err);
    } finally {
      setIsExecuting(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* Page Title */}
      <div className="border-b border-slate-800 pb-5">
        <h1 className="text-2xl font-black text-white">Guided Computational Biology Analysis Workflow</h1>
        <p className="text-xs text-slate-400 mt-1">
          Follow the 12-step guided protocol from multi-omics data ingestion to model training, SHAP explainability, and PDF research report generation.
        </p>
      </div>

      {/* 12-Step Progress Stepper */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md">
        <WorkflowStepper currentStep={currentStep} onSelectStep={(s) => setCurrentStep(s)} />
      </div>

      {/* Configuration & Action Panels */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left: Pipeline Configuration */}
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md space-y-5">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
              <Sliders className="h-4 w-4 text-cyan-400" />
              Pipeline Configuration
            </h3>

            {/* Select Dataset */}
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                Target Dataset
              </label>
              <select
                value={selectedDatasetId}
                onChange={(e) => setSelectedDatasetId(e.target.value)}
                className="w-full rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2.5 text-xs text-white focus:border-cyan-500 focus:outline-none"
              >
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.n_samples} samples, {d.n_features} features, {d.detected_modality})
                  </option>
                ))}
              </select>
            </div>

            {/* Modality & Preprocessing */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                  Molecular Modality
                </label>
                <select
                  value={modality}
                  onChange={(e) => setModality(e.target.value)}
                  className="w-full rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs text-white focus:border-cyan-500 focus:outline-none"
                >
                  <option value="multimodal">Multi-Omics (Methylation + Transcriptomics)</option>
                  <option value="methylation">DNA Methylation Only (CpG Probes)</option>
                  <option value="transcriptomics">Transcriptomics Only (Gene Expression)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                  Missing Value Imputation
                </label>
                <select
                  value={imputationStrategy}
                  onChange={(e) => setImputationStrategy(e.target.value)}
                  className="w-full rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs text-white focus:border-cyan-500 focus:outline-none"
                >
                  <option value="median">Median Imputation</option>
                  <option value="mean">Mean Imputation</option>
                  <option value="zero">Zero Constant Imputation</option>
                </select>
              </div>
            </div>

            {/* Feature Selection & Model */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                  Feature Selection
                </label>
                <select
                  value={featureSelectionMethod}
                  onChange={(e) => setFeatureSelectionMethod(e.target.value)}
                  className="w-full rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs text-white focus:border-cyan-500 focus:outline-none"
                >
                  <option value="mutual_info">Mutual Information Regression</option>
                  <option value="model_based">Ridge Model Importance</option>
                  <option value="variance_only">Unsupervised Variance</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                  Max Biomarkers to Select
                </label>
                <input
                  type="number"
                  value={maxFeatures}
                  min={10}
                  max={200}
                  onChange={(e) => setMaxFeatures(Number(e.target.value))}
                  className="w-full rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs text-white focus:border-cyan-500 focus:outline-none font-mono"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                  Model Algorithm
                </label>
                <select
                  value={modelType}
                  onChange={(e) => setModelType(e.target.value)}
                  className="w-full rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs text-white focus:border-cyan-500 focus:outline-none"
                >
                  <option value="XGBoost">XGBoost Regression</option>
                  <option value="RandomForest">Random Forest Regression</option>
                  <option value="ElasticNet">ElasticNet (Epigenetic Clock)</option>
                  <option value="EarlyFusion">Early Multi-Omics Fusion</option>
                  <option value="LateFusion">Late Fusion (Meta-Regressor)</option>
                  <option value="WeightedEnsemble">Weighted Ensemble</option>
                </select>
              </div>
            </div>

            {/* Launch Button */}
            <div className="pt-2">
              <button
                onClick={handleRunFullPipeline}
                disabled={isExecuting || !selectedDatasetId}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-teal-500 px-6 py-3.5 text-xs font-bold text-slate-950 shadow-glow hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {isExecuting ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>Executing End-to-End Pipeline...</span>
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 fill-slate-950" />
                    <span>Execute Analysis Pipeline</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Right: Results / Progress Tracker */}
        <div className="space-y-4">
          <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5 backdrop-blur-md">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 mb-3">
              Workflow Status
            </h3>

            {latestModel ? (
              <div className="space-y-3">
                <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-300 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  <span>Model trained successfully ({latestModel.model_type})</span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5">
                    <span className="text-[10px] text-slate-500">MAE</span>
                    <p className="font-mono text-base font-bold text-teal-400">{latestModel.mae?.toFixed(2)} yrs</p>
                  </div>
                  <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5">
                    <span className="text-[10px] text-slate-500">R²</span>
                    <p className="font-mono text-base font-bold text-cyan-400">{latestModel.r2?.toFixed(3)}</p>
                  </div>
                </div>

                <div className="space-y-2 pt-2">
                  <Link
                    href="/explainability"
                    className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/40 p-2.5 text-xs text-slate-300 hover:border-cyan-500/40 hover:text-cyan-300 transition-colors"
                  >
                    <span>View SHAP attributions</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>

                  <Link
                    href="/network"
                    className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/40 p-2.5 text-xs text-slate-300 hover:border-cyan-500/40 hover:text-cyan-300 transition-colors"
                  >
                    <span>Explore biological network</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>

                  {reportResult?.pdf_url && (
                    <a
                      href={reportResult.pdf_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-between rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-2.5 text-xs text-emerald-300 hover:bg-emerald-500/20 transition-colors font-medium"
                    >
                      <span>Download Research PDF</span>
                      <FileSpreadsheet className="h-3.5 w-3.5" />
                    </a>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-500 leading-relaxed">
                Click &quot;Execute Analysis Pipeline&quot; to run data preprocessing, train the chosen model, compute SHAP explainability, and generate a downloadable report.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
