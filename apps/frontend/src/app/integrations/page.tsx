"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Globe,
  Database,
  Share2,
  GitBranch,
  Search,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Zap,
  Clock,
  Layers,
  ShieldCheck,
  Server,
  Trash2,
  ArrowRight,
  ExternalLink,
  Sliders,
  Sparkles,
} from "lucide-react";
import { ResearchQuestionPanel } from "@/components/ui/ResearchQuestionPanel";

interface ProviderDetails {
  provider: string;
  status: string;
  version?: string;
  latency_ms?: number;
  last_successful_request?: string;
  cached_records: number;
  message: string;
}

interface HealthData {
  string: string;
  reactome: string;
  ensembl: string;
  ncbi: string;
  gemini?: string;
  details: {
    string: ProviderDetails;
    reactome: ProviderDetails;
    ensembl: ProviderDetails;
    ncbi: ProviderDetails;
    gemini?: ProviderDetails;
  };
  cache: {
    total_records: number;
    by_provider: Record<string, number>;
    hits: number;
    misses: number;
    writes: number;
  };
}

export default function IntegrationsPage() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"overview" | "resolver" | "geo" | "settings">("overview");

  // Resolver Playground state
  const [inputIdentifiers, setInputIdentifiers] = useState<string>("cg16867657, CDKN2A, FOXO3, smoking_status, UNKNOWN_PROBE");
  const [resolvedResults, setResolvedResults] = useState<any[]>([]);
  const [resolving, setResolving] = useState<boolean>(false);

  // GEO Discovery state
  const [geoQuery, setGeoQuery] = useState<string>("human aging blood methylation");
  const [geoResults, setGeoResults] = useState<any[]>([]);
  const [geoSearching, setGeoSearching] = useState<boolean>(false);
  const [importStatus, setImportStatus] = useState<Record<string, string>>({});

  // Settings state
  const [enableLive, setEnableLive] = useState<boolean>(true);
  const [minStringScore, setMinStringScore] = useState<number>(0.4);
  const [cacheDurationDays, setCacheDurationDays] = useState<number>(7);
  const [requestTimeoutSec, setRequestTimeoutSec] = useState<number>(8);

  const fetchHealth = async () => {
    try {
      setRefreshing(true);
      const res = await fetch("http://localhost:8000/api/v1/integrations/health");
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      }
    } catch (err) {
      console.error("Health fetch error:", err);
    } finally {
      setRefreshing(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const handleResolveTest = async () => {
    setResolving(true);
    try {
      const ids = inputIdentifiers.split(",").map((s) => s.trim()).filter(Boolean);
      const res = await fetch("http://localhost:8000/api/v1/integrations/genes/resolve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identifiers: ids }),
      });
      if (res.ok) {
        const data = await res.json();
        setResolvedResults(data.resolved);
      }
    } catch (err) {
      console.error("Resolve error:", err);
    } finally {
      setResolving(false);
    }
  };

  const handleGeoSearch = async () => {
    setGeoSearching(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/integrations/geo/search?query=${encodeURIComponent(geoQuery)}`);
      if (res.ok) {
        const data = await res.json();
        setGeoResults(data.datasets);
      }
    } catch (err) {
      console.error("GEO search error:", err);
    } finally {
      setGeoSearching(false);
    }
  };

  const handleImportGeo = async (accession: string) => {
    setImportStatus((prev) => ({ ...prev, [accession]: "importing" }));
    try {
      const res = await fetch("http://localhost:8000/api/v1/integrations/geo/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accession }),
      });
      if (res.ok) {
        const data = await res.json();
        setImportStatus((prev) => ({ ...prev, [accession]: data.message || "Imported successfully" }));
      } else {
        const err = await res.json();
        setImportStatus((prev) => ({ ...prev, [accession]: `Error: ${err.detail || "Failed"}` }));
      }
    } catch (err) {
      setImportStatus((prev) => ({ ...prev, [accession]: "Network error" }));
    }
  };

  const handleClearCache = async () => {
    if (!confirm("Are you sure you want to clear the external biological knowledge cache?")) return;
    try {
      const res = await fetch("http://localhost:8000/api/v1/integrations/cache/clear", { method: "POST" });
      if (res.ok) {
        await fetchHealth();
        alert("Biological knowledge cache successfully invalidated.");
      }
    } catch (err) {
      console.error("Clear cache error:", err);
    }
  };

  const getStatusBadge = (status: string) => {
    const s = (status || "").toUpperCase();
    if (s === "AVAILABLE_NO_KEY" || s === "AVAILABLE" || s === "LIVE") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
          {s === "AVAILABLE_NO_KEY" ? "NO KEY NEEDED • ACTIVE" : "LIVE • OPERATIONAL"}
        </span>
      );
    }
    if (s === "AVAILABLE_WITH_KEY") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
          <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
          API KEY ACTIVE
        </span>
      );
    }
    if (s === "AUTH_REQUIRED") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
          KEY REQUIRED (.env)
        </span>
      );
    }
    if (s === "DISABLED") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/30">
          DISABLED (OPTIONAL)
        </span>
      );
    }
    if (s === "CACHED") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
          <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
          CACHED
        </span>
      );
    }
    if (s === "LOCAL_FALLBACK" || s === "DEGRADED") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
          LOCAL FALLBACK
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
        UNAVAILABLE
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-[#070a11] text-slate-100 p-6 md:p-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Globe className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                External Biological Knowledge Integration Layer
              </h1>
              <p className="text-xs text-slate-400">
                Live, traceable biological enrichment for Phase 1 biomarkers and Phase 2 interactomics with reproducible caching and deterministic local fallbacks.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchHealth}
            disabled={refreshing}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 border border-slate-700 transition"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin text-cyan-400" : ""}`} />
            Refresh Status
          </button>
          <button
            onClick={handleClearCache}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-rose-950/40 hover:bg-rose-900/60 text-xs font-medium text-rose-300 border border-rose-800/50 transition"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Clear Cache
          </button>
        </div>
      </div>

      {/* Scientific Framework Guide */}
      <ResearchQuestionPanel
        phase="Integration Layer: Multi-Provider Enrichment Architecture"
        question="How does BioAge-X integrate external biological interactomes without compromising scientific reproducibility or introducing runtime fragility?"
        hypothesis="A multi-tier adapter architecture (Cache → Live REST Provider → Curated Local Fallback) enables live biological annotation while guaranteeing deterministic, offline-capable research execution."
      />

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-800">
        {[
          { id: "overview", label: "Provider Health & Matrix", icon: Server },
          { id: "resolver", label: "Identifier Resolver", icon: DnaIcon },
          { id: "geo", label: "Public GEO Cohorts", icon: Database },
          { id: "settings", label: "Pipeline Settings", icon: Sliders },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 transition -mb-[2px] ${
                isActive
                  ? "border-cyan-400 text-cyan-300 bg-cyan-500/5"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* TAB 1: OVERVIEW & PROVIDER STATUS */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* STRING */}
            <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5 flex flex-col justify-between hover:border-cyan-500/40 transition">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Share2 className="h-5 w-5 text-cyan-400" />
                    <span className="font-bold text-sm text-white">STRING DB</span>
                  </div>
                  {getStatusBadge(health?.string || "local_fallback")}
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Primary interactome provider for Phase 2 GraphOmics-AI. Provides protein-protein physical and functional interactions with confidence scores and evidence breakdown.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-500">Release:</span>
                  <span className="text-slate-200 font-mono">{health?.details?.string?.version || "v12.0"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Latency:</span>
                  <span className="text-slate-200 font-mono">{health?.details?.string?.latency_ms ? `${health.details.string.latency_ms} ms` : "Local"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Fallback:</span>
                  <span className="text-emerald-400">aging_network_edges.csv</span>
                </div>
              </div>
            </div>

            {/* Reactome */}
            <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5 flex flex-col justify-between hover:border-indigo-500/40 transition">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <GitBranch className="h-5 w-5 text-indigo-400" />
                    <span className="font-bold text-sm text-white">Reactome</span>
                  </div>
                  {getStatusBadge(health?.reactome || "local_fallback")}
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Live pathway over-representation analysis (ORA) engine for candidate biomarkers with Benjamini-Hochberg FDR correction.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-500">Release:</span>
                  <span className="text-slate-200 font-mono">{health?.details?.reactome?.version || "Release 91"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Latency:</span>
                  <span className="text-slate-200 font-mono">{health?.details?.reactome?.latency_ms ? `${health.details.reactome.latency_ms} ms` : "Local"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Fallback:</span>
                  <span className="text-emerald-400">Curated Hallmarks Database</span>
                </div>
              </div>
            </div>

            {/* Ensembl */}
            <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5 flex flex-col justify-between hover:border-emerald-500/40 transition">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Layers className="h-5 w-5 text-emerald-400" />
                    <span className="font-bold text-sm text-white">Ensembl REST</span>
                  </div>
                  {getStatusBadge(health?.ensembl || "local_fallback")}
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Canonical gene model annotation service. Normalizes heterogeneous features, resolves Ensembl Gene IDs (ENSG...), genomic coordinates, and identifies ambiguous mappings.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-500">Genome Build:</span>
                  <span className="text-slate-200 font-mono">{health?.details?.ensembl?.version || "GRCh38 / Rel 113"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Latency:</span>
                  <span className="text-slate-200 font-mono">{health?.details?.ensembl?.latency_ms ? `${health.details.ensembl.latency_ms} ms` : "Local"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Fallback:</span>
                  <span className="text-emerald-400">Curated Clock Dictionary</span>
                </div>
              </div>
            </div>

            {/* NCBI / GEO */}
            <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5 flex flex-col justify-between hover:border-amber-500/40 transition">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="h-5 w-5 text-amber-400" />
                    <span className="font-bold text-sm text-white">NCBI / GEO</span>
                  </div>
                  {getStatusBadge(health?.ncbi || "available")}
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Public functional genomics discovery layer. Searches GEO DataSets for human aging cohorts, evaluates study compatibility, and provides safe single-click cohort activation.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-500">Service:</span>
                  <span className="text-slate-200 font-mono">Entrez E-Utilities v2.0</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Rate Limit:</span>
                  <span className="text-slate-200 font-mono">3 - 10 req/s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Fallback:</span>
                  <span className="text-emerald-400">GSE40279 Benchmark Cohort</span>
                </div>
              </div>
            </div>

            {/* Google Gemini */}
            <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5 flex flex-col justify-between hover:border-purple-500/40 transition">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-purple-400" />
                    <span className="font-bold text-sm text-white">Google Gemini</span>
                  </div>
                  {getStatusBadge(health?.gemini || "disabled")}
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Optional AI Research Assistant. Operates strictly downstream of ML, SHAP, and network computations for evidence-grounded natural-language synthesis.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-500">Model:</span>
                  <span className="text-slate-200 font-mono">{health?.details?.gemini?.version || "gemini-2.0-flash"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Auth:</span>
                  <span className="text-slate-200 font-mono">Optional GEMINI_API_KEY</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Safety:</span>
                  <span className="text-emerald-400">Evidence-Constrained</span>
                </div>
              </div>
            </div>
          </div>

          {/* Provider Capability Matrix Table (Requirement 18) */}
          <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Server className="h-4 w-4 text-cyan-400" />
                  Provider Capability & Authentication Matrix
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Comprehensive audit of all external services integrated into BioAge-X, authentication requirements, and runtime status.
                </p>
              </div>
            </div>

            <div className="overflow-x-auto border border-slate-800 rounded-lg">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="py-3 px-4 font-semibold">Provider</th>
                    <th className="py-3 px-4 font-semibold">Purpose</th>
                    <th className="py-3 px-4 font-semibold text-center">Search</th>
                    <th className="py-3 px-4 font-semibold text-center">Download</th>
                    <th className="py-3 px-4 font-semibold">Authentication</th>
                    <th className="py-3 px-4 font-semibold">Current Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  <tr className="hover:bg-slate-900/40">
                    <td className="py-3 px-4 font-medium text-white flex items-center gap-2">
                      <Share2 className="h-3.5 w-3.5 text-cyan-400" /> STRING DB
                    </td>
                    <td className="py-3 px-4">Protein-Protein Interactions</td>
                    <td className="py-3 px-4 text-center text-emerald-400 font-bold">✓</td>
                    <td className="py-3 px-4 text-center text-slate-500 font-mono">N/A</td>
                    <td className="py-3 px-4"><span className="text-emerald-400 font-medium">No Key Required</span></td>
                    <td className="py-3 px-4">{getStatusBadge(health?.string || "available_no_key")}</td>
                  </tr>
                  <tr className="hover:bg-slate-900/40">
                    <td className="py-3 px-4 font-medium text-white flex items-center gap-2">
                      <GitBranch className="h-3.5 w-3.5 text-indigo-400" /> Reactome
                    </td>
                    <td className="py-3 px-4">Biological Pathways & Hallmarks</td>
                    <td className="py-3 px-4 text-center text-emerald-400 font-bold">✓</td>
                    <td className="py-3 px-4 text-center text-slate-500 font-mono">N/A</td>
                    <td className="py-3 px-4"><span className="text-emerald-400 font-medium">No Key Required</span></td>
                    <td className="py-3 px-4">{getStatusBadge(health?.reactome || "available_no_key")}</td>
                  </tr>
                  <tr className="hover:bg-slate-900/40">
                    <td className="py-3 px-4 font-medium text-white flex items-center gap-2">
                      <Globe className="h-3.5 w-3.5 text-emerald-400" /> Ensembl
                    </td>
                    <td className="py-3 px-4">Gene Annotation & ID Resolution</td>
                    <td className="py-3 px-4 text-center text-emerald-400 font-bold">✓</td>
                    <td className="py-3 px-4 text-center text-slate-500 font-mono">N/A</td>
                    <td className="py-3 px-4"><span className="text-emerald-400 font-medium">No Key Required</span></td>
                    <td className="py-3 px-4">{getStatusBadge(health?.ensembl || "available_no_key")}</td>
                  </tr>
                  <tr className="hover:bg-slate-900/40">
                    <td className="py-3 px-4 font-medium text-white flex items-center gap-2">
                      <Database className="h-3.5 w-3.5 text-amber-400" /> NCBI / GEO
                    </td>
                    <td className="py-3 px-4">Dataset Discovery & Series Matrices</td>
                    <td className="py-3 px-4 text-center text-emerald-400 font-bold">✓</td>
                    <td className="py-3 px-4 text-center text-emerald-400 font-bold">✓</td>
                    <td className="py-3 px-4"><span className="text-cyan-400 font-medium">Optional API Key</span></td>
                    <td className="py-3 px-4">{getStatusBadge(health?.ncbi || "available_no_key")}</td>
                  </tr>
                  <tr className="hover:bg-slate-900/40">
                    <td className="py-3 px-4 font-medium text-white flex items-center gap-2">
                      <Database className="h-3.5 w-3.5 text-blue-400" /> ENA (EBI)
                    </td>
                    <td className="py-3 px-4">European Nucleotide Archive Reads</td>
                    <td className="py-3 px-4 text-center text-emerald-400 font-bold">✓</td>
                    <td className="py-3 px-4 text-center text-emerald-400 font-bold">✓</td>
                    <td className="py-3 px-4"><span className="text-emerald-400 font-medium">No Key Required</span></td>
                    <td className="py-3 px-4"><span className="text-xs text-emerald-400 font-medium">Available (Open Portal)</span></td>
                  </tr>
                  <tr className="hover:bg-slate-900/40">
                    <td className="py-3 px-4 font-medium text-white flex items-center gap-2">
                      <Database className="h-3.5 w-3.5 text-teal-400" /> BioStudies
                    </td>
                    <td className="py-3 px-4">Functional Expression Studies</td>
                    <td className="py-3 px-4 text-center text-emerald-400 font-bold">✓</td>
                    <td className="py-3 px-4 text-center text-emerald-400 font-bold">✓</td>
                    <td className="py-3 px-4"><span className="text-emerald-400 font-medium">No Key Required</span></td>
                    <td className="py-3 px-4"><span className="text-xs text-emerald-400 font-medium">Available (Open REST)</span></td>
                  </tr>
                  <tr className="hover:bg-slate-900/40">
                    <td className="py-3 px-4 font-medium text-white flex items-center gap-2">
                      <Database className="h-3.5 w-3.5 text-rose-400" /> GDC / TCGA
                    </td>
                    <td className="py-3 px-4">Cancer Multi-Omics & Clinical Age</td>
                    <td className="py-3 px-4 text-center text-emerald-400 font-bold">✓</td>
                    <td className="py-3 px-4 text-center text-emerald-400 font-bold">✓</td>
                    <td className="py-3 px-4"><span className="text-amber-400 font-medium">Open Access (Controlled BAMs: dbGaP)</span></td>
                    <td className="py-3 px-4"><span className="text-xs text-emerald-400 font-medium">Available (Open Matrices)</span></td>
                  </tr>
                  <tr className="hover:bg-slate-900/40">
                    <td className="py-3 px-4 font-medium text-white flex items-center gap-2">
                      <Database className="h-3.5 w-3.5 text-violet-400" /> PRIDE
                    </td>
                    <td className="py-3 px-4">Mass Spectrometry Proteomics</td>
                    <td className="py-3 px-4 text-center text-emerald-400 font-bold">✓</td>
                    <td className="py-3 px-4 text-center text-emerald-400 font-bold">✓</td>
                    <td className="py-3 px-4"><span className="text-emerald-400 font-medium">No Key Required</span></td>
                    <td className="py-3 px-4"><span className="text-xs text-emerald-400 font-medium">Available (Open Archive)</span></td>
                  </tr>
                  <tr className="hover:bg-slate-900/40">
                    <td className="py-3 px-4 font-medium text-white flex items-center gap-2">
                      <Database className="h-3.5 w-3.5 text-orange-400" /> MetaboLights
                    </td>
                    <td className="py-3 px-4">Metabolite Quantification Profiles</td>
                    <td className="py-3 px-4 text-center text-emerald-400 font-bold">✓</td>
                    <td className="py-3 px-4 text-center text-emerald-400 font-bold">✓</td>
                    <td className="py-3 px-4"><span className="text-emerald-400 font-medium">No Key Required</span></td>
                    <td className="py-3 px-4"><span className="text-xs text-emerald-400 font-medium">Available (Open Studies)</span></td>
                  </tr>
                  <tr className="hover:bg-slate-900/40">
                    <td className="py-3 px-4 font-medium text-white flex items-center gap-2">
                      <Sparkles className="h-3.5 w-3.5 text-purple-400" /> Google Gemini
                    </td>
                    <td className="py-3 px-4">Evidence-Constrained AI Interpretation</td>
                    <td className="py-3 px-4 text-center text-slate-500 font-mono">N/A</td>
                    <td className="py-3 px-4 text-center text-slate-500 font-mono">N/A</td>
                    <td className="py-3 px-4"><span className="text-purple-400 font-medium">Optional API Key (GEMINI_API_KEY)</span></td>
                    <td className="py-3 px-4">{getStatusBadge(health?.gemini || "disabled")}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Persistent Cache Inventory Card */}
          <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-sm text-white flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-cyan-400" />
                  Deterministic Cache & Provenance Inventory
                </h3>
                <p className="text-xs text-slate-400">
                  Every external request is stored on disk with cryptographic SHA-256 checksums to guarantee reproducibility.
                </p>
              </div>
              <div className="text-right">
                <span className="text-2xl font-bold font-mono text-cyan-400">{health?.cache?.total_records || 0}</span>
                <span className="text-xs text-slate-500 ml-1.5">cached entities</span>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
              <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-800">
                <div className="text-xs text-slate-500">Ensembl Mappings</div>
                <div className="text-lg font-bold font-mono text-slate-200">{health?.cache?.by_provider?.ensembl || 0}</div>
              </div>
              <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-800">
                <div className="text-xs text-slate-500">STRING Networks</div>
                <div className="text-lg font-bold font-mono text-slate-200">{health?.cache?.by_provider?.string || 0}</div>
              </div>
              <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-800">
                <div className="text-xs text-slate-500">Reactome Pathways</div>
                <div className="text-lg font-bold font-mono text-slate-200">{health?.cache?.by_provider?.reactome || 0}</div>
              </div>
              <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-800">
                <div className="text-xs text-slate-500">GEO Studies</div>
                <div className="text-lg font-bold font-mono text-slate-200">{health?.cache?.by_provider?.geo || 0}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: IDENTIFIER RESOLVER PLAYGROUND */}
      {activeTab === "resolver" && (
        <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-6 space-y-6">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <DnaIcon className="h-5 w-5 text-cyan-400" />
              Unified Multi-Omics Identifier Resolver
            </h2>
            <p className="text-xs text-slate-400">
              Test normalization pipeline: Raw feature → Modality detection → Ensembl lookup → Ambiguity check → Canonical representation.
            </p>
          </div>

          <div className="space-y-3">
            <label className="text-xs font-semibold text-slate-300">Comma-separated Features / Probes / Symbols:</label>
            <div className="flex gap-3">
              <input
                type="text"
                value={inputIdentifiers}
                onChange={(e) => setInputIdentifiers(e.target.value)}
                className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-cyan-400 font-mono"
                placeholder="cg16867657, CDKN2A, FOXO3, smoking_status..."
              />
              <button
                onClick={handleResolveTest}
                disabled={resolving}
                className="flex items-center gap-2 px-5 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black text-xs font-bold transition shadow-lg shadow-cyan-500/20"
              >
                {resolving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
                Resolve Live
              </button>
            </div>
          </div>

          {resolvedResults.length > 0 && (
            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="py-2.5 px-3">Input Feature</th>
                    <th className="py-2.5 px-3">Type</th>
                    <th className="py-2.5 px-3">Canonical Symbol</th>
                    <th className="py-2.5 px-3">Ensembl Gene ID</th>
                    <th className="py-2.5 px-3">Chromosome</th>
                    <th className="py-2.5 px-3">Source & Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80 font-mono">
                  {resolvedResults.map((r, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 text-white font-bold">{r.input_id}</td>
                      <td className="py-2 px-3 text-slate-400">{r.identifier_type}</td>
                      <td className="py-2 px-3 text-cyan-300 font-bold">{r.canonical_symbol || "—"}</td>
                      <td className="py-2 px-3 text-emerald-400">{r.ensembl_gene_id || "—"}</td>
                      <td className="py-2 px-3 text-slate-300">{r.chromosome || "—"}</td>
                      <td className="py-2 px-3">{getStatusBadge(r.status)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: PUBLIC GEO DISCOVERY */}
      {activeTab === "geo" && (
        <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-6 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Database className="h-5 w-5 text-amber-400" />
                NCBI / GEO Public Aging Cohort Discovery
              </h2>
              <p className="text-xs text-slate-400">
                Explore real human aging datasets before downloading. Inspect sample counts, platforms, and age annotations safely.
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <input
              type="text"
              value={geoQuery}
              onChange={(e) => setGeoQuery(e.target.value)}
              className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-amber-400 font-mono"
              placeholder="human aging blood methylation..."
            />
            <button
              onClick={handleGeoSearch}
              disabled={geoSearching}
              className="flex items-center gap-2 px-5 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-black text-xs font-bold transition shadow-lg shadow-amber-500/20"
            >
              {geoSearching ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              Search GEO
            </button>
          </div>

          <div className="space-y-4">
            {geoResults.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-500">
                Click &quot;Search GEO&quot; to discover landmark cohorts (e.g. GSE40279 Hannum blood, GSE87571, GSE111629).
              </div>
            ) : (
              geoResults.map((study, idx) => (
                <div key={idx} className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 space-y-3 hover:border-slate-700 transition">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono font-bold text-sm text-cyan-300">{study.accession}</span>
                      <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">
                        {study.omics_type}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        {study.compatibility_status}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <a
                        href={study.external_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-slate-400 hover:text-cyan-400 flex items-center gap-1"
                      >
                        NCBI Link <ExternalLink className="h-3 w-3" />
                      </a>
                      <button
                        onClick={() => handleImportGeo(study.accession)}
                        disabled={importStatus[study.accession] === "importing"}
                        className="px-3 py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 text-xs font-semibold border border-cyan-500/40 transition"
                      >
                        {importStatus[study.accession] === "importing" ? "Importing..." : "Import / Activate"}
                      </button>
                    </div>
                  </div>

                  <h4 className="text-sm font-semibold text-slate-100">{study.title}</h4>
                  <p className="text-xs text-slate-400 leading-relaxed">{study.summary}</p>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 pt-2 border-t border-slate-800/80 text-[11px] text-slate-400">
                    <div>
                      <span className="text-slate-500">Organism:</span> {study.organism}
                    </div>
                    <div>
                      <span className="text-slate-500">Samples:</span> {study.sample_count}
                    </div>
                    <div>
                      <span className="text-slate-500">Tissue:</span> {study.tissue || "Blood"}
                    </div>
                    <div>
                      <span className="text-slate-500">Age Metadata:</span>{" "}
                      {study.has_age_metadata ? (
                        <span className="text-emerald-400 font-semibold">Yes ({study.age_range || "Available"})</span>
                      ) : (
                        <span className="text-amber-400">Unspecified</span>
                      )}
                    </div>
                  </div>

                  {importStatus[study.accession] && (
                    <div className="text-xs px-3 py-1.5 rounded bg-cyan-950/40 text-cyan-300 border border-cyan-800">
                      {importStatus[study.accession]}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB 4: SETTINGS */}
      {activeTab === "settings" && (
        <div className="rounded-xl border border-slate-800 bg-[#0d1322] p-6 space-y-6 max-w-3xl">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Sliders className="h-5 w-5 text-cyan-400" />
              External Biological Knowledge Settings
            </h2>
            <p className="text-xs text-slate-400">
              Configure live enrichment toggles, cache policies, and STRING network confidence thresholds.
            </p>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-3.5 bg-slate-900/60 rounded-xl border border-slate-800">
              <div>
                <div className="font-semibold text-xs text-slate-200">Enable Live External Enrichment</div>
                <div className="text-[11px] text-slate-500">When disabled, BioAge-X strictly uses cached data and local interactomes.</div>
              </div>
              <input
                type="checkbox"
                checked={enableLive}
                onChange={(e) => setEnableLive(e.target.checked)}
                className="h-4 w-4 accent-cyan-400 cursor-pointer"
              />
            </div>

            <div className="p-3.5 bg-slate-900/60 rounded-xl border border-slate-800 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="font-semibold text-slate-200">STRING Confidence Score Threshold:</span>
                <span className="font-mono text-cyan-400 font-bold">{minStringScore.toFixed(3)}</span>
              </div>
              <input
                type="range"
                min="0.150"
                max="0.900"
                step="0.050"
                value={minStringScore}
                onChange={(e) => setMinStringScore(parseFloat(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-500">
                <span>0.150 (Low)</span>
                <span>0.400 (Medium - Recommended)</span>
                <span>0.700 (High)</span>
                <span>0.900 (Highest)</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="p-3.5 bg-slate-900/60 rounded-xl border border-slate-800 space-y-1">
                <label className="text-xs font-semibold text-slate-200">Cache TTL (Days):</label>
                <input
                  type="number"
                  value={cacheDurationDays}
                  onChange={(e) => setCacheDurationDays(parseInt(e.target.value) || 7)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white font-mono"
                />
              </div>

              <div className="p-3.5 bg-slate-900/60 rounded-xl border border-slate-800 space-y-1">
                <label className="text-xs font-semibold text-slate-200">Request Timeout (Seconds):</label>
                <input
                  type="number"
                  value={requestTimeoutSec}
                  onChange={(e) => setRequestTimeoutSec(parseInt(e.target.value) || 8)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white font-mono"
                />
              </div>
            </div>

            <div className="p-3.5 bg-slate-900/60 rounded-xl border border-slate-800 space-y-1">
              <div className="text-xs font-semibold text-slate-200">NCBI API Key Configuration:</div>
              <p className="text-[11px] text-slate-400">
                For increased rate limits (up to 10 req/s), set the environment variable <code className="text-cyan-300 font-mono">NCBI_API_KEY</code> in your backend <code className="text-cyan-300 font-mono">.env</code>. API keys are never exposed in frontend JavaScript.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function DnaIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M2 15c6.667-6 13.333 0 20-6" />
      <path d="M9 22c1.798-1.998 2.518-3.995 2.807-5.993" />
      <path d="M15 2c-1.798 1.998-2.518 3.995-2.807 5.993" />
      <path d="m17 6-2.5-2.5" />
      <path d="m14 8-1-1" />
      <path d="m7 18 2.5 2.5" />
      <path d="m3.5 14.5.5.5" />
      <path d="m20 9 .5.5" />
      <path d="m6.5 12.5 1 1" />
      <path d="m16.5 10.5 1 1" />
      <path d="m10 16 1 1" />
    </svg>
  );
}
