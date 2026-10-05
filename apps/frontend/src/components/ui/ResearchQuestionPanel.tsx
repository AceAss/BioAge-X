"use client";

import React, { useState } from "react";
import { HelpCircle, ChevronDown, ChevronUp, Beaker, ShieldAlert, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface ResearchQuestionPanelProps {
  phase: string;
  question: string;
  hypothesis: string;
  dataSummary?: string;
  methodsSummary?: string;
  interpretation?: string;
  limitations?: string;
  className?: string;
}

export function ResearchQuestionPanel({
  phase,
  question,
  hypothesis,
  dataSummary = "Seed features, multi-omics matrices, and biological interaction networks.",
  methodsSummary = "Persistent caching, live REST querying, and deterministic local fallbacks.",
  interpretation,
  limitations = "External knowledge sources represent hypothesis-generating biological priors requiring experimental validation.",
  className,
}: ResearchQuestionPanelProps) {
  const [isOpen, setIsOpen] = useState(true);

  const isPhase1 = phase.includes("Phase 1");
  const badgeColor = isPhase1 ? "border-cyan-500/40 text-cyan-300 bg-cyan-950/40" : "border-purple-500/40 text-purple-300 bg-purple-950/40";
  const iconColor = isPhase1 ? "text-cyan-400" : "text-purple-400";

  return (
    <div className={cn("rounded-xl border border-slate-800 bg-[#0d131f]/90 p-4 shadow-lg backdrop-blur-md", className)}>
      <div className="flex items-center justify-between cursor-pointer select-none" onClick={() => setIsOpen(!isOpen)}>
        <div className="flex items-center gap-2.5">
          <div className={cn("flex h-7 w-7 items-center justify-center rounded-lg border", badgeColor)}>
            <Beaker className={cn("h-4 w-4", iconColor)} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className={cn("text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border", badgeColor)}>
                {phase} Scientific Contract
              </span>
              <span className="text-[11px] font-semibold text-slate-400">Formal Research Investigation</span>
            </div>
            <h3 className="text-sm font-semibold text-slate-100 mt-0.5">
              &ldquo;{question}&rdquo;
            </h3>
          </div>
        </div>
        <button className="text-slate-400 hover:text-slate-200 transition-colors p-1">
          {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </div>

      {isOpen && (
        <div className="mt-3.5 pt-3.5 border-t border-slate-800/80 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
          <div className="rounded-lg bg-slate-900/50 p-3 border border-slate-800/50">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-cyan-400 mb-1 flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
              Hypothesis
            </div>
            <p className="text-slate-300 text-[11px] leading-relaxed">{hypothesis}</p>
          </div>

          <div className="rounded-lg bg-slate-900/50 p-3 border border-slate-800/50">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-teal-400 mb-1 flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-teal-400" />
              Data & Methods
            </div>
            <p className="text-slate-300 text-[11px] leading-relaxed">
              <span className="font-semibold text-slate-200">Data:</span> {dataSummary}
              <br />
              <span className="font-semibold text-slate-200">Methods:</span> {methodsSummary}
            </p>
          </div>

          <div className="rounded-lg bg-slate-900/50 p-3 border border-slate-800/50">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-amber-400 mb-1 flex items-center gap-1.5">
              <Sparkles className="h-3 w-3" />
              Scientific Synthesis
            </div>
            <p className="text-slate-300 text-[11px] leading-relaxed">
              {interpretation || "Run benchmark to quantify cross-modality performance and epigenetic clock convergence."}
            </p>
          </div>

          <div className="rounded-lg bg-slate-900/50 p-3 border border-slate-800/50">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-rose-400 mb-1 flex items-center gap-1.5">
              <ShieldAlert className="h-3 w-3" />
              Research Caveats & Rigor
            </div>
            <p className="text-slate-400 text-[10px] leading-relaxed">{limitations}</p>
          </div>
        </div>
      )}
    </div>
  );
}
