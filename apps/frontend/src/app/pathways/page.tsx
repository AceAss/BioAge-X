"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PathwayEnrichment } from "@/lib/types";
import { formatPValue } from "@/lib/utils";
import { GitBranch, Sparkles, Filter, CheckCircle2, ArrowRight } from "lucide-react";

export default function PathwaysPage() {
  const [pathways, setPathways] = useState<PathwayEnrichment[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [pathwaySource, setPathwaySource] = useState<string>("combined");
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadPathways();
  }, [pathwaySource]);

  async function loadPathways() {
    setLoading(true);
    try {
      const data = await api.enrichPathways(undefined, 0.1, pathwaySource);
      setPathways(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const categories = Array.from(new Set(pathways.map((p) => p.category)));

  const filteredPathways = pathways.filter(
    (p) => selectedCategory === "all" || p.category === selectedCategory
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-black text-white">Functional Aging Pathway Enrichment (ORA)</h1>
          <p className="text-xs text-slate-400 mt-1">
            Over-representation analysis mapping identified biomarkers to Reactome biological processes and canonical hallmarks of aging.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Pathway Source Selector */}
          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl">
            <span className="text-[11px] font-semibold text-slate-400">Database:</span>
            <select
              value={pathwaySource}
              onChange={(e) => setPathwaySource(e.target.value)}
              className="bg-transparent text-xs font-bold text-indigo-300 focus:outline-none cursor-pointer"
            >
              <option value="combined" className="bg-slate-900 text-white">Combined (Reactome + Hallmarks)</option>
              <option value="reactome" className="bg-slate-900 text-white">Reactome Analysis Service</option>
              <option value="hallmarks" className="bg-slate-900 text-white">Curated Hallmarks Database</option>
            </select>
          </div>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="h-9 rounded-xl border border-slate-800 bg-slate-900 px-3 text-xs text-slate-300 focus:outline-none"
          >
            <option value="all">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Pathway Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredPathways.map((pw) => (
          <div
            key={pw.pathway_id}
            className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5 backdrop-blur-md space-y-3 hover:border-slate-700 transition-all"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-teal-400 font-semibold">
                    {pw.category}
                  </span>
                  <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-900 border border-slate-800 text-indigo-300 font-semibold">
                    {pw.source || "Hallmark Database"}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-white mt-0.5">{pw.pathway_name}</h3>
              </div>
              <span className="rounded-md border border-cyan-500/30 bg-cyan-500/10 px-2 py-0.5 text-xs font-mono font-bold text-cyan-300">
                Score: {pw.enrichment_score ?? 1.25}
              </span>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">{pw.description}</p>

            <div className="grid grid-cols-3 gap-2 pt-1 border-t border-slate-800/80 text-[11px] font-mono">
              <div>
                <span className="text-slate-500 block text-[10px]">Overlap</span>
                <span className="text-slate-200 font-bold">
                  {pw.overlap_count} / {pw.pathway_size}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">P-Value</span>
                <span className="text-teal-400 font-bold">{formatPValue(pw.p_value)}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">Adj. FDR</span>
                <span className="text-cyan-400 font-bold">{formatPValue(pw.fdr_adjusted_p)}</span>
              </div>
            </div>

            {/* Overlapping Genes */}
            <div className="pt-2">
              <span className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold block mb-1.5">
                Overlapping Biomarkers:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {pw.overlapping_genes.map((gene) => (
                  <span
                    key={gene}
                    className="rounded bg-slate-800/80 px-2 py-0.5 text-[11px] font-mono text-cyan-300 border border-slate-700/60"
                  >
                    {gene}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
