"use client";

import React, { useState } from "react";
import { api } from "@/lib/api";
import { GNNResult } from "@/lib/types";
import { Network, Play, RefreshCw, AlertCircle, CheckCircle2, Award } from "lucide-react";

export default function GNNPage() {
  const [architecture, setArchitecture] = useState<string>("GCN");
  const [epochs, setEpochs] = useState<number>(40);
  const [lr, setLr] = useState<number>(0.01);
  const [isTraining, setIsTraining] = useState<boolean>(false);
  const [gnnResult, setGnnResult] = useState<GNNResult | null>(null);

  async function handleTrainGNN() {
    setIsTraining(true);
    try {
      const res = await api.trainGNN(architecture, epochs, lr);
      setGnnResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsTraining(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-black text-white">Graph Neural Networks (PyTorch / PyG)</h1>
          <p className="text-xs text-slate-400 mt-1">
            Inductive message passing across molecular interaction topologies using GCN, GraphSAGE, and GAT architectures.
          </p>
        </div>
      </div>

      {/* Control Panel */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 mb-4 flex items-center gap-2">
          <Network className="h-4 w-4 text-purple-400" />
          GNN Architecture & Training Configuration
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1.5">
              GNN Architecture
            </label>
            <select
              value={architecture}
              onChange={(e) => setArchitecture(e.target.value)}
              className="w-full rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs text-white focus:outline-none"
            >
              <option value="GCN">Graph Convolutional Network (GCN)</option>
              <option value="GraphSAGE">GraphSAGE (Sample & Aggregate)</option>
              <option value="GAT">Graph Attention Network (GAT)</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1.5">
              Epochs: <span className="font-mono text-cyan-400">{epochs}</span>
            </label>
            <input
              type="range"
              min={10}
              max={100}
              step={10}
              value={epochs}
              onChange={(e) => setEpochs(Number(e.target.value))}
              className="w-full h-2 rounded-lg bg-slate-800 accent-cyan-500 cursor-pointer mt-2"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1.5">
              Learning Rate (Adam): <span className="font-mono text-teal-400">{lr}</span>
            </label>
            <select
              value={lr}
              onChange={(e) => setLr(Number(e.target.value))}
              className="w-full rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs text-white focus:outline-none font-mono"
            >
              <option value={0.05}>0.05</option>
              <option value={0.01}>0.01 (Default)</option>
              <option value={0.005}>0.005</option>
              <option value={0.001}>0.001</option>
            </select>
          </div>
        </div>

        <div className="mt-5">
          <button
            onClick={handleTrainGNN}
            disabled={isTraining}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-purple-500 to-indigo-500 px-6 py-2.5 text-xs font-bold text-white shadow-[0_0_20px_rgba(168,85,247,0.3)] hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {isTraining ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4 fill-white" />}
            {isTraining ? `Training ${architecture}...` : `Train ${architecture} on Molecular Graph`}
          </button>
        </div>
      </div>

      {/* Results */}
      {gnnResult && (
        <div className="space-y-6">
          {/* Test Performance Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
              <span className="text-[11px] text-slate-400">Architecture</span>
              <p className="text-xl font-bold font-mono text-purple-400 mt-1">
                {gnnResult.model_architecture}
              </p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
              <span className="text-[11px] text-slate-400">Test MSE</span>
              <p className="text-xl font-bold font-mono text-teal-400 mt-1">
                {gnnResult.test_mse.toFixed(4)}
              </p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
              <span className="text-[11px] text-slate-400">Test R² Score</span>
              <p className="text-xl font-bold font-mono text-cyan-400 mt-1">
                {gnnResult.test_r2.toFixed(3)}
              </p>
            </div>
          </div>

          {/* Node-Level Predictions Table */}
          <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 mb-4 flex items-center gap-2">
              <Award className="h-4 w-4 text-purple-400" />
              Node-Level Aging Association Predictions
            </h3>

            <div className="overflow-x-auto rounded-xl border border-slate-800/80">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-2.5">Rank</th>
                    <th className="px-4 py-2.5 font-sans font-semibold">Node Symbol</th>
                    <th className="px-4 py-2.5">Predicted Score</th>
                    <th className="px-4 py-2.5">Target Value</th>
                    <th className="px-4 py-2.5 font-sans font-semibold">Biomarker Prior</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-950/40">
                  {gnnResult.top_predicted_nodes.map((node, idx) => (
                    <tr key={node.node_id} className="hover:bg-slate-900/30">
                      <td className="px-4 py-2.5 text-slate-500">#{idx + 1}</td>
                      <td className="px-4 py-2.5 font-sans font-bold text-white flex items-center gap-2">
                        <span className="h-1.5 w-1.5 rounded-full bg-purple-400" />
                        {node.node_id}
                      </td>
                      <td className="px-4 py-2.5 font-bold text-purple-400">
                        {node.predicted_score.toFixed(3)}
                      </td>
                      <td className="px-4 py-2.5 text-slate-400">{node.true_score.toFixed(3)}</td>
                      <td className="px-4 py-2.5 font-sans">
                        <span
                          className={`rounded px-2 py-0.5 text-[10px] font-semibold ${
                            node.is_biomarker
                              ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/30"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          {node.is_biomarker ? "Seed Biomarker" : "Network Neighbor"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Scientific Caveat Alert */}
          <div className="flex items-start gap-3 rounded-xl border border-purple-500/30 bg-purple-500/10 p-4 text-xs text-purple-200">
            <AlertCircle className="h-4 w-4 shrink-0 text-purple-400 mt-0.5" />
            <span className="leading-relaxed">{gnnResult.disclaimer}</span>
          </div>
        </div>
      )}
    </div>
  );
}
