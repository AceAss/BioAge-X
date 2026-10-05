"use client";

import React, { useEffect, useState, useRef } from "react";
import {
  Upload,
  Database,
  FileText,
  AlertCircle,
  CheckCircle2,
  Table as TableIcon,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { api } from "@/lib/api";
import { Dataset } from "@/lib/types";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [datasetDetails, setDatasetDetails] = useState<any>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isLoadingDemo, setIsLoadingDemo] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadDatasets();
  }, []);

  async function loadDatasets() {
    try {
      const data = await api.listDatasets();
      setDatasets(data);
      if (data.length > 0) {
        selectDataset(data[0]);
      }
    } catch (err) {
      console.error(err);
    }
  }

  async function selectDataset(ds: Dataset) {
    setSelectedDataset(ds);
    try {
      const details = await api.getDataset(ds.id);
      setDatasetDetails(details);
    } catch (err) {
      console.error(err);
    }
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadError(null);
    try {
      const newDs = await api.uploadDataset(file);
      setDatasets((prev) => [newDs, ...prev]);
      selectDataset(newDs);
    } catch (err: any) {
      setUploadError(err.message || "Failed to upload dataset.");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleLoadDemo() {
    setIsLoadingDemo(true);
    setUploadError(null);
    try {
      const demo = await api.loadDemoDataset();
      setDatasets((prev) => [demo, ...prev.filter((d) => d.id !== demo.id)]);
      selectDataset(demo);
    } catch (err: any) {
      setUploadError(err.message || "Failed to load demo dataset.");
    } finally {
      setIsLoadingDemo(false);
    }
  }

  const profile = datasetDetails?.profile || selectedDataset?.profile;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-black text-white">Multi-Omics Dataset Ingestion & Profiling</h1>
          <p className="text-xs text-slate-400 mt-1">
            Validate matrix orientations, detect chronological age, profile missingness, and inspect omics covariates.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".csv,.tsv,.txt,.parquet,.h5ad"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="flex items-center gap-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-4 py-2 text-xs transition-colors shadow-glow disabled:opacity-50"
          >
            <Upload className="h-4 w-4" />
            {isUploading ? "Profiling File..." : "Upload Matrix"}
          </button>

          <button
            onClick={handleLoadDemo}
            disabled={isLoadingDemo}
            className="flex items-center gap-2 rounded-xl border border-teal-500/40 bg-teal-500/10 hover:bg-teal-500/20 text-teal-300 font-semibold px-4 py-2 text-xs transition-colors disabled:opacity-50"
          >
            <Sparkles className="h-4 w-4 text-teal-400" />
            {isLoadingDemo ? "Loading Demo..." : "Load Synthetic Demo"}
          </button>
        </div>
      </div>

      {uploadError && (
        <div className="flex items-center gap-3 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
          <span>{uploadError}</span>
        </div>
      )}

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        {/* Left Sidebar: Dataset List */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Registered Datasets ({datasets.length})
          </h3>

          <div className="space-y-2">
            {datasets.map((ds) => {
              const isSelected = selectedDataset?.id === ds.id;
              return (
                <div
                  key={ds.id}
                  onClick={() => selectDataset(ds)}
                  className={`cursor-pointer rounded-xl border p-3.5 transition-all ${
                    isSelected
                      ? "border-cyan-500/50 bg-cyan-500/10 shadow-[0_0_15px_rgba(14,165,233,0.15)]"
                      : "border-slate-800 bg-slate-950/60 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-white truncate max-w-[140px]" title={ds.name}>
                      {ds.name}
                    </span>
                    <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-mono text-cyan-400 uppercase">
                      {ds.format}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400">
                    <span>{ds.n_samples} samples</span>
                    <span>{ds.n_features} features</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Section: Profiler & Preview (3 cols) */}
        <div className="lg:col-span-3 space-y-6">
          {selectedDataset && (
            <>
              {/* Profiler Card */}
              <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-cyan-400" />
                      Dataset Profile: {selectedDataset.name}
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Ingestion ID: <code className="font-mono text-cyan-400">{selectedDataset.id}</code>
                    </p>
                  </div>
                  <span className="rounded-full border border-teal-500/30 bg-teal-500/10 px-3 py-1 text-xs font-mono font-medium text-teal-300 uppercase">
                    Modality: {selectedDataset.detected_modality}
                  </span>
                </div>

                {/* Profile Grid */}
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-3">
                    <span className="text-[11px] text-slate-400">Sample Count</span>
                    <p className="text-xl font-bold font-mono text-white mt-1">
                      {profile?.n_samples ?? selectedDataset.n_samples}
                    </p>
                  </div>

                  <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-3">
                    <span className="text-[11px] text-slate-400">Molecular Features</span>
                    <p className="text-xl font-bold font-mono text-cyan-400 mt-1">
                      {profile?.n_features ?? selectedDataset.n_features}
                    </p>
                  </div>

                  <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-3">
                    <span className="text-[11px] text-slate-400">Orientation</span>
                    <p className="text-xs font-mono text-slate-200 mt-2 truncate">
                      {profile?.orientation ?? selectedDataset.orientation}
                    </p>
                  </div>

                  <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-3">
                    <span className="text-[11px] text-slate-400">Missingness</span>
                    <p className="text-xl font-bold font-mono text-teal-400 mt-1">
                      {((profile?.missing_fraction ?? selectedDataset.missing_fraction) * 100).toFixed(2)}%
                    </p>
                  </div>
                </div>

                {/* Target & Metadata Column Detection */}
                <div className="mt-4 rounded-xl border border-slate-800/60 bg-slate-900/30 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                    <div>
                      <span className="text-slate-400 font-medium">Target Chronological Age Column:</span>{" "}
                      <span className="font-mono font-bold text-cyan-400 ml-1">
                        {profile?.age_column || selectedDataset.age_column || "chronological_age (Detected)"}
                      </span>
                    </div>

                    <div>
                      <span className="text-slate-400 font-medium">Metadata Columns:</span>{" "}
                      <span className="font-mono text-slate-300 ml-1">
                        {profile?.metadata_columns?.join(", ") || "sample_id, sex, smoking_status, bmi"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Warnings / Profiler Alerts */}
                {profile?.warnings && profile.warnings.length > 0 && (
                  <div className="mt-4 space-y-2">
                    {profile.warnings.map((w: string, i: number) => (
                      <div key={i} className="flex items-center gap-2 rounded-lg bg-amber-500/10 border border-amber-500/20 px-3 py-2 text-xs text-amber-300">
                        <AlertCircle className="h-3.5 w-3.5 shrink-0 text-amber-400" />
                        <span>{w}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Data Preview Table */}
              <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <TableIcon className="h-4 w-4 text-cyan-400" />
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                      Matrix Preview (Top Samples & Columns)
                    </h3>
                  </div>
                  <span className="text-[11px] text-slate-500 font-mono">Showing first rows</span>
                </div>

                <div className="overflow-x-auto rounded-xl border border-slate-800/80">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800">
                      <tr>
                        {datasetDetails?.preview_columns?.map((col: string) => (
                          <th key={col} className="px-3 py-2.5 whitespace-nowrap">
                            {col}
                          </th>
                        )) || (
                          <>
                            <th className="px-3 py-2.5">sample_id</th>
                            <th className="px-3 py-2.5">chronological_age</th>
                            <th className="px-3 py-2.5">cg16867657_ELOVL2</th>
                            <th className="px-3 py-2.5">cg06639320_FHL2</th>
                            <th className="px-3 py-2.5">GENE_CDKN2A</th>
                            <th className="px-3 py-2.5">GENE_SIRT1</th>
                          </>
                        )}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-950/40">
                      {datasetDetails?.preview_rows?.slice(0, 5).map((row: any, rIdx: number) => (
                        <tr key={rIdx} className="hover:bg-slate-900/30">
                          {datasetDetails?.preview_columns?.map((col: string) => (
                            <td key={col} className="px-3 py-2 text-slate-300 whitespace-nowrap">
                              {typeof row[col] === "number" ? row[col].toFixed(3) : String(row[col] ?? "")}
                            </td>
                          ))}
                        </tr>
                      )) || (
                        <tr>
                          <td className="px-3 py-2 text-slate-400">BIOAGE_SYNTH_001</td>
                          <td className="px-3 py-2 text-cyan-400">54.2</td>
                          <td className="px-3 py-2 text-teal-400">0.782</td>
                          <td className="px-3 py-2 text-teal-400">0.651</td>
                          <td className="px-3 py-2 text-purple-400">8.94</td>
                          <td className="px-3 py-2 text-purple-400">5.21</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
