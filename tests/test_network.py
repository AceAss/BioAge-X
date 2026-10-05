"""Unit tests for Biological Interaction Graph and Centrality Analysis."""

import pytest
from bioage.network.interaction_graph import BiologicalInteractionGraph


def test_interaction_graph_build():
    biomarkers = ["TP53", "CDKN2A", "SIRT1", "IL6", "ELOVL2"]
    graph = BiologicalInteractionGraph()
    graph.build_from_biomarkers(biomarkers, edge_list_path=None, include_pathways=True)

    assert graph.graph.number_of_nodes() >= 5
    assert graph.graph.number_of_edges() >= 4

    metrics = graph.topological_metrics_
    assert "TP53" in metrics
    assert "betweenness_centrality" in metrics["TP53"]
    assert "pagerank" in metrics["TP53"]
    assert "community_id" in metrics["TP53"]

    cyto = graph.to_cytoscape_json()
    assert len(cyto["elements"]["nodes"]) == graph.graph.number_of_nodes()
    assert len(cyto["elements"]["edges"]) == graph.graph.number_of_edges()
