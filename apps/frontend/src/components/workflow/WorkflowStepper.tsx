"use client";

import React from "react";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export const WORKFLOW_STEPS = [
  { step: 1, label: "Upload Data", desc: "Ingest matrix" },
  { step: 2, label: "Profiling", desc: "Orientation & QC" },
  { step: 3, label: "Modality", desc: "Meth / RNA / Multi" },
  { step: 4, label: "Preprocessing", desc: "Impute & filter" },
  { step: 5, label: "Model Selection", desc: "XGB / RF / Elastic" },
  { step: 6, label: "Train & Predict", desc: "Estimate bio age" },
  { step: 7, label: "Metrics", desc: "MAE, RMSE, R²" },
  { step: 8, label: "SHAP Values", desc: "Beeswarm & local" },
  { step: 9, label: "Biomarkers", desc: "Rank loci" },
  { step: 10, label: "Bio Network", desc: "Centrality graph" },
  { step: 11, label: "GNN Analysis", desc: "Graph neural net" },
  { step: 12, label: "Research Report", desc: "Export PDF" },
];

interface WorkflowStepperProps {
  currentStep: number;
  onSelectStep?: (step: number) => void;
}

export function WorkflowStepper({ currentStep, onSelectStep }: WorkflowStepperProps) {
  return (
    <div className="w-full overflow-x-auto pb-2">
      <div className="flex items-center min-w-[900px] justify-between">
        {WORKFLOW_STEPS.map((s, idx) => {
          const isCompleted = s.step < currentStep;
          const isCurrent = s.step === currentStep;

          return (
            <React.Fragment key={s.step}>
              <div
                onClick={() => onSelectStep?.(s.step)}
                className={cn(
                  "flex flex-col items-center cursor-pointer group transition-all",
                  isCurrent ? "scale-105" : ""
                )}
              >
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold transition-all",
                    isCompleted
                      ? "bg-emerald-500 text-slate-950 font-black shadow-[0_0_10px_rgba(16,185,129,0.5)]"
                      : isCurrent
                      ? "bg-cyan-500 text-slate-950 ring-4 ring-cyan-500/20 shadow-glow"
                      : "bg-slate-800 text-slate-400 group-hover:bg-slate-700"
                  )}
                >
                  {isCompleted ? <Check className="h-4 w-4 stroke-[3]" /> : s.step}
                </div>
                <span
                  className={cn(
                    "mt-1.5 text-[11px] font-semibold text-center truncate max-w-[70px]",
                    isCurrent ? "text-cyan-300" : isCompleted ? "text-slate-300" : "text-slate-500"
                  )}
                >
                  {s.label}
                </span>
              </div>

              {idx < WORKFLOW_STEPS.length - 1 && (
                <div
                  className={cn(
                    "h-[2px] flex-1 mx-1.5 transition-all",
                    s.step < currentStep ? "bg-emerald-500/80" : "bg-slate-800"
                  )}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
