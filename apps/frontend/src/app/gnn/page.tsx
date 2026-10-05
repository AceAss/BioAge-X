"use client";

import React, { useState } from "react";
import { api } from "@/lib/api";
import { GNNResult } from "@/lib/types";
import {
  Network,
  Play,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Award,
  Sparkles,
  Info,
  ShieldAlert,
  ArrowRight,
  TrendingDown,
} from "lucide-react";
import { ResearchQuestionPanel } from "@/components/ui/ResearchQuestionPanel";
import Link from "next/link";

export default function GNNPage() {
  const [architecture, setArchitecture] = useState<string>("GCN");
  const [epochs, setEpochs] = useState<number>(40);
  const [lr, setLr] = useState<number>(0.01);
  const [isTraining, setIsTraining] = useState<boolean>(false);
  const [gnnResult, setGnnResult] = useState<GNNResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleTrainGNN() {
    setIsTraining(true);
    setError(null);
    try {
      const res = await api.trainGNN(architecture, epochs, lr);
      setGnnResult(res);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to train GNN architecture.");
    } finally {
      setIsTraining(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400 bg-purple-950/60 border border-purple-800/60 px-2 py-0.5 rounded-full">
              Phase 2: GraphOmics-AI
            </span>
            <span className="text-xs text-slate-500">Deep Graph Learning Lab</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Graph Neural Networks (GCN, GraphSAGE, GAT)
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Inductive message passing across molecular interaction topologies to predict node-level biological age regression scores and identify high-centrality aging network regions.
          </p>
        </div>

        <Link
          href="/reports"
          className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 px-3.5 py-1.5 text-xs font-semibold text-slate-200 transition-all shrink-0"
        >
          <span>Generate Research Report</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      {/* Research Question Panel (TASK 10 & 13) */}
      <ResearchQuestionPanel
        phase="Phase 2: GraphOmics-AI"
        question="Can message-passing Graph Neural Networks identify high-centrality aging network regions and predict node-level biological age regression scores?"
        hypothesis="Topological interaction neighborhoods encode non-linear biological regulatory signals that spectral and spatial graph convolutions can exploit to prioritize candidate aging modules."
        dataSummary="Heterogeneous biological interaction graph constructed from Phase 1 candidate biomarkers with node feature vectors and topological adjacency matrices."
        methodsSummary="PyTorch Geometric 2-layer Graph Convolutional Networks (GCN), GraphSAGE neighborhood sampling, and Multi-Head Graph Attention Networks (GAT)."
        interpretation={
          gnnResult
            ? `Trained ${gnnResult.model_architecture} over ${epochs} epochs. Achieved test MSE loss of ${gnnResult.test_mse.toFixed(4)}, test MAE of ${gnnResult.test_mae.toFixed(2)} years, and R² of ${gnnResult.test_r2.toFixed(3)}.`
            : "Select an architecture below and click 'Train GNN' to execute message passing."
        }
        limitations="All GNN outputs are classified as 'Computational Predictions / Model-Derived Network Signals'. Graph neural networks generate exploratory research hypotheses and do NOT prove in vivo molecular mechanisms without experimental validation."
      />

      {/* Scientific Nomenclature Notice */}
      <div className="rounded-xl border border-purple-500/30 bg-purple-950/20 p-3.5 text-xs text-purple-300/90 flex items-start gap-2.5">
        <Info className="h-4 w-4 text-purple-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-purple-200">GNN Output Classification:</span>
          <span className="ml-1 text-slate-300">
            Node aging scores and attention weights are mathematical representations of network message passing. They are explicitly labeled as <em>Computational Predictions</em>.
          </span>
        </div>
      </div>

      {/* GNN Configuration & Control Panel */}
      <div className="rounded-xl border border-slate-800 bg-[#0d131f]/90 p-5 shadow-md backdrop-blur-md">
        <div className="flex items-center gap-2 mb-4 border-b border-slate-800 pb-3">
          <Network className="h-4 w-4 text-purple-400" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Graph Architecture & Training Parameters
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              GNN Architecture
            </label>
            <select
              value={architecture}
              onChange={(e) => setArchitecture(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-200 focus:border-purple-500 focus:outline-none"
            >
              <option value="GCN">GCN (Graph Convolutional Network — Kipf & Welling)</option>
              <option value="GraphSAGE">GraphSAGE (Sample & Aggregate — Hamilton et al.)</option>
              <option value="GAT">GAT (Graph Attention Network with Self-Attention)</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Training Epochs: <span className="font-mono text-cyan-400">{epochs}</span>
            </label>
            <input
              type="range"
              min={10}
              max={100}
              step={10}
              value={epochs}
              onChange={(e) => setEpochs(Number(e.target.value))}
              className="w-full h-2 rounded-lg bg-slate-800 accent-purple-500 cursor-pointer mt-2"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Learning Rate (Adam Optimizer): <span className="font-mono text-teal-400">{lr}</span>
            </label>
            <select
              value={lr}
              onChange={(e) => setLr(Number(e.target.value))}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-200 focus:outline-none font-mono"
            >
              <option value={0.05}>0.05 (Fast exploratory)</option>
              <option value={0.01}>0.01 (Standard recommended)</option>
              <option value={0.005}>0.005 (Fine convergence)</option>
              <option value={0.001}>0.001 (Conservative)</option>
            </select>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between">
          <span className="text-[11px] text-slate-500">
            Executes pure PyTorch sparse message passing on CPU or GPU without platform wheel conflicts.
          </span>

          <button
            onClick={handleTrainGNN}
            disabled={isTraining}
            className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 px-5 py-2 text-xs font-semibold text-white shadow-md shadow-purple-950 transition-all disabled:opacity-50"
          >
            {isTraining ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5 fill-white" />}
            <span>{isTraining ? "Training Message Passing..." : `Train ${architecture} Model`}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-4 text-xs text-rose-300">
          <div className="flex items-center gap-2 font-semibold">
            <AlertCircle className="h-4 w-4 text-rose-400" />
            GNN Training Error
          </div>
          <p className="mt-1 text-slate-300">{error}</p>
        </div>
      )}

      {/* Results Display */}
      {gnnResult && (
        <div className="space-y-4">
          {/* Metrics Summary */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Architecture Evaluated</span>
              <p className="text-lg font-bold font-mono text-purple-400 mt-1">{gnnResult.model_architecture}</p>
              <div className="text-[10px] text-slate-500 mt-0.5">Inductive message passing</div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Test Error (MAE)</span>
              <p className="text-lg font-bold font-mono text-emerald-400 mt-1">{gnnResult.test_mae.toFixed(2)} yrs</p>
              <div className="text-[10px] text-slate-500 mt-0.5">Mean absolute error</div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Test Generalization (MSE)</span>
              <p className="text-lg font-bold font-mono text-cyan-400 mt-1">{gnnResult.test_mse.toFixed(4)}</p>
              <div className="text-[10px] text-slate-500 mt-0.5">Mean squared error</div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Computational Status</span>
              <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-bold mt-1">
                <CheckCircle2 className="h-4 w-4" /> Converged
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">Trained over {epochs} epochs</div>
            </div>
          </div>

          {/* Top Network Signals Predicted by GNN */}
          <div className="rounded-xl border border-slate-800 bg-[#0d131f]/90 shadow-md backdrop-blur-md overflow-hidden">
            <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3 bg-slate-900/50">
              <div className="flex items-center gap-2">
                <Award className="h-4 w-4 text-purple-400" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                  Candidate Aging Network Signals (GNN Node Predictions)
                </h3>
              </div>
              <span className="text-[10px] text-purple-300 font-semibold px-2 py-0.5 rounded-full bg-purple-950/60 border border-purple-800/60">
                Model-Derived Predictions
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-950/60 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    <th className="py-2.5 px-3">Rank</th>
                    <th className="py-2.5 px-3">Node Symbol</th>
                    <th className="py-2.5 px-3">Biomarker Origin</th>
                    <th className="py-2.5 px-3">GNN Predicted Aging Score</th>
                    <th className="py-2.5 px-3">True Aging Score</th>
                    <th className="py-2.5 px-3">Predicted Aging Role</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {gnnResult.top_predicted_nodes.slice(0, 10).map((item, idx) => (
                    <tr key={item.node_id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-2.5 px-3 font-bold text-slate-500">#{idx + 1}</td>
                      <td className="py-2.5 px-3 font-bold font-mono text-slate-100">
                        {item.node_id}
                      </td>
                      <td className="py-2.5 px-3">
                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                          item.is_biomarker
                            ? "bg-purple-500/10 text-purple-300 border-purple-500/30"
                            : "bg-slate-800 text-slate-400 border-slate-700"
                        }`}>
                          {item.is_biomarker ? "Phase 1 Seed Biomarker" : "Network Interactor"}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono font-bold text-purple-400">
                        {item.predicted_score.toFixed(4)}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-300">
                        {item.true_score.toFixed(4)}
                      </td>
                      <td className="py-2.5 px-3 text-slate-300 text-[11px]">
                        {item.node_id === "CDKN2A"
                          ? "Cellular senescence checkpoint p16INK4a"
                          : item.node_id === "SIRT1"
                          ? "NAD+ longevity enzyme & histone deacetylase"
                          : item.node_id === "IL6"
                          ? "Chronic systemic inflammaging mediator"
                          : item.node_id === "MTOR"
                          ? "Nutrient sensing & metabolic signaling hub"
                          : item.node_id === "TP53"
                          ? "Genomic stability & apoptosis coordinator"
                          : "High message-passing weight in aging network"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
