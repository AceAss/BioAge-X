"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { NetworkData } from "@/lib/types";
import { CytoscapeGraph } from "@/components/network/CytoscapeGraph";
import { Share2, Network as NetIcon, Layers, Award, Sparkles, Filter } from "lucide-react";

export default function NetworkPage() {
  const [networkData, setNetworkData] = useState<NetworkData | null>(null);
  const [includePathways, setIncludePathways] = useState<boolean>(true);
  const [selectedNodeData, setSelectedNodeData] = useState<any>(null);

  useEffect(() => {
    loadNetwork();
  }, [includePathways]);

  async function loadNetwork() {
    try {
      const data = await api.buildNetwork(undefined, includePathways);
      setNetworkData(data);
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-black text-white">Biological Interaction Graph & Centrality Topology</h1>
          <p className="text-xs text-slate-400 mt-1">
            Construct molecular networks from aging biomarkers, compute PageRank & betweenness centrality, and detect functional communities.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs font-semibold text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={includePathways}
              onChange={(e) => setIncludePathways(e.target.checked)}
              className="rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-0"
            />
            <span>Include Pathway Membership Nodes</span>
          </label>
        </div>
      </div>

      {/* Network Stats Cards */}
      {networkData && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
            <span className="text-[11px] text-slate-400">Total Graph Nodes</span>
            <p className="text-2xl font-black font-mono text-cyan-400 mt-1">
              {networkData.summary.n_nodes}
            </p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
            <span className="text-[11px] text-slate-400">Molecular Edges</span>
            <p className="text-2xl font-black font-mono text-teal-400 mt-1">
              {networkData.summary.n_edges}
            </p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
            <span className="text-[11px] text-slate-400">Louvain Communities</span>
            <p className="text-2xl font-black font-mono text-purple-400 mt-1">
              {networkData.summary.n_communities}
            </p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
            <span className="text-[11px] text-slate-400">Connected Components</span>
            <p className="text-2xl font-black font-mono text-white mt-1">
              {networkData.summary.connected_components}
            </p>
          </div>
        </div>
      )}

      {/* Main Cytoscape Graph */}
      {networkData && (
        <CytoscapeGraph
          nodes={networkData.elements.nodes}
          edges={networkData.elements.edges}
          onSelectNode={(node) => setSelectedNodeData(node)}
        />
      )}

      {/* Centrality Rankings Table */}
      {networkData && (
        <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
              <Award className="h-4 w-4 text-cyan-400" />
              Top Network Hubs Ranked by Betweenness Centrality
            </h3>
            <span className="text-xs text-slate-500 font-mono">Structural bottlenecks in aging network</span>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800/80">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-2.5 font-sans font-semibold">Node ID</th>
                  <th className="px-4 py-2.5">Degree</th>
                  <th className="px-4 py-2.5">Degree Centrality</th>
                  <th className="px-4 py-2.5">Betweenness Centrality</th>
                  <th className="px-4 py-2.5">PageRank</th>
                  <th className="px-4 py-2.5">Community Cluster</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-slate-950/40">
                {networkData.centrality_top_nodes.slice(0, 10).map((n) => (
                  <tr key={n.node_id} className="hover:bg-slate-900/30">
                    <td className="px-4 py-2.5 font-sans font-bold text-white flex items-center gap-2">
                      <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
                      {n.node_id}
                    </td>
                    <td className="px-4 py-2.5 text-slate-300">{n.degree}</td>
                    <td className="px-4 py-2.5 text-slate-400">{n.degree_centrality.toFixed(3)}</td>
                    <td className="px-4 py-2.5 font-bold text-teal-400">{n.betweenness_centrality.toFixed(3)}</td>
                    <td className="px-4 py-2.5 text-cyan-400 font-bold">{n.pagerank.toFixed(3)}</td>
                    <td className="px-4 py-2.5 text-purple-400">Cluster #{n.community_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
