"""
Biological Interaction Network Module for BioAge-X.
Constructs heterogeneous molecular graphs (Gene, Protein, Pathway, Biological Process)
with typed edges (interaction, pathway_membership, regulation, association).
Computes topological metrics: degree, betweenness centrality, PageRank, connected components,
and community clustering with full Cytoscape.js export support.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
import networkx as nx
import pandas as pd
from networkx.algorithms.community import greedy_modularity_communities

from bioage.pathways.database import PATHWAY_KNOWLEDGE_BASE
from bioage.utils.logger import get_logger

logger = get_logger("bioage.network.interaction_graph")


class BiologicalInteractionGraph:
    """Manages the creation, topological analysis, and export of molecular aging graphs."""

    def __init__(self):
        self.graph = nx.Graph()
        self.node_attributes_: Dict[str, Dict[str, Any]] = {}
        self.topological_metrics_: Dict[str, Dict[str, float]] = {}
        self.communities_: List[Set[str]] = []

    def build_from_biomarkers(
        self,
        biomarker_genes: List[str],
        edge_list_path: Optional[str | Path] = None,
        include_pathways: bool = True,
        max_hops: int = 1,
    ) -> "BiologicalInteractionGraph":
        """
        Builds graph seeded with top biomarker genes. Connects to known interactions
        from an edge list and incorporates pathway membership nodes.
        """
        self.graph.clear()
        clean_biomarkers = set(
            str(g).replace("GENE_", "").split("_")[-1].upper()
            for g in biomarker_genes
        )

        logger.info(f"Building biological interaction network for {len(clean_biomarkers)} biomarker seeds")

        # Load edge list
        df_edges = self._load_edge_list(edge_list_path)

        # Add seed Gene nodes
        for gene in clean_biomarkers:
            self._add_node(gene, node_type="Gene", is_biomarker=True)

        # Filter edges incident to seeds or between seeds
        for _, row in df_edges.iterrows():
            src = str(row["source"]).upper()
            tgt = str(row["target"]).upper()
            edge_type = str(row.get("edge_type", "interaction"))
            weight = float(row.get("weight", 1.0))

            if src in clean_biomarkers or tgt in clean_biomarkers:
                src_type = str(row.get("source_type", "Gene"))
                tgt_type = str(row.get("target_type", "Gene"))

                self._add_node(src, node_type=src_type, is_biomarker=(src in clean_biomarkers))
                self._add_node(tgt, node_type=tgt_type, is_biomarker=(tgt in clean_biomarkers))
                self.graph.add_edge(src, tgt, edge_type=edge_type, weight=weight)

        # Optional: Add Pathway nodes & pathway_membership edges
        if include_pathways:
            for pw_id, pw_data in PATHWAY_KNOWLEDGE_BASE.items():
                pw_name = pw_data["name"]
                pw_genes = set(g.upper() for g in pw_data["genes"])
                overlap = clean_biomarkers.intersection(pw_genes)

                if overlap:
                    self._add_node(pw_name, node_type="Pathway", category=pw_data.get("category", "Hallmark"))
                    for gene in overlap:
                        self.graph.add_edge(gene, pw_name, edge_type="pathway_membership", weight=0.8)

        # Compute topological properties
        self.compute_centrality_metrics()
        logger.info(
            f"Network constructed: {self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges"
        )
        return self

    def _add_node(self, node_id: str, **attrs) -> None:
        """Adds or updates a node with metadata."""
        if not self.graph.has_node(node_id):
            self.graph.add_node(node_id, **attrs)
        else:
            self.graph.nodes[node_id].update(attrs)

    def _load_edge_list(self, edge_list_path: Optional[str | Path]) -> pd.DataFrame:
        """Loads edge list file or returns canonical aging interaction default."""
        if edge_list_path and Path(edge_list_path).exists():
            return pd.read_csv(edge_list_path)
        
        # Built-in canonical aging interactions
        return pd.DataFrame([
            {"source": "TP53", "target": "CDKN1A", "edge_type": "regulation", "source_type": "Protein", "target_type": "Gene", "weight": 0.95},
            {"source": "CDKN2A", "target": "RB1", "edge_type": "regulation", "source_type": "Protein", "target_type": "Protein", "weight": 0.90},
            {"source": "SIRT1", "target": "TP53", "edge_type": "regulation", "source_type": "Protein", "target_type": "Protein", "weight": 0.85},
            {"source": "SIRT1", "target": "FOXO3", "edge_type": "interaction", "source_type": "Protein", "target_type": "Protein", "weight": 0.88},
            {"source": "MTOR", "target": "RPS6KB1", "edge_type": "regulation", "source_type": "Protein", "target_type": "Protein", "weight": 0.92},
            {"source": "AKT1", "target": "MTOR", "edge_type": "regulation", "source_type": "Protein", "target_type": "Protein", "weight": 0.94},
            {"source": "AKT1", "target": "FOXO3", "edge_type": "regulation", "source_type": "Protein", "target_type": "Protein", "weight": 0.89},
            {"source": "IL6", "target": "STAT3", "edge_type": "regulation", "source_type": "Protein", "target_type": "Protein", "weight": 0.91},
            {"source": "TNF", "target": "NFKB1", "edge_type": "regulation", "source_type": "Protein", "target_type": "Protein", "weight": 0.93},
            {"source": "NFKB1", "target": "IL6", "edge_type": "regulation", "source_type": "Protein", "target_type": "Gene", "weight": 0.87},
            {"source": "TERT", "target": "POT1", "edge_type": "interaction", "source_type": "Protein", "target_type": "Protein", "weight": 0.86},
            {"source": "ATM", "target": "TP53", "edge_type": "regulation", "source_type": "Protein", "target_type": "Protein", "weight": 0.94},
            {"source": "ELOVL2", "target": "FHL2", "edge_type": "association", "source_type": "Gene", "target_type": "Gene", "weight": 0.72},
            {"source": "FHL2", "target": "TP53", "edge_type": "interaction", "source_type": "Protein", "target_type": "Protein", "weight": 0.78},
            {"source": "SOD2", "target": "FOXO3", "edge_type": "regulation", "source_type": "Gene", "target_type": "Protein", "weight": 0.80},
            {"source": "GDF15", "target": "TP53", "edge_type": "regulation", "source_type": "Gene", "target_type": "Protein", "weight": 0.81},
            {"source": "KLOTHO", "target": "IGF1", "edge_type": "regulation", "source_type": "Protein", "target_type": "Protein", "weight": 0.84},
            {"source": "DNMT1", "target": "ELOVL2", "edge_type": "regulation", "source_type": "Protein", "target_type": "Gene", "weight": 0.79},
        ])

    def compute_centrality_metrics(self) -> Dict[str, Dict[str, float]]:
        """Calculates degree centrality, betweenness centrality, and PageRank."""
        if self.graph.number_of_nodes() == 0:
            return {}

        degree_dict = dict(self.graph.degree())
        deg_centrality = nx.degree_centrality(self.graph)
        betweenness = nx.betweenness_centrality(self.graph, weight="weight")
        
        try:
            pagerank = nx.pagerank(self.graph, weight="weight")
        except Exception:
            pagerank = {n: 1.0 / len(self.graph) for n in self.graph.nodes()}

        # Community detection
        try:
            self.communities_ = list(greedy_modularity_communities(self.graph))
        except Exception:
            self.communities_ = [set(self.graph.nodes())]

        comm_map = {}
        for c_idx, comm in enumerate(self.communities_):
            for n in comm:
                comm_map[n] = c_idx

        self.topological_metrics_ = {}
        for node in self.graph.nodes():
            metrics = {
                "degree": int(degree_dict.get(node, 0)),
                "degree_centrality": round(float(deg_centrality.get(node, 0.0)), 4),
                "betweenness_centrality": round(float(betweenness.get(node, 0.0)), 4),
                "pagerank": round(float(pagerank.get(node, 0.0)), 4),
                "community_id": int(comm_map.get(node, 0)),
            }
            self.topological_metrics_[node] = metrics
            self.graph.nodes[node].update(metrics)

        return self.topological_metrics_

    def to_cytoscape_json(self) -> Dict[str, Any]:
        """Exports graph elements in standard Cytoscape.js format."""
        elements = {"nodes": [], "edges": []}

        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get("node_type", "Gene")
            is_biomarker = data.get("is_biomarker", False)
            metrics = self.topological_metrics_.get(node_id, {})

            elements["nodes"].append({
                "data": {
                    "id": str(node_id),
                    "label": str(node_id),
                    "node_type": node_type,
                    "is_biomarker": bool(is_biomarker),
                    "degree": metrics.get("degree", 0),
                    "betweenness": metrics.get("betweenness_centrality", 0.0),
                    "pagerank": metrics.get("pagerank", 0.0),
                    "community_id": metrics.get("community_id", 0),
                    "category": data.get("category", ""),
                }
            })

        for src, tgt, data in self.graph.edges(data=True):
            elements["edges"].append({
                "data": {
                    "id": f"{src}_{tgt}",
                    "source": str(src),
                    "target": str(tgt),
                    "edge_type": data.get("edge_type", "interaction"),
                    "weight": round(float(data.get("weight", 1.0)), 2),
                }
            })

        return {
            "elements": elements,
            "summary": {
                "n_nodes": self.graph.number_of_nodes(),
                "n_edges": self.graph.number_of_edges(),
                "n_communities": len(self.communities_),
                "connected_components": nx.number_connected_components(self.graph),
            }
        }
