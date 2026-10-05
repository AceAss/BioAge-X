"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Activity, Clock, Dna, FileText, Sparkles, Database } from "lucide-react";
import { api } from "@/lib/api";

export function Navbar() {
  const [backendHealth, setBackendHealth] = useState<string>("checking");

  useEffect(() => {
    api.getHealth().then((res) => {
      setBackendHealth(res.status === "healthy" ? "online" : "offline");
    });
  }, []);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800 bg-[#060913]/90 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between px-6">
        {/* Brand */}
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 via-teal-500 to-indigo-600 p-[1px] shadow-glow">
            <div className="flex h-full w-full items-center justify-center rounded-[11px] bg-slate-950">
              <Clock className="h-5 w-5 text-cyan-400 transition-transform group-hover:scale-110" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-black tracking-wider text-white">
                BIOAGE<span className="text-cyan-400">-X</span>
              </span>
              <span className="rounded border border-cyan-500/30 bg-cyan-500/10 px-1.5 py-0.2 text-[10px] font-mono font-medium text-cyan-300">
                v0.1.0-RESEARCH
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium">
              From molecular signals to biological age
            </p>
          </div>
        </Link>

        {/* Right Action Items */}
        <div className="flex items-center gap-4">
          {/* Backend Status indicator */}
          <div className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/60 px-3 py-1 text-xs">
            <span
              className={`h-2 w-2 rounded-full ${
                backendHealth === "online"
                  ? "bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]"
                  : "bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]"
              }`}
            />
            <span className="text-slate-300 font-mono text-[11px]">
              Engine: {backendHealth === "online" ? "Active (PyTorch/XGB)" : "Local Mode"}
            </span>
          </div>

          <Link
            href="/datasets"
            className="flex items-center gap-1.5 rounded-lg border border-teal-500/40 bg-teal-500/10 px-3 py-1.5 text-xs font-medium text-teal-300 hover:bg-teal-500/20 transition-colors"
          >
            <Database className="h-3.5 w-3.5" />
            <span>Load Demo Data</span>
          </Link>

          <Link
            href="/reports"
            className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 transition-colors"
          >
            <FileText className="h-3.5 w-3.5 text-cyan-400" />
            <span>Reports</span>
          </Link>
        </div>
      </div>
    </header>
  );
}
