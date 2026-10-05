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
        self.network_source_: str = "hybrid"
        self.knowledge_status_: str = "LOCAL_FALLBACK"
        self.source_breakdown_: Dict[str, int] = {}

    def build_from_biomarkers(
        self,
        biomarker_genes: List[str],
        edge_list_path: Optional[str | Path] = None,
        include_pathways: bool = True,
        max_hops: int = 1,
        network_source: str = "hybrid",
        min_confidence: float = 0.400,
        species: int = 9606,
        enable_live: bool = True,
    ) -> "BiologicalInteractionGraph":
        """
        Builds graph seeded with top biomarker genes. Connects to known interactions
        from STRING DB and/or local interactome, and incorporates pathway membership nodes.
        Supports network_source: 'hybrid', 'string', 'local'.
        """
        self.graph.clear()
        self.network_source_ = network_source
        self.source_breakdown_ = {"STRING": 0, "Local": 0, "Pathway": 0}

        clean_biomarkers = set(
            str(g).replace("GENE_", "").split("_")[-1].upper()
            for g in biomarker_genes
        )

        logger.info(
            f"Building biological interaction network for {len(clean_biomarkers)} biomarker seeds "
            f"(source={network_source}, min_conf={min_confidence})"
        )

        # Add seed Gene nodes
        for gene in clean_biomarkers:
            self._add_node(gene, node_type="Gene", is_biomarker=True)

        # Query PPI edges via STRINGClient or Local Fallback
        from bioage.integrations.string_client import STRINGClient

        string_client = STRINGClient(
            enable_live=enable_live,
            edge_file_path=Path(edge_list_path) if edge_list_path else None,
        )

        interaction_edges, status = string_client.get_interactions(
            genes=list(clean_biomarkers),
            min_score=min_confidence,
            species=species,
            network_source=network_source,
        )
        self.knowledge_status_ = status.value if hasattr(status, "value") else str(status)

        for edge in interaction_edges:
            src = edge.source.upper()
            tgt = edge.target.upper()
            prov = edge.provider

            if "STRING" in prov:
                self.source_breakdown_["STRING"] += 1
            else:
                self.source_breakdown_["Local"] += 1

            self._add_node(src, node_type=edge.source_type, is_biomarker=(src in clean_biomarkers))
            self._add_node(tgt, node_type=edge.target_type, is_biomarker=(tgt in clean_biomarkers))

            self.graph.add_edge(
                src,
                tgt,
                edge_type=edge.interaction_type,
                weight=edge.confidence_score,
                provider=prov,
                status=edge.status.value if hasattr(edge.status, "value") else str(edge.status),
                evidence_scores=edge.evidence_scores,
            )

        # Optional: Add Pathway nodes & pathway_membership edges
        if include_pathways:
            for pw_id, pw_data in PATHWAY_KNOWLEDGE_BASE.items():
                pw_name = pw_data["name"]
                pw_genes = set(g.upper() for g in pw_data["genes"])
                overlap = clean_biomarkers.intersection(pw_genes)

                if overlap:
                    self._add_node(pw_name, node_type="Pathway", category=pw_data.get("category", "Hallmark"))
                    for gene in overlap:
                        self.graph.add_edge(
                            gene,
                            pw_name,
                            edge_type="pathway_membership",
                            weight=0.80,
                            provider="Hallmark Pathway",
                            status="LOCAL_FALLBACK",
                            evidence_scores={"curated": 0.80},
                        )
                        self.source_breakdown_["Pathway"] += 1

        # Compute topological properties
        self.compute_centrality_metrics()
        logger.info(
            f"Network constructed: {self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges (Status: {self.knowledge_status_})"
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
                    "provider": data.get("provider", "Local Aging Interactome"),
                    "status": data.get("status", "LOCAL_FALLBACK"),
                    "evidence_scores": data.get("evidence_scores", {}),
                }
            })

        density = nx.density(self.graph) if self.graph.number_of_nodes() > 1 else 0.0

        return {
            "elements": elements,
            "summary": {
                "n_nodes": self.graph.number_of_nodes(),
                "n_edges": self.graph.number_of_edges(),
                "n_communities": len(self.communities_),
                "connected_components": nx.number_connected_components(self.graph),
                "density": round(float(density), 4),
                "network_source": getattr(self, "network_source_", "hybrid"),
                "knowledge_status": getattr(self, "knowledge_status_", "LOCAL_FALLBACK"),
                "source_breakdown": getattr(self, "source_breakdown_", {"STRING": 0, "Local": 0, "Pathway": 0}),
            }
        }

    def get_top_centrality_nodes(self, top_k: int = 10) -> List[Dict[str, Any]]:
        """Returns top aging network nodes ranked by betweenness and degree centrality."""
        if not hasattr(self, "topological_metrics_") or not self.topological_metrics_:
            self.compute_centrality_metrics()

        node_list = []
        for node, metrics in self.topological_metrics_.items():
            node_data = self.graph.nodes.get(node, {})
            node_list.append({
                "gene": str(node),
                "node_type": node_data.get("node_type", "Gene"),
                "is_biomarker": node_data.get("is_biomarker", False),
                "degree": metrics.get("degree", 0),
                "degree_centrality": metrics.get("degree_centrality", 0.0),
                "betweenness_centrality": metrics.get("betweenness_centrality", 0.0),
                "pagerank": metrics.get("pagerank", 0.0),
                "community_id": metrics.get("community_id", 0),
            })

        # Rank primarily by betweenness, then PageRank
        node_list.sort(key=lambda x: (x["betweenness_centrality"], x["pagerank"]), reverse=True)
        return node_list[:top_k]

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Returns topological and integration summary statistics."""
        cy_data = self.to_cytoscape_json()
        summary = cy_data["summary"]
        summary["num_nodes"] = summary["n_nodes"]
        summary["num_edges"] = summary["n_edges"]
        return summary

