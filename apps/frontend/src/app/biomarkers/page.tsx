"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ShapBiomarker } from "@/lib/types";
import { Dna, Search, Filter, Sparkles, CheckCircle2, ArrowUpRight } from "lucide-react";

export default function BiomarkersPage() {
  const [biomarkers, setBiomarkers] = useState<ShapBiomarker[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [directionFilter, setDirectionFilter] = useState<string>("all");

  useEffect(() => {
    async function load() {
      try {
        const [models, datasets] = await Promise.all([api.listModels(), api.listDatasets()]);
        if (models.length > 0 && datasets.length > 0) {
          const res = await api.getExplainability(models[0].id, datasets[0].id, 30);
          setBiomarkers(res.global_biomarkers);
        }
      } catch (err) {
        console.error(err);
      }
    }
    load();
  }, []);

  const filteredBiomarkers = biomarkers.filter((bm) => {
    const matchesSearch =
      bm.gene_symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
      bm.feature.toLowerCase().includes(searchTerm.toLowerCase()) ||
      bm.biological_role.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDir = directionFilter === "all" || bm.direction === directionFilter;
    return matchesSearch && matchesDir;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-black text-white">Molecular Biomarkers & Aging Loci</h1>
          <p className="text-xs text-slate-400 mt-1">
            Prioritized epigenetic CpG probes and transcriptomic genes mapped to biological aging functions.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search gene or function..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="h-9 w-56 rounded-xl border border-slate-800 bg-slate-900 pl-9 pr-3 text-xs text-white placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none"
            />
          </div>

          <select
            value={directionFilter}
            onChange={(e) => setDirectionFilter(e.target.value)}
            className="h-9 rounded-xl border border-slate-800 bg-slate-900 px-3 text-xs text-slate-300 focus:outline-none"
          >
            <option value="all">All Effects</option>
            <option value="accelerates_age">Accelerating</option>
            <option value="decelerates_age">Decelerating</option>
          </select>
        </div>
      </div>

      {/* Biomarker Table */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md">
        <div className="overflow-x-auto rounded-xl border border-slate-800/80">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">Rank</th>
                <th className="px-4 py-3 font-sans font-semibold">Gene Symbol</th>
                <th className="px-4 py-3">Feature Locus</th>
                <th className="px-4 py-3 font-sans font-semibold">Modality</th>
                <th className="px-4 py-3 font-sans font-semibold">Aging Impact</th>
                <th className="px-4 py-3">Mean |SHAP|</th>
                <th className="px-4 py-3 font-sans font-semibold">Biological Role & Mechanism</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-950/40">
              {filteredBiomarkers.map((bm, idx) => {
                const isMeth = bm.feature.startsWith("cg");
                const isAccel = bm.direction === "accelerates_age";

                return (
                  <tr key={bm.feature} className="hover:bg-slate-900/40 transition-colors">
                    <td className="px-4 py-3 font-bold text-slate-500">#{idx + 1}</td>
                    <td className="px-4 py-3 font-sans font-black text-white text-sm">
                      {bm.gene_symbol}
                    </td>
                    <td className="px-4 py-3 text-cyan-400 font-mono text-[11px]">{bm.feature}</td>
                    <td className="px-4 py-3 font-sans">
                      <span
                        className={`rounded px-2 py-0.5 text-[10px] font-semibold ${
                          isMeth
                            ? "bg-teal-500/10 text-teal-300 border border-teal-500/30"
                            : "bg-purple-500/10 text-purple-300 border border-purple-500/30"
                        }`}
                      >
                        {isMeth ? "DNA Methylation" : "Transcriptomics"}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-sans">
                      <span
                        className={`inline-flex items-center gap-1 text-[11px] font-semibold ${
                          isAccel ? "text-rose-400" : "text-emerald-400"
                        }`}
                      >
                        <span className={`h-1.5 w-1.5 rounded-full ${isAccel ? "bg-rose-500" : "bg-emerald-500"}`} />
                        {isAccel ? "Accelerates Age" : "Decelerates Age"}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-bold text-cyan-400">{bm.mean_abs_shap.toFixed(3)}</td>
                    <td className="px-4 py-3 font-sans text-slate-300 max-w-md leading-relaxed text-[11px]">
                      {bm.biological_role}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
