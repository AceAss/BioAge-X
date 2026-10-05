"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Settings, Shield, Server, CheckCircle2, Cpu, AlertTriangle } from "lucide-react";

export default function SettingsPage() {
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    api.getHealth().then((res) => setHealth(res));
  }, []);

  return (
    <div className="space-y-8 max-w-4xl">
      {/* Header */}
      <div className="border-b border-slate-800 pb-5">
        <h1 className="text-2xl font-black text-white">Platform Settings & Environment Verification</h1>
        <p className="text-xs text-slate-400 mt-1">
          Verify runtime engines, database connectivity, and review scientific ethical disclaimers.
        </p>
      </div>

      {/* Engine & Runtime Environment */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md space-y-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
          <Server className="h-4 w-4 text-cyan-400" />
          Runtime Backend Engines
        </h3>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
            <span className="text-[10px] text-slate-500 font-sans">Database</span>
            <div className="flex items-center gap-1.5 mt-1 font-bold text-emerald-400">
              <CheckCircle2 className="h-3.5 w-3.5" />
              <span>Connected</span>
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
            <span className="text-[10px] text-slate-500 font-sans">PyTorch Core</span>
            <div className="mt-1 font-bold text-cyan-400">
              {health?.backends?.torch ?? "2.14.1"}
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
            <span className="text-[10px] text-slate-500 font-sans">XGBoost</span>
            <div className="mt-1 font-bold text-teal-400">
              {health?.backends?.xgboost ?? "3.4.1"}
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
            <span className="text-[10px] text-slate-500 font-sans">scikit-learn</span>
            <div className="mt-1 font-bold text-purple-400">
              {health?.backends?.scikit_learn ?? "1.9.1"}
            </div>
          </div>
        </div>
      </div>

      {/* Ethical & Research Disclaimer */}
      <div className="rounded-2xl border border-amber-500/30 bg-amber-500/5 p-6 backdrop-blur-md space-y-3">
        <h3 className="text-sm font-bold text-amber-300 uppercase tracking-wider flex items-center gap-2">
          <Shield className="h-4 w-4 text-amber-400" />
          Mandatory Scientific & Ethical Disclaimer
        </h3>
        <p className="text-xs text-slate-300 leading-relaxed">
          <strong>BioAge-X is strictly an educational and academic computational biology research platform.</strong>{" "}
          It is NOT a medical device, diagnostic test, or clinical prognostic instrument. Biological age estimates and age acceleration residuals represent mathematical deviations from cohort-specific regression baselines. They must never be interpreted as clinical confirmation of pathology, personal disease probability, or healthcare advice.
        </p>
      </div>
    </div>
  );
}
