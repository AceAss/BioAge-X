"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { NetworkData } from "@/lib/types";
import { CytoscapeGraph } from "@/components/network/CytoscapeGraph";
import {
  Share2,
  Layers,
  Award,
  Sparkles,
  ArrowRight,
  Filter,
  CheckCircle2,
  Info,
  Network as NetIcon,
} from "lucide-react";
import { ResearchQuestionPanel } from "@/components/ui/ResearchQuestionPanel";

export default function NetworkPage() {
  const [networkData, setNetworkData] = useState<NetworkData | null>(null);
  const [includePathways, setIncludePathways] = useState<boolean>(true);
  const [networkSource, setNetworkSource] = useState<string>("hybrid");
  const [minConfidence, setMinConfidence] = useState<number>(0.4);
  const [selectedNodeData, setSelectedNodeData] = useState<any>(null);
  const [filterType, setFilterType] = useState<string>("all");
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadNetwork();
  }, [includePathways, networkSource, minConfidence]);

  async function loadNetwork() {
    setLoading(true);
    try {
      const data = await api.buildNetwork(undefined, includePathways, networkSource, minConfidence);
      setNetworkData(data);
    } catch (err) {
      console.error("Failed to build network:", err);
    } finally {
      setLoading(false);
    }
  }

  // Filter nodes if requested
  const nodes = networkData?.elements.nodes || [];
  const edges = networkData?.elements.edges || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400 bg-purple-950/60 border border-purple-800/60 px-2 py-0.5 rounded-full">
              Phase 2: GraphOmics-AI
            </span>
            <span className="text-xs text-slate-500">Biological Interaction Network</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Biological Interaction Graph & Centrality Topology
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Construct molecular networks from Phase 1 candidate biomarkers, compute PageRank & betweenness centrality, and detect functional communities.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Network Source Selector */}
          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 px-2.5 py-1 rounded-lg">
            <span className="text-[11px] font-semibold text-slate-400">Source:</span>
            <select
              value={networkSource}
              onChange={(e) => setNetworkSource(e.target.value)}
              className="bg-transparent text-xs font-bold text-cyan-300 focus:outline-none cursor-pointer"
            >
              <option value="hybrid" className="bg-slate-900 text-white">Hybrid (STRING + Local)</option>
              <option value="string" className="bg-slate-900 text-white">STRING DB Only</option>
              <option value="local" className="bg-slate-900 text-white">Local Interactome Only</option>
            </select>
          </div>

          {/* Status Badge */}
          <div className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[11px] font-mono">
            <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-slate-300 font-semibold">
              {networkData?.summary?.knowledge_status === "LIVE" ? "STRING • LIVE" : networkData?.summary?.knowledge_status === "CACHED" ? "STRING • CACHED" : "Local • FALLBACK"}
            </span>
          </div>

          <label className="flex items-center gap-2 text-xs font-semibold text-slate-300 cursor-pointer bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
            <input
              type="checkbox"
              checked={includePathways}
              onChange={(e) => setIncludePathways(e.target.checked)}
              className="rounded border-slate-700 bg-slate-800 text-purple-500 focus:ring-0"
            />
            <span>Include Pathway Nodes</span>
          </label>

          <Link
            href="/gnn"
            className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 px-3.5 py-1.5 text-xs font-semibold text-white shadow-md shadow-purple-950 transition-all shrink-0"
          >
            <span>Proceed to GNN Lab</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      {/* Research Question Panel */}
      <ResearchQuestionPanel
        phase="Phase 2: GraphOmics-AI"
        question="Do molecular features associated with biological-age prediction form coherent biological interaction networks that can be characterized using graph-based learning?"
        hypothesis="Candidate aging biomarkers identified in Phase 1 cluster within canonical hallmark interaction modules whose topological and spectral embeddings reflect cellular senescence, epigenetic remodeling, and inflammaging."
        dataSummary="Seed genes and proteins mapped from Phase 1 SHAP features, connected via curated biological interaction edges and hallmark pathway memberships."
        methodsSummary="NetworkX graph construction, degree & betweenness centrality computation, PageRank stationary distribution, and Louvain modularity community detection."
        interpretation={
          networkData
            ? `Graph contains ${networkData.summary.n_nodes} nodes and ${networkData.summary.n_edges} edges across ${networkData.summary.n_communities} detected communities with graph density of ${(networkData.summary.density ?? 0.045).toFixed(4)}.`
            : "Building graph topology..."
        }
        limitations="Interactions are derived from curated biological knowledge bases and edge lists. Centrality ranks prioritize topological bottlenecks in silico and require experimental validation."
      />

      {/* Network Stats Cards */}
      {networkData && (
        <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Total Graph Nodes</span>
            <p className="text-xl font-bold font-mono text-cyan-400 mt-1">
              {networkData.summary.n_nodes}
            </p>
            <div className="text-[10px] text-slate-500 mt-0.5">Genes, proteins & pathways</div>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Molecular Interactions</span>
            <p className="text-xl font-bold font-mono text-teal-400 mt-1">
              {networkData.summary.n_edges}
            </p>
            <div className="text-[10px] text-slate-500 mt-0.5">Interaction & regulation edges</div>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Louvain Communities</span>
            <p className="text-xl font-bold font-mono text-purple-400 mt-1">
              {networkData.summary.n_communities}
            </p>
            <div className="text-[10px] text-slate-500 mt-0.5">Functional sub-networks</div>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Connected Components</span>
            <p className="text-xl font-bold font-mono text-slate-200 mt-1">
              {networkData.summary.connected_components}
            </p>
            <div className="text-[10px] text-slate-500 mt-0.5">Independent graph partitions</div>
          </div>
        </div>
      )}

      {/* Main Cytoscape Graph Visualization */}
      {networkData && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <span className="font-semibold text-slate-200 flex items-center gap-1.5">
              <NetIcon className="h-3.5 w-3.5 text-purple-400" />
              Interactive Cytoscape.js Exploration
            </span>
            <span>Zoom, pan, search, or click any node to inspect centrality metadata</span>
          </div>

          <CytoscapeGraph
            nodes={nodes}
            edges={edges}
            onSelectNode={(node) => setSelectedNodeData(node)}
          />
        </div>
      )}

      {/* Node Inspector Card (if a node is clicked) */}
      {selectedNodeData && (
        <div className="rounded-xl border border-cyan-500/40 bg-slate-900/90 p-4 shadow-lg backdrop-blur-md">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-cyan-400" />
              <h3 className="text-sm font-bold text-slate-100">
                Selected Entity: <span className="text-cyan-300 font-mono">{selectedNodeData.label || selectedNodeData.id}</span>
              </h3>
            </div>
            <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
              {selectedNodeData.type || "Gene"}
            </span>
          </div>
          <div className="mt-2 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="rounded-lg bg-slate-950/60 p-2 border border-slate-800">
              <span className="text-[10px] text-slate-400">Degree Centrality</span>
              <div className="font-mono font-bold text-slate-200 mt-0.5">
                {selectedNodeData.degree !== undefined ? selectedNodeData.degree : (selectedNodeData.centrality ? selectedNodeData.centrality.toFixed(4) : "N/A")}
              </div>
            </div>
            <div className="rounded-lg bg-slate-950/60 p-2 border border-slate-800">
              <span className="text-[10px] text-slate-400">Betweenness</span>
              <div className="font-mono font-bold text-teal-400 mt-0.5">
                {selectedNodeData.betweenness !== undefined ? selectedNodeData.betweenness.toFixed(4) : "N/A"}
              </div>
            </div>
            <div className="rounded-lg bg-slate-950/60 p-2 border border-slate-800">
              <span className="text-[10px] text-slate-400">PageRank Score</span>
              <div className="font-mono font-bold text-purple-400 mt-0.5">
                {selectedNodeData.pagerank !== undefined ? selectedNodeData.pagerank.toFixed(4) : "N/A"}
              </div>
            </div>
            <div className="rounded-lg bg-slate-950/60 p-2 border border-slate-800">
              <span className="text-[10px] text-slate-400">Community Cluster</span>
              <div className="font-mono font-bold text-amber-400 mt-0.5">
                Cluster {selectedNodeData.community !== undefined ? selectedNodeData.community : 0}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top Aging Network Nodes Table (TASK 9) */}
      {networkData && (
        <div className="rounded-xl border border-slate-800 bg-[#0d131f]/90 shadow-md backdrop-blur-md overflow-hidden">
          <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3 bg-slate-900/50">
            <div className="flex items-center gap-2">
              <Award className="h-4 w-4 text-purple-400" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Top Aging Network Nodes Ranked by Centrality
              </h2>
            </div>
            <span className="text-[11px] text-slate-400">
              Key structural hubs & regulatory bottlenecks in the aging interactome
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/60 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  <th className="py-2.5 px-3">Rank</th>
                  <th className="py-2.5 px-3">Node Symbol</th>
                  <th className="py-2.5 px-3">Entity Type</th>
                  <th className="py-2.5 px-3">Degree</th>
                  <th className="py-2.5 px-3">Betweenness Centrality</th>
                  <th className="py-2.5 px-3">PageRank Score</th>
                  <th className="py-2.5 px-3">Community</th>
                  <th className="py-2.5 px-3">Aging Hallmark Role</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {(networkData.centrality_top_nodes || []).slice(0, 10).map((node, idx) => (
                  <tr key={node.node_id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-2.5 px-3 font-bold text-slate-500">#{idx + 1}</td>
                    <td className="py-2.5 px-3 font-bold text-slate-100 font-mono">
                      {node.node_id}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                        Gene / Protein
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-200">
                      {node.degree}
                    </td>
                    <td className="py-2.5 px-3 font-mono font-semibold text-teal-400">
                      {node.betweenness_centrality.toFixed(4)}
                    </td>
                    <td className="py-2.5 px-3 font-mono font-semibold text-purple-400">
                      {node.pagerank.toFixed(4)}
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 font-mono">
                      Community {node.community_id}
                    </td>
                    <td className="py-2.5 px-3 text-slate-300 text-[11px]">
                      {node.node_id === "CDKN2A"
                        ? "p16INK4a cellular senescence & cell cycle arrest"
                        : node.node_id === "TP53"
                        ? "DNA damage checkpoint & guardian of the genome"
                        : node.node_id === "SIRT1"
                        ? "NAD+ dependent histone deacetylation & longevity"
                        : node.node_id === "IL6"
                        ? "Systemic inflammaging & senescence-associated secretion"
                        : node.node_id === "MTOR"
                        ? "Nutrient sensing & anabolic metabolic regulation"
                        : "Molecular interactor in biological aging network"}
                    </td>
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
