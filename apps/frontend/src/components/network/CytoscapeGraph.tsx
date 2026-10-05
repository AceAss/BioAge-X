"use client";

import React, { useEffect, useRef, useState } from "react";
import cytoscape, { Core } from "cytoscape";
import { CytoscapeNode, CytoscapeEdge } from "@/lib/types";
import { ZoomIn, ZoomOut, RotateCcw, Filter, Info, Search } from "lucide-react";

interface CytoscapeGraphProps {
  nodes: CytoscapeNode[];
  edges: CytoscapeEdge[];
  onSelectNode?: (nodeData: any) => void;
}

export function CytoscapeGraph({ nodes, edges, onSelectNode }: CytoscapeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [filterType, setFilterType] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState<string>("");

  useEffect(() => {
    if (!containerRef.current) return;

    // Filter elements
    const filteredNodes = nodes.filter((n) => {
      const matchesType = filterType === "all" || n.data.node_type === filterType;
      const matchesSearch = !searchTerm || n.data.label.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesType && matchesSearch;
    });

    const nodeIds = new Set(filteredNodes.map((n) => n.data.id));
    const filteredEdges = edges.filter((e) => nodeIds.has(e.data.source) && nodeIds.has(e.data.target));

    const cy = cytoscape({
      container: containerRef.current,
      elements: [...filteredNodes, ...filteredEdges],
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "color": "#f8fafc",
            "font-size": "11px",
            "font-family": "Inter, sans-serif",
            "text-valign": "center",
            "text-halign": "center",
            "background-color": "#0ea5e9",
            "border-width": 2,
            "border-color": "#38bdf8",
            width: "mapData(degree, 1, 10, 24, 48)",
            height: "mapData(degree, 1, 10, 24, 48)",
            "text-outline-color": "#090d16",
            "text-outline-width": 2,
            "transition-property": "background-color, border-color, width, height",
            "transition-duration": 0.2,
          },
        },
        {
          selector: 'node[node_type = "Protein"]',
          style: {
            "background-color": "#14b8a6",
            "border-color": "#2dd4bf",
          },
        },
        {
          selector: 'node[node_type = "Pathway"]',
          style: {
            "background-color": "#8b5cf6",
            "border-color": "#a78bfa",
            shape: "round-rectangle",
            width: 44,
            height: 30,
          },
        },
        {
          selector: "node:selected",
          style: {
            "border-color": "#f59e0b",
            "border-width": 4,
            "background-color": "#f59e0b",
          },
        },
        {
          selector: "edge",
          style: {
            width: "mapData(weight, 0.5, 1.0, 1.5, 3.5)",
            "line-color": "#334155",
            "curve-style": "bezier",
            opacity: 0.7,
          },
        },
        {
          selector: 'edge[edge_type = "regulation"]',
          style: {
            "line-color": "#0284c7",
            "target-arrow-shape": "triangle",
            "target-arrow-color": "#0284c7",
          },
        },
        {
          selector: 'edge[edge_type = "pathway_membership"]',
          style: {
            "line-color": "#7c3aed",
            "line-style": "dashed",
          },
        },
      ],
      layout: {
        name: "cose",
        animate: false,
        randomize: false,
        componentSpacing: 60,
        nodeOverlap: 20,
      },
    });

    cy.on("tap", "node", (evt) => {
      const node = evt.target;
      const data = node.data();
      setSelectedNode(data);
      if (onSelectNode) onSelectNode(data);
    });

    cy.on("tap", (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [nodes, edges, filterType, searchTerm]);

  return (
    <div className="relative w-full h-[540px] rounded-xl border border-slate-800 bg-slate-950/80 overflow-hidden">
      {/* Top Toolbar */}
      <div className="absolute top-3 left-3 z-10 flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/90 p-1.5 backdrop-blur-md">
        <div className="relative flex items-center">
          <Search className="absolute left-2.5 h-3.5 w-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search gene..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="h-7 w-32 rounded-md bg-slate-950 pl-8 pr-2 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
          />
        </div>

        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="h-7 rounded-md bg-slate-950 px-2 text-xs text-slate-300 border border-slate-800 focus:outline-none"
        >
          <option value="all">All Types</option>
          <option value="Gene">Genes</option>
          <option value="Protein">Proteins</option>
          <option value="Pathway">Pathways</option>
        </select>
      </div>

      {/* Zoom / View controls */}
      <div className="absolute top-3 right-3 z-10 flex flex-col gap-1 rounded-lg border border-slate-800 bg-slate-900/90 p-1 backdrop-blur-md">
        <button
          onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 1.2)}
          className="p-1.5 text-slate-400 hover:text-cyan-400 transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="h-4 w-4" />
        </button>
        <button
          onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 0.8)}
          className="p-1.5 text-slate-400 hover:text-cyan-400 transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="h-4 w-4" />
        </button>
        <button
          onClick={() => cyRef.current?.fit()}
          className="p-1.5 text-slate-400 hover:text-cyan-400 transition-colors"
          title="Reset View"
        >
          <RotateCcw className="h-4 w-4" />
        </button>
      </div>

      {/* Graph canvas */}
      <div ref={containerRef} className="w-full h-full" />

      {/* Selected Node Details Drawer */}
      {selectedNode && (
        <div className="absolute bottom-3 left-3 z-10 w-72 rounded-xl border border-cyan-500/30 bg-slate-900/95 p-3.5 backdrop-blur-md shadow-glow">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="font-bold text-white text-sm flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-cyan-400" />
              {selectedNode.label}
            </span>
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
              {selectedNode.node_type}
            </span>
          </div>
          <div className="mt-2.5 grid grid-cols-2 gap-2 text-[11px]">
            <div>
              <span className="text-slate-500">Degree:</span>{" "}
              <span className="font-mono text-slate-200">{selectedNode.degree ?? "N/A"}</span>
            </div>
            <div>
              <span className="text-slate-500">PageRank:</span>{" "}
              <span className="font-mono text-slate-200">{selectedNode.pagerank?.toFixed(3) ?? "N/A"}</span>
            </div>
            <div>
              <span className="text-slate-500">Betweenness:</span>{" "}
              <span className="font-mono text-slate-200">{selectedNode.betweenness?.toFixed(3) ?? "N/A"}</span>
            </div>
            <div>
              <span className="text-slate-500">Cluster:</span>{" "}
              <span className="font-mono text-slate-200">#{selectedNode.community_id ?? "0"}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
