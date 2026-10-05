"use client";

import React, { useState } from "react";
import { SamplePrediction } from "@/lib/types";

interface AgeAccelerationScatterProps {
  predictions: SamplePrediction[];
}

export function AgeAccelerationScatter({ predictions }: AgeAccelerationScatterProps) {
  const [hovered, setHovered] = useState<SamplePrediction | null>(null);

  if (!predictions || predictions.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-slate-800 bg-slate-900/40 text-xs text-slate-500">
        No prediction data available.
      </div>
    );
  }

  const width = 500;
  const height = 340;
  const padding = 45;

  const minAge = 18;
  const maxAge = 88;

  const scaleX = (val: number) => padding + ((val - minAge) / (maxAge - minAge)) * (width - 2 * padding);
  const scaleY = (val: number) => height - padding - ((val - minAge) / (maxAge - minAge)) * (height - 2 * padding);

  return (
    <div className="relative rounded-xl border border-slate-800 bg-slate-950/70 p-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Predicted Biological Age vs. Chronological Age
        </h4>
        <div className="flex items-center gap-3 text-[11px]">
          <span className="flex items-center gap-1 text-rose-400">
            <span className="h-2 w-2 rounded-full bg-rose-500" /> Accelerated
          </span>
          <span className="flex items-center gap-1 text-emerald-400">
            <span className="h-2 w-2 rounded-full bg-emerald-500" /> Decelerated
          </span>
          <span className="flex items-center gap-1 text-sky-400">
            <span className="h-2 w-2 rounded-full bg-sky-500" /> Synchronous
          </span>
        </div>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto overflow-visible">
        {/* Grid lines */}
        {[20, 40, 60, 80].map((tick) => (
          <g key={tick}>
            <line
              x1={scaleX(tick)}
              y1={padding}
              x2={scaleX(tick)}
              y2={height - padding}
              stroke="#1e293b"
              strokeDasharray="2,2"
            />
            <line
              x1={padding}
              y1={scaleY(tick)}
              x2={width - padding}
              y2={scaleY(tick)}
              stroke="#1e293b"
              strokeDasharray="2,2"
            />
            {/* Axis labels */}
            <text x={scaleX(tick)} y={height - padding + 15} fill="#64748b" fontSize="10" textAnchor="middle">
              {tick}
            </text>
            <text x={padding - 10} y={scaleY(tick) + 3} fill="#64748b" fontSize="10" textAnchor="end">
              {tick}
            </text>
          </g>
        ))}

        {/* 45-degree Identity Line (y = x) */}
        <line
          x1={scaleX(minAge)}
          y1={scaleY(minAge)}
          x2={scaleX(maxAge)}
          y2={scaleY(maxAge)}
          stroke="#0ea5e9"
          strokeWidth="1.5"
          strokeDasharray="4,4"
          opacity="0.6"
        />

        {/* Axis borders */}
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#334155" />
        <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#334155" />

        {/* Points */}
        {predictions.map((p, idx) => {
          const cx = scaleX(p.chronological_age);
          const cy = scaleY(p.predicted_bio_age);
          const color =
            p.acceleration_status === "Accelerated"
              ? "#f43f5e"
              : p.acceleration_status === "Decelerated"
              ? "#10b981"
              : "#38bdf8";

          return (
            <circle
              key={idx}
              cx={cx}
              cy={cy}
              r={hovered?.sample_id === p.sample_id ? 6 : 3.5}
              fill={color}
              stroke="#090d16"
              strokeWidth={1}
              opacity={hovered?.sample_id === p.sample_id ? 1.0 : 0.8}
              className="cursor-pointer transition-all duration-150"
              onMouseEnter={() => setHovered(p)}
              onMouseLeave={() => setHovered(null)}
            />
          );
        })}
      </svg>

      {/* Axis titles */}
      <div className="flex justify-between text-[11px] text-slate-500 mt-1 px-10">
        <span>Chronological Age (years)</span>
        <span>Predicted Biological Age (years)</span>
      </div>

      {/* Tooltip drawer */}
      {hovered && (
        <div className="absolute top-12 right-6 rounded-lg border border-slate-700 bg-slate-900/95 p-2.5 text-xs shadow-glow backdrop-blur-md">
          <div className="font-semibold text-white mb-1">{hovered.sample_id}</div>
          <div className="text-slate-300">
            Chronological: <span className="font-mono text-cyan-400">{hovered.chronological_age}y</span>
          </div>
          <div className="text-slate-300">
            Biological: <span className="font-mono text-teal-400">{hovered.predicted_bio_age}y</span>
          </div>
          <div className="text-slate-300">
            Acceleration:{" "}
            <span
              className={`font-mono font-semibold ${
                hovered.age_acceleration > 0 ? "text-rose-400" : "text-emerald-400"
              }`}
            >
              {hovered.age_acceleration > 0 ? "+" : ""}
              {hovered.age_acceleration}y
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
