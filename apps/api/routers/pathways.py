"""
Pathways router for BioAge-X API.
Executes functional pathway over-representation analysis against hallmarks of aging.
"""

from fastapi import APIRouter
from apps.api.schemas.api_schemas import PathwayEnrichmentRequest, PathwayEnrichmentResponse
from bioage.pathways.enrichment import PathwayEnrichmentAnalyzer
from bioage.utils.logger import get_logger

logger = get_logger("apps.api.routers.pathways")
router = APIRouter(prefix="/pathways", tags=["Pathways"])


@router.post("/enrich", response_model=PathwayEnrichmentResponse)
def enrich_pathways(request: PathwayEnrichmentRequest):
    """Calculates pathway over-representation using Reactome, Hallmark knowledge base, or Combined."""
    query_genes = request.query_genes or [
        "ELOVL2", "FHL2", "CDKN2A", "TP53", "SIRT1", "IL6", "TNF", "FOXO3",
        "MTOR", "TERT", "SOD2", "GDF15", "KLOTHO", "DNMT1", "ATM", "GSTP1"
    ]

    from bioage.integrations.reactome_client import ReactomeClient

    client = ReactomeClient()
    enriched, status = client.enrich_pathways(
        genes=query_genes,
        species=request.species,
        fdr_threshold=request.fdr_threshold,
        pathway_source=request.pathway_source,
    )

    pathway_dicts = [p.to_dict() for p in enriched]
    source_label = (
        f"Reactome Analysis Service ({status.value if hasattr(status, 'value') else status})"
        if request.pathway_source == "reactome"
        else "Local Hallmarks of Aging Database"
        if request.pathway_source == "hallmarks"
        else "Combined (Reactome + Curated Hallmarks)"
    )

    return PathwayEnrichmentResponse(
        pathways=pathway_dicts,
        query_gene_count=len(query_genes),
        source_attribution=source_label,
    )
