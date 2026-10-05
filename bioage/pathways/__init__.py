"""Pathways module for BioAge-X."""
from bioage.pathways.database import PATHWAY_KNOWLEDGE_BASE, ALL_PATHWAY_GENES
from bioage.pathways.enrichment import PathwayEnrichmentAnalyzer

__all__ = [
    "PATHWAY_KNOWLEDGE_BASE",
    "ALL_PATHWAY_GENES",
    "PathwayEnrichmentAnalyzer",
]
