"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Search,
  Database,
  Download,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Unlock,
  RefreshCw,
  Layers,
  FileCode,
  Globe,
  ArrowRight,
  X,
  Play,
  Info,
} from "lucide-react";
import { api } from "@/lib/api";
import {
  DataSourceSummary,
  DatasetSearchResult,
  DatasetMetadata,
  DownloadJob,
} from "@/lib/types";

export default function DatasetExplorerPage() {
  // Tabs: "search" | "capabilities" | "resolver" | "url_import" | "manifest"
  const [activeTab, setActiveTab] = useState<string>("search");

  // Capabilities
  const [sources, setSources] = useState<DataSourceSummary[]>([]);
  const [loadingSources, setLoadingSources] = useState<boolean>(false);

  // Search state
  const [searchQuery, setSearchQuery] = useState<string>("aging");
  const [selectedRepo, setSelectedRepo] = useState<string>("ALL");
  const [selectedModality, setSelectedModality] = useState<string>("ALL");
  const [selectedOrganism, setSelectedOrganism] = useState<string>("Homo sapiens");
  const [publicOnly, setPublicOnly] = useState<boolean>(false);
  const [searchResults, setSearchResults] = useState<DatasetSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Preview Modal / Card
  const [previewData, setPreviewData] = useState<DatasetMetadata | null>(null);
  const [previewLoading, setPreviewLoading] = useState<boolean>(false);

  // Direct Resolver
  const [resolverInput, setResolverInput] = useState<string>("GSE40279");
  const [resolverLoading, setResolverLoading] = useState<boolean>(false);

  // URL Importer
  const [urlInput, setUrlInput] = useState<string>("");
  const [urlName, setUrlName] = useState<string>("");
  const [urlAgeCol, setUrlAgeCol] = useState<string>("chronological_age");
  const [urlImporting, setUrlImporting] = useState<boolean>(false);
  const [importSuccess, setImportSuccess] = useState<string | null>(null);

  // Manifest Importer
  const sampleManifest = `dataset_id: "MULTIOMICS_COHORT_2025"
title: "Longitudinal Epigenetic & Transcriptomic Aging Cohort"
organism: "Homo sapiens"
tissue: "Whole Blood"
merge_strategy: "intersection"
target_age_column: "chronological_age"

modalities:
  methylation:
    source_type: "file"
    file_path: "data/example_datasets/demo_multiomics.csv"
    format: "csv"
    sample_id_column: "sample_id"
    feature_prefix: "cg"

  transcriptomics:
    source_type: "file"
    file_path: "data/example_datasets/demo_multiomics.csv"
    format: "csv"
    sample_id_column: "sample_id"
    feature_prefix: "GENE_"
`;
  const [manifestContent, setManifestContent] = useState<string>(sampleManifest);
  const [manifestImporting, setManifestImporting] = useState<boolean>(false);

  // Active Download Jobs
  const [activeJobs, setActiveJobs] = useState<DownloadJob[]>([]);

  useEffect(() => {
    loadCapabilities();
    performSearch();
  }, []);

  // Poll active download jobs
  useEffect(() => {
    const runningJobs = activeJobs.filter((j) => j.status === "PENDING" || j.status === "RUNNING");
    if (runningJobs.length === 0) return;

    const interval = setInterval(async () => {
      try {
        const updated = await Promise.all(
          runningJobs.map((j) => api.getDownloadJob(j.job_id))
        );
        setActiveJobs((prev) =>
          prev.map((job) => {
            const match = updated.find((u) => u.job_id === job.job_id);
            return match || job;
          })
        );
      } catch (e) {
        console.error("Failed to poll download jobs", e);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [activeJobs]);

  async function loadCapabilities() {
    setLoadingSources(true);
    try {
      const data = await api.getDataSources();
      setSources(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error("Failed to load capabilities:", e);
      setSources([]);
    } finally {
      setLoadingSources(false);
    }
  }

  async function performSearch() {
    setIsSearching(true);
    setSearchError(null);
    try {
      const results = await api.searchDatasets(searchQuery, {
        repository: selectedRepo === "ALL" ? undefined : selectedRepo,
        modality: selectedModality === "ALL" ? undefined : selectedModality,
        organism: selectedOrganism === "ALL" ? undefined : selectedOrganism,
        publicOnly,
      });
      setSearchResults(results);
    } catch (err: any) {
      setSearchError(err.message || "Failed to search biological repositories.");
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }

  async function handlePreview(provider: string, accession: string) {
    setPreviewLoading(true);
    setPreviewData(null);
    try {
      const meta = await api.previewDataset(provider, accession);
      setPreviewData(meta);
    } catch (err: any) {
      alert(`Preview failed: ${err.message}`);
    } finally {
      setPreviewLoading(false);
    }
  }

  async function handleStartDownload(provider: string, accession: string, optionId?: string) {
    try {
      const job = await api.startDownload(provider, accession, optionId);
      setActiveJobs((prev) => [job, ...prev.filter((j) => j.job_id !== job.job_id)]);
      alert(`Download job started: ${job.job_id} (${job.status})`);
    } catch (err: any) {
      alert(`Download request failed: ${err.message}`);
    }
  }

  async function handleCancelDownload(jobId: string) {
    try {
      const cancelled = await api.cancelDownloadJob(jobId);
      setActiveJobs((prev) => prev.map((j) => (j.job_id === jobId ? cancelled : j)));
    } catch (err: any) {
      alert(`Cancel failed: ${err.message}`);
    }
  }

  async function handleDirectResolve() {
    if (!resolverInput.trim()) return;
    setResolverLoading(true);
    try {
      const acc = resolverInput.trim().toUpperCase();
      let prov = "GEO";
      if (acc.startsWith("E-")) prov = "ArrayExpress";
      else if (acc.startsWith("S-") || acc.startsWith("BSST")) prov = "BioStudies";
      else if (acc.startsWith("PXD")) prov = "PRIDE";
      else if (acc.startsWith("MTBLS")) prov = "MetaboLights";
      else if (acc.startsWith("TCGA") || acc.startsWith("GDC")) prov = "GDC";
      else if (acc.startsWith("SRR") || acc.startsWith("SRP")) prov = "SRA";
      else if (acc.startsWith("ERR") || acc.startsWith("ERP")) prov = "ENA";

      await handlePreview(prov, acc);
    } finally {
      setResolverLoading(false);
    }
  }

  async function handleImportUrl() {
    if (!urlInput.trim()) return;
    setUrlImporting(true);
    setImportSuccess(null);
    try {
      const ds = await api.importDatasetFromUrl(urlInput.trim(), urlName || undefined, urlAgeCol || undefined);
      setImportSuccess(`Successfully imported dataset "${ds.name}" (${ds.n_samples} samples, ${ds.n_features} features).`);
      setUrlInput("");
    } catch (err: any) {
      alert(`URL import failed: ${err.message}`);
    } finally {
      setUrlImporting(false);
    }
  }

  async function handleImportManifest() {
    setManifestImporting(true);
    setImportSuccess(null);
    try {
      const ds = await api.importManifest(manifestContent);
      setImportSuccess(`Manifest assembled cohort: "${ds.name}" (${ds.n_samples} samples, ${ds.n_features} features, modality: ${ds.detected_modality}).`);
    } catch (err: any) {
      alert(`Manifest import failed: ${err.message}`);
    } finally {
      setManifestImporting(false);
    }
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 mb-2">
            <Globe className="w-3 h-3 animate-spin-slow" />
            Universal Biological Data Acquisition Layer
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Universal Biological Dataset Explorer
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Discover, preview, download, and auto-ingest real-world cohorts across GEO, ArrayExpress, BioStudies, GDC/TCGA, PRIDE, and MetaboLights.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/datasets"
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700/80 transition-all flex items-center gap-2"
          >
            <Database className="w-4 h-4 text-cyan-400" />
            Cohort Profiler &amp; Fallback
          </Link>
          <Link
            href="/analysis"
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-lg shadow-cyan-900/30 transition-all flex items-center gap-2"
          >
            <Play className="w-4 h-4" />
            Launch Guided Pipeline
          </Link>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-800 text-sm font-medium gap-1 overflow-x-auto">
        {[
          { id: "search", label: "Multi-Repository Search", icon: Search },
          { id: "capabilities", label: "Database Capability Matrix", icon: Layers },
          { id: "resolver", label: "Direct Accession Resolver", icon: ArrowRight },
          { id: "url_import", label: "Public HTTPS Importer", icon: Download },
          { id: "manifest", label: "Multi-Omics Manifest Importer", icon: FileCode },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-all whitespace-nowrap ${
                isActive
                  ? "border-cyan-400 text-cyan-300 bg-cyan-950/20 font-semibold"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Active Download Jobs Status Bar */}
      {activeJobs.length > 0 && (
        <div className="rounded-xl border border-cyan-500/30 bg-cyan-950/20 p-4 space-y-3 backdrop-blur-md">
          <div className="flex items-center justify-between text-xs text-cyan-300 font-semibold uppercase tracking-wider">
            <span className="flex items-center gap-2">
              <Download className="w-4 h-4 animate-bounce text-cyan-400" />
              Active Background Downloads ({activeJobs.length})
            </span>
          </div>
          <div className="space-y-3">
            {activeJobs.map((job) => (
              <div
                key={job.job_id}
                className="bg-slate-900/80 rounded-lg p-3 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
              >
                <div className="space-y-1 max-w-xl">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-cyan-300 font-bold">{job.job_id}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        job.status === "COMPLETED"
                          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                          : job.status === "FAILED"
                          ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                          : "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                      }`}
                    >
                      {job.status}
                    </span>
                    <span className="text-slate-400">{job.status_message}</span>
                  </div>
                  {job.status === "RUNNING" && (
                    <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden mt-1">
                      <div
                        className="bg-cyan-500 h-2 transition-all duration-300 rounded-full"
                        style={{ width: `${Math.round(job.progress * 100)}%` }}
                      />
                    </div>
                  )}
                  {job.total_bytes && (
                    <div className="text-[11px] text-slate-500 flex gap-3">
                      <span>{((job.downloaded_bytes || 0) / 1024 / 1024).toFixed(1)} MB / {(job.total_bytes / 1024 / 1024).toFixed(1)} MB</span>
                      {job.speed_bytes_sec && (
                        <span>Speed: {(job.speed_bytes_sec / 1024 / 1024).toFixed(2)} MB/s</span>
                      )}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {job.status === "RUNNING" && (
                    <button
                      onClick={() => handleCancelDownload(job.job_id)}
                      className="px-2.5 py-1 rounded bg-rose-950/40 text-rose-300 border border-rose-800/50 hover:bg-rose-900/60 transition-all flex items-center gap-1"
                    >
                      <X className="w-3 h-3" /> Cancel
                    </button>
                  )}
                  {job.status === "COMPLETED" && (
                    <Link
                      href="/datasets"
                      className="px-2.5 py-1 rounded bg-emerald-950/40 text-emerald-300 border border-emerald-800/50 hover:bg-emerald-900/60 transition-all flex items-center gap-1"
                    >
                      <Database className="w-3 h-3" /> View in Datasets
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 1: MULTI-REPOSITORY SEARCH */}
      {activeTab === "search" && (
        <div className="space-y-6">
          {/* Filter Bar */}
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-5 backdrop-blur-md space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
              <div className="md:col-span-5 relative">
                <Search className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && performSearch()}
                  placeholder="Search keywords, disease, accession (e.g. aging blood DNAm GSE40279)..."
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-lg pl-9 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
                />
              </div>

              <div className="md:col-span-2">
                <select
                  value={selectedRepo}
                  onChange={(e) => setSelectedRepo(e.target.value)}
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-lg px-3 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="ALL">All Repositories</option>
                  <option value="GEO">NCBI GEO</option>
                  <option value="ArrayExpress">ArrayExpress</option>
                  <option value="BioStudies">EMBL-EBI BioStudies</option>
                  <option value="GDC">GDC / TCGA</option>
                  <option value="PRIDE">PRIDE Proteomics</option>
                  <option value="MetaboLights">MetaboLights</option>
                  <option value="SRA">NCBI SRA</option>
                  <option value="ENA">EMBL-EBI ENA</option>
                </select>
              </div>

              <div className="md:col-span-2">
                <select
                  value={selectedModality}
                  onChange={(e) => setSelectedModality(e.target.value)}
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-lg px-3 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="ALL">All Modalities</option>
                  <option value="methylation">DNA Methylation</option>
                  <option value="transcriptomics">Transcriptomics</option>
                  <option value="proteomics">Proteomics</option>
                  <option value="metabolomics">Metabolomics</option>
                  <option value="multimodal">Multi-Omics</option>
                </select>
              </div>

              <div className="md:col-span-2">
                <select
                  value={selectedOrganism}
                  onChange={(e) => setSelectedOrganism(e.target.value)}
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-lg px-3 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="Homo sapiens">Homo sapiens</option>
                  <option value="Mus musculus">Mus musculus</option>
                  <option value="Rattus norvegicus">Rattus norvegicus</option>
                  <option value="ALL">All Organisms</option>
                </select>
              </div>

              <div className="md:col-span-1">
                <button
                  onClick={performSearch}
                  disabled={isSearching}
                  className="w-full h-full bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-medium rounded-lg px-4 py-2.5 flex items-center justify-center transition-all shadow-md shadow-cyan-900/20"
                >
                  {isSearching ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800">
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={publicOnly}
                    onChange={(e) => setPublicOnly(e.target.checked)}
                    className="rounded bg-slate-900 border-slate-700 text-cyan-500 focus:ring-0"
                  />
                  <span>Public &amp; Open Access Only</span>
                </label>
                <span className="text-slate-600">|</span>
                <span>Found <strong className="text-cyan-300 font-semibold">{searchResults.length}</strong> indexed biological series</span>
              </div>
              <div className="text-slate-500">
                Live query directly against repository REST metadata endpoints.
              </div>
            </div>
          </div>

          {/* Results Grid */}
          {searchError && (
            <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-950/20 text-rose-300 text-sm flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 flex-shrink-0" />
              <span>{searchError}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {searchResults.map((item) => (
              <div
                key={`${item.repository}-${item.accession}`}
                className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md flex flex-col justify-between hover:border-slate-700 hover:bg-slate-900/80 transition-all group"
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-cyan-300 border border-slate-700">
                        {item.repository}
                      </span>
                      <h3 className="font-mono text-base font-bold text-white mt-1 group-hover:text-cyan-300 transition-colors">
                        {item.accession}
                      </h3>
                    </div>
                    {item.access_restricted ? (
                      <span className="inline-flex items-center gap-1 text-[11px] text-amber-400 bg-amber-950/40 border border-amber-800/40 px-2 py-0.5 rounded">
                        <Lock className="w-3 h-3" /> Controlled (dbGaP)
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-2 py-0.5 rounded">
                        <Unlock className="w-3 h-3" /> Open Access
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-slate-300 line-clamp-3 leading-relaxed">
                    {item.title}
                  </p>

                  <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 bg-slate-950/50 p-2.5 rounded-lg border border-slate-800/50">
                    <div>
                      <span className="text-slate-500">Modality:</span>{" "}
                      <span className="text-slate-200 capitalize font-medium">{item.modality}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Organism:</span>{" "}
                      <span className="text-slate-200 font-medium">{item.organism}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Samples:</span>{" "}
                      <span className="text-cyan-300 font-medium">{item.sample_count}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Status:</span>{" "}
                      {item.requires_preprocessing ? (
                        <span className="text-amber-400 font-semibold">Raw Reads</span>
                      ) : (
                        <span className="text-emerald-400 font-semibold">Normalized Matrix</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="pt-4 mt-4 border-t border-slate-800/80 flex items-center justify-between gap-2">
                  <button
                    onClick={() => handlePreview(item.repository, item.accession)}
                    className="text-xs text-slate-300 hover:text-cyan-300 flex items-center gap-1 font-medium transition-colors"
                  >
                    <Info className="w-3.5 h-3.5" /> Details &amp; Files
                  </button>
                  <button
                    onClick={() => handleStartDownload(item.repository, item.accession)}
                    disabled={item.access_restricted}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-cyan-600/90 hover:bg-cyan-500 disabled:opacity-40 disabled:cursor-not-allowed text-white flex items-center gap-1.5 transition-all shadow-md shadow-cyan-900/20"
                  >
                    <Download className="w-3.5 h-3.5" /> Download
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 2: DATABASE CAPABILITY MATRIX */}
      {activeTab === "capabilities" && (
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur-md">
            <h2 className="text-lg font-bold text-white mb-1">Biological Repository Capability Matrix</h2>
            <p className="text-xs text-slate-400 mb-4">
              BioAge-X provides authentic native adapters across 12 major public repositories with automated accession resolution, metadata parsing, and stream ingestion.
            </p>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-950/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3">Repository</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">Search API</th>
                    <th className="px-4 py-3">Download Stream</th>
                    <th className="px-4 py-3">Auto-Ingestion</th>
                    <th className="px-4 py-3">Access Model</th>
                    <th className="px-4 py-3">Supported Accessions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {(sources || []).map((src) => (
                    <tr key={src.repository} className="hover:bg-slate-800/30">
                      <td className="px-4 py-3 font-semibold text-white">{src.repository}</td>
                      <td className="px-4 py-3 text-slate-400">{src.category}</td>
                      <td className="px-4 py-3">
                        {src.search_supported ? (
                          <span className="text-emerald-400 font-medium flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Native
                          </span>
                        ) : (
                          <span className="text-slate-500">Manifest only</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {src.download_supported ? (
                          <span className="text-emerald-400 font-medium flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Yes
                          </span>
                        ) : (
                          <span className="text-amber-400">Direct URL</span>
                        )}
                      </td>
                      <td className="px-4 py-3 font-mono text-[11px] text-cyan-300">
                        {src.auto_ingest}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            src.access_type === "OPEN_ACCESS"
                              ? "bg-emerald-950/40 text-emerald-400 border border-emerald-800/40"
                              : "bg-amber-950/40 text-amber-400 border border-amber-800/40"
                          }`}
                        >
                          {src.access_type}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-slate-400">
                        {src.supported_accessions.join(", ")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: DIRECT ACCESSION RESOLVER */}
      {activeTab === "resolver" && (
        <div className="max-w-2xl mx-auto space-y-6">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md space-y-4">
            <h2 className="text-lg font-bold text-white">Direct Repository Accession Resolver</h2>
            <p className="text-xs text-slate-400">
              Provide any biological accession from GEO, ArrayExpress, BioStudies, PRIDE, MetaboLights, or GDC. BioAge-X automatically resolves the target repository, queries metadata, and determines matrix ingestibility.
            </p>

            <div className="flex gap-2">
              <input
                type="text"
                value={resolverInput}
                onChange={(e) => setResolverInput(e.target.value)}
                placeholder="e.g. GSE40279, E-MTAB-6945, PXD000001, MTBLS1..."
                className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
              />
              <button
                onClick={handleDirectResolve}
                disabled={resolverLoading}
                className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-medium px-5 py-2.5 rounded-lg text-sm flex items-center gap-2 transition-all shadow-md shadow-cyan-900/20"
              >
                {resolverLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                Resolve Accession
              </button>
            </div>

            <div className="pt-2 text-xs text-slate-500 flex flex-wrap gap-2">
              <span className="text-slate-400">Quick Test Accessions:</span>
              {["GSE40279", "GSE87571", "E-MTAB-6945", "PXD000001", "MTBLS1"].map((acc) => (
                <button
                  key={acc}
                  onClick={() => {
                    setResolverInput(acc);
                  }}
                  className="px-2 py-0.5 rounded bg-slate-800 text-cyan-400 hover:bg-slate-700 font-mono transition-colors"
                >
                  {acc}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: PUBLIC HTTPS URL IMPORTER */}
      {activeTab === "url_import" && (
        <div className="max-w-2xl mx-auto space-y-6">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md space-y-4">
            <h2 className="text-lg font-bold text-white">Public HTTPS Dataset Importer</h2>
            <p className="text-xs text-slate-400">
              Download and auto-ingest datasets directly from any public HTTP/HTTPS URL, Zenodo DOI, or institutional repository URL (CSV, TSV, Parquet, H5AD).
            </p>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-slate-300 font-medium mb-1 block">Download URL</label>
                <input
                  type="text"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="https://example.org/aging_epigenome_matrix.csv"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-300 font-medium mb-1 block">Cohort Name (Optional)</label>
                  <input
                    type="text"
                    value={urlName}
                    onChange={(e) => setUrlName(e.target.value)}
                    placeholder="Blood Epigenetics 2025"
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-300 font-medium mb-1 block">Target Age Column</label>
                  <input
                    type="text"
                    value={urlAgeCol}
                    onChange={(e) => setUrlAgeCol(e.target.value)}
                    placeholder="chronological_age"
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <button
                onClick={handleImportUrl}
                disabled={urlImporting || !urlInput.trim()}
                className="w-full mt-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg text-sm flex items-center justify-center gap-2 transition-all shadow-md shadow-cyan-900/20"
              >
                {urlImporting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                Stream Download &amp; Ingest
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: MULTI-OMICS MANIFEST IMPORTER */}
      {activeTab === "manifest" && (
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-white">Multi-Omics Cohort Manifest Importer</h2>
                <p className="text-xs text-slate-400">
                  Ingest complex heterogeneous studies spanning DNA methylation, transcriptomics, proteomics, and metabolomics using standard YAML manifests.
                </p>
              </div>
              <span className="text-xs font-mono text-cyan-400 bg-cyan-950/40 px-2 py-1 rounded border border-cyan-800/40">
                YAML / JSON
              </span>
            </div>

            <div>
              <textarea
                rows={16}
                value={manifestContent}
                onChange={(e) => setManifestContent(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-4 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
              />
            </div>

            <button
              onClick={handleImportManifest}
              disabled={manifestImporting}
              className="w-full bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg text-sm flex items-center justify-center gap-2 transition-all shadow-md shadow-cyan-900/20"
            >
              {manifestImporting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <FileCode className="w-4 h-4" />}
              Validate Manifest &amp; Assemble Multi-Omics Cohort
            </button>
          </div>
        </div>
      )}

      {/* Notification banner */}
      {importSuccess && (
        <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/30 text-emerald-300 text-sm flex items-center justify-between gap-3 animate-fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-400" />
            <span>{importSuccess}</span>
          </div>
          <Link
            href="/datasets"
            className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-md text-xs transition-colors"
          >
            Go to Datasets
          </Link>
        </div>
      )}

      {/* PREVIEW MODAL */}
      {previewData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full p-6 space-y-5 shadow-2xl relative max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setPreviewData(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-cyan-950 text-cyan-300 border border-cyan-800">
                  {previewData.repository}
                </span>
                <span className="font-mono text-cyan-400 font-bold">{previewData.accession}</span>
              </div>
              <h2 className="text-lg font-bold text-white">{previewData.title}</h2>
              <p className="text-xs text-slate-400 mt-1">{previewData.organism} • {previewData.sample_count} Samples</p>
            </div>

            <div className="text-xs text-slate-300 bg-slate-950/60 p-3 rounded-lg border border-slate-800 leading-relaxed">
              {previewData.description || "No extended abstract description provided."}
            </div>

            {/* Compatibility Badge */}
            <div className="flex items-center justify-between text-xs p-3 rounded-lg bg-slate-800/60 border border-slate-700">
              <span className="text-slate-400">Compatibility Status:</span>
              <span
                className={`font-semibold ${
                  previewData.compatibility_status === "DIRECT_INGEST"
                    ? "text-emerald-400"
                    : previewData.compatibility_status === "ACCESS_RESTRICTED"
                    ? "text-rose-400"
                    : "text-amber-400"
                }`}
              >
                {previewData.compatibility_status || "ANALYSIS_READY"}
              </span>
            </div>

            {/* Download Options */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Available Study Files ({previewData.download_options.length})
              </h4>
              <div className="space-y-2">
                {previewData.download_options.map((opt) => (
                  <div
                    key={opt.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-xs"
                  >
                    <div>
                      <div className="font-medium text-slate-200">{opt.label}</div>
                      <div className="text-slate-500 font-mono text-[11px]">
                        Format: {opt.format} {opt.size_bytes ? `• ${(opt.size_bytes / 1024 / 1024).toFixed(1)} MB` : ""}
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        handleStartDownload(previewData.repository, previewData.accession, opt.id);
                        setPreviewData(null);
                      }}
                      className="px-3 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs flex items-center gap-1 transition-all"
                    >
                      <Download className="w-3.5 h-3.5" /> Download File
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {previewData.citation && (
              <div className="text-[11px] text-slate-500 border-t border-slate-800 pt-3">
                <strong>Citation:</strong> {previewData.citation}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
