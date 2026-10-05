"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Dna,
  Search,
  Filter,
  Sparkles,
  CheckCircle2,
  ArrowRight,
  ShieldAlert,
  Share2,
  Layers,
  Info,
} from "lucide-react";
import { ResearchQuestionPanel } from "@/components/ui/ResearchQuestionPanel";

interface CandidateBiomarkerItem {
  feature_id: string;
  modality: string;
  scientific_term: string;
  mean_abs_shap: number;
  importance_rank: number;
  direction: string;
  gene_symbol?: string;
  protein_name?: string;
  pathway_name?: string;
  pathway_id?: string;
  biological_role?: string;
  chromosome?: string;
  feature_type?: string;
  validation_status: string;
  ensembl_gene_id?: string;
  external_source?: string;
  external_status?: string;
}

export default function BiomarkersPage() {
  const [candidates, setCandidates] = useState<CandidateBiomarkerItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [modalityFilter, setModalityFilter] = useState<string>("all");
  const [selectedModelName, setSelectedModelName] = useState<string>("");
  const [bridgePayload, setBridgePayload] = useState<any>(null);

  useEffect(() => {
    async function loadBiomarkers() {
      setLoading(true);
      try {
        const modelsRes = await fetch("http://localhost:8000/api/v1/models");
        if (modelsRes.ok) {
          const models = await modelsRes.json();
          if (models.length > 0) {
            setSelectedModelName(models[0].name);
            // Fetch formal Phase 1 -> Phase 2 bridge
            const bridgeRes = await fetch(`http://localhost:8000/api/v1/explain/bridge/${models[0].id}`);
            if (bridgeRes.ok) {
              const data = await bridgeRes.json();
              setBridgePayload(data.bridge_payload);
              if (data.bridge_payload && data.bridge_payload.candidates) {
                setCandidates(data.bridge_payload.candidates);
              }
            }
          }
        }
      } catch (err) {
        console.error("Failed to load biomarker bridge:", err);
      } finally {
        setLoading(false);
      }
    }
    loadBiomarkers();
  }, []);

  const filteredCandidates = candidates.filter((bm) => {
    const matchesSearch =
      (bm.gene_symbol && bm.gene_symbol.toLowerCase().includes(searchTerm.toLowerCase())) ||
      bm.feature_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (bm.biological_role && bm.biological_role.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (bm.pathway_name && bm.pathway_name.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesMod = modalityFilter === "all" || bm.modality.toLowerCase().includes(modalityFilter.toLowerCase());
    return matchesSearch && matchesMod;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 bg-cyan-950/60 border border-cyan-800/60 px-2 py-0.5 rounded-full">
              Phase 1: BioAge
            </span>
            <span className="text-xs text-slate-500">Biomarker Discovery & Biological Bridge</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Candidate Aging-Associated Biomarkers
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Model-derived molecular features prioritized through SHAP game-theoretic attribution and mapped to canonical human aging pathways.
          </p>
        </div>

        {/* Phase 2 Handoff Callout */}
        <Link
          href="/network"
          className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-purple-950/30 transition-all shrink-0"
        >
          <Share2 className="h-4 w-4" />
          <span>Continue to GraphOmics-AI</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      {/* Research Question Panel */}
      <ResearchQuestionPanel
        phase="Phase 1: BioAge"
        question="Do model-important molecular features represent coherent candidate biomarkers that bridge statistical prediction to biological interaction networks?"
        hypothesis="Features exerting the strongest SHAP contribution to biological age prediction map to known hallmarks of aging (senescence, epigenetic drift, inflammaging, nutrient sensing) and serve as seeds for interaction network topology."
        dataSummary="DNA methylation beta values (CpG sites), transcriptomic mRNA levels, and phenotypic covariates."
        methodsSummary="TreeExplainer SHAP values, feature importance rankings, genomic annotation mapping (CpG -> Gene -> Pathway), and cross-experiment consistency checks."
        interpretation={
          bridgePayload
            ? `Extracted ${bridgePayload.candidate_feature_count} candidate molecular features mapping to ${bridgePayload.mapped_seed_genes.length} unique seed genes ready for Phase 2 network analysis.`
            : "Features prioritize core aging regulators including ELOVL2, FHL2, CDKN2A, and SIRT1."
        }
        limitations="Features identified are classified as 'Candidate Aging-Associated Features' or 'Model-Associated Biomarkers'. They represent statistical and machine-learning associations, NOT experimentally validated causal drivers without independent wet-lab validation."
      />

      {/* Mandatory Terminology Notice */}
      <div className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-3.5 text-xs text-amber-300/90 flex items-start gap-2.5">
        <Info className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-amber-200">Scientific Nomenclature Policy:</span>
          <span className="ml-1 text-slate-300">
            BioAge-X explicitly distinguishes <em>&ldquo;model-important feature&rdquo;</em> from <em>&ldquo;validated biological biomarker&rdquo;</em>. All entries in this table are candidate features identified through in silico computational modeling on the active cohort.
          </span>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-800 bg-[#0d131f]/90 p-3 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search gene, probe ID, or pathway..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="h-8.5 w-64 rounded-lg border border-slate-700 bg-slate-900 pl-8 pr-3 text-xs text-slate-200 placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none"
            />
          </div>

          <select
            value={modalityFilter}
            onChange={(e) => setModalityFilter(e.target.value)}
            className="h-8.5 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-300 focus:outline-none"
          >
            <option value="all">All Modalities</option>
            <option value="methylation">DNA Methylation</option>
            <option value="transcript">Transcriptomics</option>
            <option value="clinical">Clinical Covariates</option>
          </select>
        </div>

        <div className="text-xs text-slate-400">
          Showing <strong className="text-slate-200">{filteredCandidates.length}</strong> prioritized candidate features
          {selectedModelName && <span> from model <span className="font-mono text-cyan-400">{selectedModelName}</span></span>}
        </div>
      </div>

      {/* Biomarker Table */}
      <div className="rounded-xl border border-slate-800 bg-[#0d131f]/90 shadow-md backdrop-blur-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                <th className="py-2.5 px-3">Rank</th>
                <th className="py-2.5 px-3">Feature Locus</th>
                <th className="py-2.5 px-3">Mapped Gene</th>
                <th className="py-2.5 px-3">Modality</th>
                <th className="py-2.5 px-3">Chromosome</th>
                <th className="py-2.5 px-3">Direction of Effect</th>
                <th className="py-2.5 px-3">Mean |SHAP|</th>
                <th className="py-2.5 px-3">Associated Pathway</th>
                <th className="py-2.5 px-3">Functional Role in Aging</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-500">
                    <Sparkles className="h-6 w-6 mx-auto mb-2 text-cyan-400 animate-spin" />
                    <p className="text-xs text-slate-400">Extracting candidate biomarkers from model SHAP attributions...</p>
                  </td>
                </tr>
              ) : filteredCandidates.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-500">
                    <Dna className="h-8 w-8 mx-auto mb-2 text-slate-600 opacity-60" />
                    <p className="font-medium text-slate-400">No candidate biomarkers match your query.</p>
                  </td>
                </tr>
              ) : (
                filteredCandidates.map((bm) => {
                  const isMeth = bm.modality.includes("Methylation");
                  const isAccel = bm.direction.includes("(+)");

                  return (
                    <tr key={bm.feature_id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-2.5 px-3 font-bold text-slate-500">#{bm.importance_rank}</td>
                      <td className="py-2.5 px-3 font-mono font-semibold text-cyan-300 text-[11px] whitespace-nowrap">
                        {bm.feature_id}
                      </td>
                      <td className="py-2.5 px-3 whitespace-nowrap">
                        <div className="font-bold text-slate-100">{bm.gene_symbol || "—"}</div>
                        {bm.ensembl_gene_id && (
                          <div className="font-mono text-[9px] text-emerald-400 font-medium">
                            {bm.ensembl_gene_id}
                          </div>
                        )}
                        <span className="inline-block mt-0.5 text-[8.5px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-mono border border-slate-700">
                          {bm.external_source?.includes("Ensembl") ? `Ensembl • ${bm.external_status || "LIVE"}` : "Curated • FALLBACK"}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 whitespace-nowrap">
                        <span
                          className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                            isMeth
                              ? "bg-teal-500/10 text-teal-300 border-teal-500/30"
                              : "bg-purple-500/10 text-purple-300 border-purple-500/30"
                          }`}
                        >
                          {bm.modality}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-400 font-mono text-[11px] whitespace-nowrap">
                        {bm.chromosome || "N/A"}
                      </td>
                      <td className="py-2.5 px-3 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center gap-1 text-[11px] font-semibold ${
                            isAccel ? "text-rose-400" : "text-emerald-400"
                          }`}
                        >
                          <span className={`h-1.5 w-1.5 rounded-full ${isAccel ? "bg-rose-500" : "bg-emerald-500"}`} />
                          {bm.direction}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-bold font-mono text-cyan-400 whitespace-nowrap">
                        {bm.mean_abs_shap.toFixed(4)}
                      </td>
                      <td className="py-2.5 px-3 text-slate-300 text-[11px] whitespace-nowrap">
                        {bm.pathway_name || "Epigenetics"}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400 text-[11px] max-w-xs truncate" title={bm.biological_role}>
                        {bm.biological_role || "Associated with age regression model."}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Biomarker to Biology Bridge Callout Banner */}
      <div className="rounded-xl border border-purple-500/30 bg-gradient-to-r from-purple-950/40 via-indigo-950/30 to-slate-900/60 p-5 shadow-lg backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-purple-300 bg-purple-950/80 border border-purple-700/60 px-2 py-0.5 rounded-full">
                Phase 1 → Phase 2 Handoff
              </span>
              <span className="text-xs text-slate-400">Biological Entity & Network Translation</span>
            </div>
            <h3 className="text-base font-bold text-slate-100 mt-1">
              Ready to Bridge Candidate Features into Biological Interaction Networks
            </h3>
            <p className="text-xs text-slate-300 max-w-2xl mt-1 leading-relaxed">
              These {candidates.length} molecular features will seed the Phase 2 GraphOmics-AI biological network.
              Construct protein-protein interactions, calculate topological centrality (degree, betweenness, PageRank), and run Graph Neural Networks (GCN, GraphSAGE, GAT).
            </p>
          </div>

          <Link
            href="/network"
            className="flex items-center gap-2 rounded-xl bg-purple-600 hover:bg-purple-500 px-5 py-2.5 text-xs font-semibold text-white shadow-lg shadow-purple-950 transition-all shrink-0"
          >
            <span>Launch GraphOmics-AI Workspace</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
