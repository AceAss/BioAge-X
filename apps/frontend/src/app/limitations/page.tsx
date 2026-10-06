"use client";

import React from "react";
import Link from "next/link";
import { AlertTriangle, ShieldAlert, BookOpen, Layers, Dna, Network, Activity, HelpCircle } from "lucide-react";

export default function ScientificLimitationsPage() {
  const limitations = [
    {
      category: "Experimental & Epidemiological Design",
      title: "1. Cross-Sectional vs. Longitudinal Aging",
      icon: Activity,
      color: "text-amber-400 border-amber-500/20 bg-amber-950/10",
      description:
        "BioAge-X models trained on single-timepoint cohorts quantify cross-sectional age-associated molecular differences rather than individual longitudinal trajectories. Cross-sectional designs are vulnerable to cohort mortality selection and secular environmental trends.",
      guidance: "Do not interpret cross-sectional residuals as individual biological aging speed unless verified in repeated longitudinal cohorts (e.g. Dunedin longitudinal design).",
    },
    {
      category: "Biological & Anatomical Context",
      title: "2. Tissue Specificity & Cell-Type Heterogeneity",
      icon: Dna,
      color: "text-rose-400 border-rose-500/20 bg-rose-950/10",
      description:
        "Epigenetic and transcriptomic landscapes differ radically across human cell types and solid organs. A clock trained on whole blood (e.g. Hannum) measures leukocyte composite signals, which cannot be extrapolated to neurological, hepatic, or cardiac tissues.",
      guidance: "Always verify tissue compatibility tags. BioAge-X flags tissue mismatches with explicit scientific warnings.",
    },
    {
      category: "Population & Cohort Demographics",
      title: "3. Demographic Bias & Batch Effects",
      icon: Layers,
      color: "text-indigo-400 border-indigo-500/20 bg-indigo-950/10",
      description:
        "Training cohorts dominated by specific ancestral populations, narrow chronological age ranges, or unified geographic locations exhibit systematic covariate shift when applied to external cohorts. Inter-laboratory batch variations in array hybridization or RNA sequencing library prep introduce non-biological variance.",
      guidance: "Utilize Dataset Shift Analysis (KS tests, effect size divergence) before drawing conclusions about external model performance.",
    },
    {
      category: "Molecular Platform Coverage",
      title: "4. Missing Modalities & Epigenetic Probe Dropout",
      icon: AlertTriangle,
      color: "text-yellow-400 border-yellow-500/20 bg-yellow-950/10",
      description:
        "Canonical reference clocks (e.g., Horvath 353 CpGs, PhenoAge 513 CpGs) were developed on Illumina 27K and 450K arrays. Newer MethylationEPIC arrays and targeted panels omit specific historical probes, while RNA-seq datasets lack DNAm entirely.",
      guidance: "BioAge-X strictly reports PARTIAL_COVERAGE or UNAVAILABLE and lists missing loci without ever manufacturing missing features.",
    },
    {
      category: "Network Biology & Knowledge Bases",
      title: "5. Incompleteness of Public Interactome Graphs",
      icon: Network,
      color: "text-cyan-400 border-cyan-500/20 bg-cyan-950/10",
      description:
        "External biological databases (STRING, Reactome) reflect cumulative published literature and are inherently biased toward heavily investigated cancer, metabolic, and cardiovascular genes. Less-studied senescence effectors may lack recorded protein interactions.",
      guidance: "Network topologies represent curated computational models. Perform confidence-threshold sweeps to verify hub resilience.",
    },
    {
      category: "Causal Inference & Clinical Validity",
      title: "6. Non-Causality of SHAP Scores & GNN Embeddings",
      icon: ShieldAlert,
      color: "text-red-400 border-red-500/20 bg-red-950/10",
      description:
        "Shapley additive attributions (SHAP) and GNN graph attention weights denote mathematical predictive importance within a machine learning model, NOT biological essentiality or therapeutic causality. Correlated passenger genes frequently receive high attribution without driving cellular aging.",
      guidance: "All prioritized features are designated 'Candidate Aging-Associated Biomarkers' and require in vitro perturbation assays or CRISPR screens for causal validation.",
    },
  ];

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-12">
      {/* Header */}
      <div className="border-b border-slate-800 pb-5">
        <div className="flex items-center gap-2 text-xs font-mono text-amber-400 mb-1">
          <Link href="/dashboard" className="hover:underline">
            Dashboard
          </Link>
          <span>/</span>
          <span>ETHICS & RIGOR</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <ShieldAlert className="w-6 h-6 text-amber-400" />
          Scientific Limitations & Boundaries
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Explicit disclosure of methodological constraints, non-causal boundaries, and biological assumptions in BioAge-X v1.0.
        </p>
      </div>

      {/* Top Banner */}
      <div className="p-5 rounded-xl border border-amber-500/30 bg-amber-950/20 text-xs text-amber-200 leading-relaxed">
        <div className="font-bold uppercase tracking-wider text-amber-100 mb-1 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          Core Epistemological Principle
        </div>
        <p>
          BioAge-X is a computational biology discovery and modeling platform designed for academic and translational research.
          <strong> It does not provide medical diagnoses, clinical prognostic predictions, or therapeutic claims. </strong>
          Computational age acceleration estimates reflect mathematical residuals under specific statistical assumptions and
          must never substitute for comprehensive clinical evaluation.
        </p>
      </div>

      {/* Grid of Limitations */}
      <div className="space-y-6">
        {limitations.map((lim, i) => {
          const Icon = lim.icon;
          return (
            <div key={i} className={`p-6 rounded-xl border ${lim.color} space-y-3`}>
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase tracking-wider font-semibold opacity-75">
                  {lim.category}
                </span>
                <Icon className="w-5 h-5 opacity-80" />
              </div>
              <h2 className="text-base font-bold text-white tracking-tight">{lim.title}</h2>
              <p className="text-xs text-slate-300 leading-relaxed">{lim.description}</p>
              <div className="pt-3 border-t border-slate-800/60 text-xs font-mono text-slate-400">
                <span className="font-semibold text-slate-200">Mitigation & Guidance: </span>
                {lim.guidance}
              </div>
            </div>
          );
        })}
      </div>

      {/* Four Tier Taxonomy Reference */}
      <div className="p-6 rounded-xl border border-slate-800 bg-slate-900 space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-200 flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-cyan-400" />
          BioAge-X Four-Tier Evidence Taxonomy
        </h3>
        <p className="text-xs text-slate-400">
          To maintain strict scientific honesty, all outputs across the frontend, REST APIs, and reports are partitioned into four standardized tiers:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
          <div className="p-3 bg-slate-950 rounded border border-cyan-500/20">
            <span className="text-cyan-400 font-bold block mb-1">1. COMPUTATIONAL OUTPUT</span>
            <span className="text-slate-400 font-sans">
              Exact mathematical calculations produced by algorithms (e.g. MAE=3.4 yrs, SHAP=+0.42, GNN Loss=0.12).
            </span>
          </div>

          <div className="p-3 bg-slate-950 rounded border border-teal-500/20">
            <span className="text-teal-400 font-bold block mb-1">2. EXTERNAL BIOLOGICAL EVIDENCE</span>
            <span className="text-slate-400 font-sans">
              Facts documented in verified external databases (STRING PPI edges, Reactome pathways, Ensembl coordinates).
            </span>
          </div>

          <div className="p-3 bg-slate-950 rounded border border-purple-500/20">
            <span className="text-purple-400 font-bold block mb-1">3. MODEL-DERIVED HYPOTHESIS</span>
            <span className="text-slate-400 font-sans">
              Plausible biological interpretations suggested by statistical convergence (e.g. chromatin remodeling hypothesis).
            </span>
          </div>

          <div className="p-3 bg-slate-950 rounded border border-rose-500/20">
            <span className="text-rose-400 font-bold block mb-1">4. EXPERIMENTAL VALIDATION</span>
            <span className="text-slate-400 font-sans">
              Wet-lab biological confirmations (CRISPR KO, Western Blot, animal longevity assays) — NOT established by in silico software alone.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
