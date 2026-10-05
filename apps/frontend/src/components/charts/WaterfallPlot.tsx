"use client";

import React from "react";
import { WaterfallExplanation } from "@/lib/types";

interface WaterfallPlotProps {
  waterfall: WaterfallExplanation;
}

export function WaterfallPlot({ waterfall }: WaterfallPlotProps) {
  if (!waterfall || !waterfall.contributions) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-slate-800 bg-slate-900/40 text-xs text-slate-500">
        No local explanation data available.
      </div>
    );
  }

  const baseVal = waterfall.base_value;
  const predVal = waterfall.predicted_biological_age;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Local Waterfall Explanation ({waterfall.sample_id})
          </h4>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Cohort Base Expected Age: <span className="font-mono text-slate-300">{baseVal.toFixed(1)}y</span> → Predicted Biological Age: <span className="font-mono text-cyan-400 font-semibold">{predVal.toFixed(1)}y</span>
          </p>
        </div>
      </div>

      <div className="space-y-2.5">
        {waterfall.contributions.map((c, idx) => {
          const isPos = c.shap_value >= 0;
          return (
            <div key={idx} className="flex items-center gap-3 text-xs">
              <div className="w-28 text-right font-mono font-medium text-slate-300 truncate" title={c.feature}>
                {c.gene_symbol}
              </div>

              {/* Bar container */}
              <div className="relative flex-1 h-6 bg-slate-900/80 rounded border border-slate-800 flex items-center px-2">
                <div
                  className={`h-4 rounded ${
                    isPos
                      ? "bg-rose-500/80 border border-rose-400"
                      : "bg-emerald-500/80 border border-emerald-400"
                  }`}
                  style={{
                    width: `${Math.min(100, Math.max(8, Math.abs(c.shap_value) * 18))}%`,
                  }}
                />
                <span className="ml-2 font-mono text-[11px] font-semibold text-slate-200">
                  {isPos ? "+" : ""}{c.shap_value.toFixed(2)}y
                </span>
                <span className="ml-auto text-[10px] text-slate-400 truncate max-w-xs" title={c.biological_role}>
                  {c.biological_role}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
