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
    """Calculates hypergeometric pathway over-representation with Benjamini-Hochberg FDR."""
    query_genes = request.query_genes or [
        "ELOVL2", "FHL2", "CDKN2A", "TP53", "SIRT1", "IL6", "TNF", "FOXO3",
        "MTOR", "TERT", "SOD2", "GDF15", "KLOTHO", "DNMT1", "ATM", "GSTP1"
    ]

    analyzer = PathwayEnrichmentAnalyzer()
    results = analyzer.analyze(query_genes, fdr_threshold=request.fdr_threshold)

    return PathwayEnrichmentResponse(
        pathways=results,
        query_gene_count=len(query_genes),
    )
