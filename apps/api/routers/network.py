"""
Biological Network router for BioAge-X API.
Constructs molecular interaction graphs, computes topological centralities,
and exports Cytoscape.js compatible graph topologies.
"""

from pathlib import Path
from fastapi import APIRouter
from apps.api.core.config import settings
from apps.api.schemas.api_schemas import NetworkBuildRequest, NetworkResponseSchema
from bioage.network.interaction_graph import BiologicalInteractionGraph
from bioage.utils.logger import get_logger

logger = get_logger("apps.api.routers.network")
router = APIRouter(prefix="/network", tags=["Network Biology"])


@router.post("/build", response_model=NetworkResponseSchema)
def build_network(request: NetworkBuildRequest):
    """Builds biological interaction network seeded by candidate biomarker genes."""
    biomarkers = request.biomarkers or [
        "ELOVL2", "FHL2", "CDKN2A", "TP53", "SIRT1", "IL6", "TNF", "FOXO3",
        "MTOR", "TERT", "SOD2", "GDF15", "KLOTHO", "AKT1", "ATM", "GSTP1"
    ]

    edge_file = settings.EXAMPLE_DIR / "aging_network_edges.csv"
    edge_path = edge_file if edge_file.exists() else None

    graph_builder = BiologicalInteractionGraph()
    graph_builder.build_from_biomarkers(
        biomarker_genes=biomarkers,
        edge_list_path=edge_path,
        include_pathways=request.include_pathways,
    )

    cyto_data = graph_builder.to_cytoscape_json()

    # Extract top centrality nodes
    top_centrality = []
    for node, metrics in graph_builder.topological_metrics_.items():
        top_centrality.append({
            "node_id": node,
            "degree": metrics["degree"],
            "degree_centrality": metrics["degree_centrality"],
            "betweenness_centrality": metrics["betweenness_centrality"],
            "pagerank": metrics["pagerank"],
            "community_id": metrics["community_id"],
        })
    top_centrality = sorted(top_centrality, key=lambda x: x["betweenness_centrality"], reverse=True)

    return NetworkResponseSchema(
        elements=cyto_data["elements"],
        summary=cyto_data["summary"],
        centrality_top_nodes=top_centrality,
    )
