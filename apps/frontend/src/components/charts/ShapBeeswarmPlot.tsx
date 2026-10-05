"use client";

import React, { useState } from "react";
import { BeeswarmPoint, ShapBiomarker } from "@/lib/types";

interface ShapBeeswarmPlotProps {
  biomarkers: ShapBiomarker[];
  beeswarmPoints: BeeswarmPoint[];
}

export function ShapBeeswarmPlot({ biomarkers, beeswarmPoints }: ShapBeeswarmPlotProps) {
  const [hoveredPoint, setHoveredPoint] = useState<BeeswarmPoint | null>(null);

  if (!biomarkers || biomarkers.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-slate-800 bg-slate-900/40 text-xs text-slate-500">
        No SHAP summary data available.
      </div>
    );
  }

  const width = 600;
  const rowHeight = 36;
  const paddingX = 140;
  const height = biomarkers.length * rowHeight + 50;

  // Find min/max shap
  const shapVals = beeswarmPoints.map((p) => p.shap_value);
  const maxAbsShap = Math.max(...shapVals.map(Math.abs), 2.0);

  const scaleX = (val: number) => paddingX + ((val + maxAbsShap) / (2 * maxAbsShap)) * (width - paddingX - 30);

  return (
    <div className="relative rounded-xl border border-slate-800 bg-slate-950/70 p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          SHAP Beeswarm Summary (Feature Value Impact on Biological Age)
        </h4>
        <div className="flex items-center gap-2 text-[10px]">
          <span className="text-blue-400 font-mono">Low Value</span>
          <div className="h-2 w-16 rounded-full bg-gradient-to-r from-blue-500 via-purple-500 to-rose-500" />
          <span className="text-rose-400 font-mono">High Value</span>
        </div>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto overflow-visible">
        {/* Zero SHAP line */}
        <line
          x1={scaleX(0)}
          y1={10}
          x2={scaleX(0)}
          y2={height - 25}
          stroke="#475569"
          strokeWidth="1.5"
          strokeDasharray="3,3"
        />

        {biomarkers.map((bm, rowIdx) => {
          const yPos = 25 + rowIdx * rowHeight;
          const points = beeswarmPoints.filter((p) => p.feature === bm.feature);

          return (
            <g key={bm.feature}>
              {/* Row guideline */}
              <line x1={paddingX} y1={yPos} x2={width - 20} y2={yPos} stroke="#1e293b" />

              {/* Feature Name */}
              <text
                x={paddingX - 10}
                y={yPos + 4}
                fill="#cbd5e1"
                fontSize="11"
                fontFamily="monospace"
                textAnchor="end"
                className="font-medium"
              >
                {bm.gene_symbol}
              </text>

              {/* Beeswarm dots */}
              {points.map((pt, pIdx) => {
                const cx = scaleX(pt.shap_value);
                // Slight jitter along Y
                const jitter = ((pIdx % 5) - 2) * 2.5;
                const cy = yPos + jitter;

                // Color based on normalized feature value (0 = blue, 1 = red)
                const hue = 220 - pt.normalized_value * 220; // 220 (blue) to 0 (red)
                const color = `hsl(${hue}, 85%, 55%)`;

                return (
                  <circle
                    key={pIdx}
                    cx={cx}
                    cy={cy}
                    r={3.2}
                    fill={color}
                    opacity={0.8}
                    className="cursor-pointer hover:scale-150 transition-transform"
                    onMouseEnter={() => setHoveredPoint(pt)}
                    onMouseLeave={() => setHoveredPoint(null)}
                  />
                );
              })}
            </g>
          );
        })}

        {/* X Axis labels */}
        <text x={scaleX(-maxAbsShap)} y={height - 8} fill="#64748b" fontSize="10" textAnchor="middle">
          -{maxAbsShap.toFixed(1)}y
        </text>
        <text x={scaleX(0)} y={height - 8} fill="#64748b" fontSize="10" textAnchor="middle">
          0.0y
        </text>
        <text x={scaleX(maxAbsShap)} y={height - 8} fill="#64748b" fontSize="10" textAnchor="middle">
          +{maxAbsShap.toFixed(1)}y
        </text>
      </svg>

      <div className="flex justify-between text-[11px] text-slate-500 mt-1 px-32">
        <span>Decelerates Biological Age</span>
        <span>Accelerates Biological Age</span>
      </div>

      {hoveredPoint && (
        <div className="absolute top-12 right-6 rounded-lg border border-slate-700 bg-slate-900/95 p-2 text-xs shadow-glow backdrop-blur-md">
          <div className="font-semibold text-white">{hoveredPoint.sample_id}</div>
          <div className="text-slate-300">Feature: <span className="font-mono text-cyan-400">{hoveredPoint.feature}</span></div>
          <div className="text-slate-300">SHAP Impact: <span className="font-mono text-teal-400">{hoveredPoint.shap_value > 0 ? "+" : ""}{hoveredPoint.shap_value}y</span></div>
        </div>
      )}
    </div>
  );
}
