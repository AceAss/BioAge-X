"""
External Biological Knowledge Integration Layer for BioAge-X.
Provides modular, decoupled adapters for STRING, Reactome, Ensembl, and NCBI/GEO
with persistent caching, provenance tracking, and deterministic local fallbacks.
"""

from bioage.integrations.base import (
    KnowledgeStatus,
    ProviderHealth,
    ResolvedIdentifier,
    InteractionEdge,
    EnrichedPathway,
    GeoDatasetMetadata,
    BiologicalKnowledgeProvider,
    IdentifierResolver,
    InteractionProvider,
    PathwayProvider,
    DatasetProvider,
)
from bioage.integrations.cache import PersistentBiologicalCache, get_integration_cache, get_biological_cache
from bioage.integrations.rate_limit import RateLimiter, retry_with_backoff
from bioage.integrations.provenance import BiologicalProvenanceTracker, get_provenance_tracker
from bioage.integrations.ensembl_client import EnsemblClient
from bioage.integrations.string_client import STRINGClient
from bioage.integrations.reactome_client import ReactomeClient
from bioage.integrations.ncbi_client import NCBIClient
from bioage.integrations.geo_client import GEOClient
from bioage.integrations.resolver import UnifiedIdentifierResolver

__all__ = [
    "KnowledgeStatus",
    "ProviderHealth",
    "ResolvedIdentifier",
    "InteractionEdge",
    "EnrichedPathway",
    "GeoDatasetMetadata",
    "BiologicalKnowledgeProvider",
    "IdentifierResolver",
    "InteractionProvider",
    "PathwayProvider",
    "DatasetProvider",
    "PersistentBiologicalCache",
    "get_integration_cache",
    "RateLimiter",
    "retry_with_backoff",
    "BiologicalProvenanceTracker",
    "get_provenance_tracker",
    "EnsemblClient",
    "STRINGClient",
    "ReactomeClient",
    "NCBIClient",
    "GEOClient",
    "UnifiedIdentifierResolver",
]
