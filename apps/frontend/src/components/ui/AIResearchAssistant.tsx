"use client";

import React, { useState, useEffect } from "react";
import {
  Sparkles,
  Bot,
  BrainCircuit,
  FileText,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  Layers,
  ShieldCheck,
  RefreshCw,
  ExternalLink,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { api } from "@/lib/api";
import { AIStatus, AIInterpretation } from "@/lib/types";

interface AIResearchAssistantProps {
  evidence: Record<string, any>;
  experimentId?: string;
  contextTitle?: string;
}

export function AIResearchAssistant({
  evidence,
  experimentId,
  contextTitle = "Current Analysis",
}: AIResearchAssistantProps) {
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);
  const [loadingStatus, setLoadingStatus] = useState<boolean>(true);
  const [interpretation, setInterpretation] = useState<AIInterpretation | null>(null);
  const [generating, setGenerating] = useState<boolean>(false);
  const [activeTask, setActiveTask] = useState<string>("explain_results");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [showConfigHelp, setShowConfigHelp] = useState<boolean>(false);

  useEffect(() => {
    async function loadStatus() {
      try {
        const s = await api.getAIStatus();
        setAiStatus(s);
      } catch (e) {
        setAiStatus({
          enabled: false,
          configured: false,
          model: "gemini-2.0-flash",
          status: "DISABLED",
          message: "AI service unreachable or disabled",
        });
      } finally {
        setLoadingStatus(false);
      }
    }
    loadStatus();
  }, []);

  const handleInterpret = async (taskType: string) => {
    setActiveTask(taskType);
    setGenerating(true);
    setErrorMsg(null);
    try {
      const res = await api.interpretWithAI(taskType, evidence, experimentId);
      setInterpretation(res);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to generate AI interpretation.");
    } finally {
      setGenerating(false);
    }
  };

  const getStatusBadge = () => {
    if (loadingStatus) {
      return <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400">Checking...</span>;
    }
    if (!aiStatus?.enabled) {
      return (
        <span className="text-xs px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700 font-medium">
          AI Disabled (Optional)
        </span>
      );
    }
    if (!aiStatus?.configured) {
      return (
        <span className="text-xs px-2.5 py-1 rounded-full bg-amber-950/60 text-amber-300 border border-amber-800/60 font-medium">
          API Key Required (.env)
        </span>
      );
    }
    return (
      <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-950/60 text-emerald-300 border border-emerald-800/60 font-medium flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        Gemini Active ({aiStatus.model})
      </span>
    );
  };

  return (
    <div className="mt-8 rounded-xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl backdrop-blur-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-indigo-950/80 border border-indigo-700/50 text-indigo-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white tracking-tight">AI Research Assistant</h2>
              <span className="text-xs px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/50">
                Evidence-Constrained
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Grounded natural-language interpretation of computed metrics & biological evidence ({contextTitle}).
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          {getStatusBadge()}
          <button
            onClick={() => setShowConfigHelp(!showConfigHelp)}
            className="text-xs text-slate-400 hover:text-slate-200 transition-colors p-1"
            title="AI Configuration Help"
          >
            <HelpCircle className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Configuration Help Accordion */}
      {showConfigHelp && (
        <div className="my-4 p-4 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-300 space-y-2">
          <div className="flex items-center justify-between text-indigo-300 font-semibold">
            <span>Configuring Google Gemini for BioAge-X</span>
            <button onClick={() => setShowConfigHelp(false)} className="text-slate-400 hover:text-white">✕</button>
          </div>
          <p>
            Gemini acts as an <strong>optional, evidence-constrained research assistant</strong>. It operates strictly
            downstream of mathematical and statistical models and never invents biomarkers, alterations, or clinical claims.
          </p>
          <div className="font-mono bg-slate-900 p-2.5 rounded border border-slate-800 text-slate-200 space-y-1">
            <div>GEMINI_ENABLED=true</div>
            <div>GEMINI_API_KEY=your_google_ai_studio_key</div>
            <div>GEMINI_MODEL=gemini-2.0-flash</div>
          </div>
          <p className="text-slate-400">
            When disabled or unconfigured, BioAge-X continues 100% normal scientific computation with deterministic algorithmic summaries.
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="mt-5">
        <p className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2.5">
          Select Interpretation Task:
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          {[
            { id: "explain_results", label: "Explain Results", icon: BrainCircuit },
            { id: "summarize_experiment", label: "Summarize Experiment", icon: FileText },
            { id: "explain_biomarkers", label: "Explain Biomarkers", icon: Sparkles },
            { id: "explain_pathways", label: "Explain Pathways", icon: Layers },
            { id: "research_discussion", label: "Research Discussion", icon: Bot },
            { id: "limitations", label: "Generate Limitations", icon: AlertCircle },
          ].map((btn) => {
            const Icon = btn.icon;
            const isSelected = activeTask === btn.id;
            return (
              <button
                key={btn.id}
                onClick={() => handleInterpret(btn.id)}
                disabled={generating}
                className={`flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  isSelected && interpretation
                    ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/25 border border-indigo-500"
                    : "bg-slate-800/80 hover:bg-slate-750 text-slate-300 hover:text-white border border-slate-700/60"
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                <Icon className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">{btn.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Loading state */}
      {generating && (
        <div className="mt-6 p-6 rounded-lg bg-slate-950/60 border border-slate-800/80 flex flex-col items-center justify-center gap-3 text-center">
          <RefreshCw className="w-6 h-6 text-indigo-400 animate-spin" />
          <div>
            <p className="text-sm font-medium text-slate-200">Constraining Evidence & Synthesizing Interpretation...</p>
            <p className="text-xs text-slate-400 mt-1">Grounding observations against computed model metrics and verified biology.</p>
          </div>
        </div>
      )}

      {/* Error state */}
      {errorMsg && !generating && (
        <div className="mt-5 p-4 rounded-lg bg-red-950/30 border border-red-900/50 text-red-300 text-xs flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Interpretation Request Notice</p>
            <p className="mt-0.5 text-red-400/90">{errorMsg}</p>
          </div>
        </div>
      )}

      {/* Interpretation Output */}
      {interpretation && !generating && (
        <div className="mt-6 rounded-lg bg-slate-950/80 border border-slate-800 p-5 space-y-5">
          {/* Executive Summary */}
          <div>
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                Executive Synthesis
              </h3>
              {interpretation.cached && (
                <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                  CACHED RESPONSE
                </span>
              )}
            </div>
            <p className="text-sm text-slate-200 leading-relaxed mt-2 p-3.5 rounded-lg bg-slate-900/90 border border-slate-800/80">
              {interpretation.summary}
            </p>
          </div>

          {/* Observations & Empirical Findings */}
          {interpretation.observations?.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">
                Empirical Computational Observations
              </h4>
              <ul className="space-y-1.5 text-xs text-slate-300">
                {interpretation.observations.map((obs, idx) => (
                  <li key={idx} className="flex items-start gap-2 p-2 rounded bg-slate-900/50 border border-slate-800/40">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{obs}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Testable Hypotheses */}
          {interpretation.hypotheses?.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-indigo-300 uppercase tracking-wider mb-2">
                Grounded Testable Hypotheses
              </h4>
              <ul className="space-y-1.5 text-xs text-slate-300">
                {interpretation.hypotheses.map((hyp, idx) => (
                  <li key={idx} className="flex items-start gap-2 p-2 rounded bg-slate-900/50 border border-slate-800/40">
                    <BrainCircuit className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                    <span>{hyp}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Methodological Limitations */}
          {interpretation.limitations?.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2">
                Methodological Caveats & Limitations
              </h4>
              <ul className="space-y-1.5 text-xs text-slate-300">
                {interpretation.limitations.map((lim, idx) => (
                  <li key={idx} className="flex items-start gap-2 p-2 rounded bg-slate-900/50 border border-slate-800/40">
                    <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                    <span>{lim}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Evidence Sources */}
          {interpretation.evidence_sources?.length > 0 && (
            <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
              <span className="font-semibold text-slate-300">Evidence Sources:</span>
              {interpretation.evidence_sources.map((src, idx) => (
                <span key={idx} className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  {src}
                </span>
              ))}
            </div>
          )}

          {/* Compulsory Scientific Disclaimers */}
          <div className="pt-3 border-t border-slate-800/80 flex items-start gap-2 text-[11px] text-slate-500 leading-normal">
            <ShieldCheck className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-medium text-slate-400">Scientific Integrity Notice: </span>
              {interpretation.disclaimer}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
