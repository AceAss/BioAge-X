"""
Base interfaces and standard biological data schemas for BioAge-X integrations.
Defines provider contracts, knowledge statuses, and data transfer representations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone


class KnowledgeStatus(str, Enum):
    """Execution status and provenance state of a biological knowledge request."""
    LIVE = "LIVE"
    CACHED = "CACHED"
    LOCAL_FALLBACK = "LOCAL_FALLBACK"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_FOUND = "NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"
    ERROR = "ERROR"


@dataclass
class ProviderHealth:
    """Operational health status of an external biological knowledge provider."""
    provider: str
    status: str  # "available", "degraded", "unavailable"
    version: Optional[str] = None
    latency_ms: Optional[float] = None
    last_successful_request: Optional[str] = None
    cached_records: int = 0
    message: str = "Provider operational"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResolvedIdentifier:
    """Canonical biological identifier normalized across omics layers."""
    input_id: str
    identifier_type: str  # "symbol", "cpg", "ensembl", "uniprot", "covariate"
    canonical_symbol: Optional[str] = None
    ensembl_gene_id: Optional[str] = None
    species: str = "homo_sapiens"
    chromosome: Optional[str] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    description: Optional[str] = None
    biotype: Optional[str] = None
    status: KnowledgeStatus = KnowledgeStatus.LIVE
    ambiguity_candidates: List[str] = field(default_factory=list)
    source: str = "Ensembl"
    retrieved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, KnowledgeStatus) else str(self.status)
        return d


@dataclass
class InteractionEdge:
    """Protein-protein or gene-gene interaction with confidence and evidence breakdown."""
    source: str
    target: str
    source_type: str = "Gene"
    target_type: str = "Gene"
    interaction_type: str = "functional"  # functional, physical, regulatory, association
    confidence_score: float = 0.400
    evidence_scores: Dict[str, float] = field(default_factory=dict)
    provider: str = "STRING"
    provider_version: Optional[str] = None
    status: KnowledgeStatus = KnowledgeStatus.LIVE
    retrieved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, KnowledgeStatus) else str(self.status)
        return d


@dataclass
class EnrichedPathway:
    """Biological pathway over-representation record."""
    pathway_id: str
    pathway_name: str
    category: str = "Biological Process"
    matched_genes: List[str] = field(default_factory=list)
    pathway_size: int = 0
    overlap_count: int = 0
    p_value: float = 1.0
    fdr_adjusted_p: float = 1.0
    odds_ratio: float = 0.0
    source: str = "Reactome"
    provider_version: Optional[str] = None
    status: KnowledgeStatus = KnowledgeStatus.LIVE
    retrieved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, KnowledgeStatus) else str(self.status)
        d["p_value_fdr"] = self.fdr_adjusted_p
        return d

    @property
    def p_value_fdr(self) -> float:
        return self.fdr_adjusted_p


@dataclass
class GeoDatasetMetadata:
    """Public functional genomics dataset metadata from NCBI / GEO."""
    accession: str
    title: str
    summary: str = ""
    organism: str = "Homo sapiens"
    platform_id: Optional[str] = None
    tissue: Optional[str] = None
    study_type: str = "Methylation profiling"
    omics_type: str = "DNA Methylation"
    sample_count: int = 0
    has_age_metadata: bool = True
    age_range: Optional[str] = None
    compatibility_status: str = "Compatible"  # "Compatible", "Requires Preprocessing", "Not Compatible"
    approximate_size_mb: Optional[float] = None
    source: str = "NCBI GEO"
    external_url: str = ""
    retrieved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# ABSTRACT INTERFACES
# =============================================================================

class BiologicalKnowledgeProvider(ABC):
    """Abstract base provider for external biological knowledge integrations."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider service (e.g. 'STRING', 'Reactome')."""
        pass

    @abstractmethod
    def check_health(self) -> ProviderHealth:
        """Checks connectivity, latency, and service availability."""
        pass


class IdentifierResolver(ABC):
    """Abstract interface for gene and probe identifier normalization."""

    @abstractmethod
    def resolve(self, identifier: str) -> ResolvedIdentifier:
        """Resolves a single identifier to canonical symbol and Ensembl ID."""
        pass

    @abstractmethod
    def resolve_batch(self, identifiers: List[str]) -> List[ResolvedIdentifier]:
        """Resolves a list of identifiers in an efficient batch query."""
        pass


class InteractionProvider(ABC):
    """Abstract interface for retrieving protein/gene interaction networks."""

    @abstractmethod
    def get_interactions(
        self,
        genes: List[str],
        min_score: float = 0.400,
        species: int = 9606,
        network_source: str = "hybrid",
    ) -> Tuple[List[InteractionEdge], KnowledgeStatus]:
        """Retrieves interaction edges connecting seed genes."""
        pass


class PathwayProvider(ABC):
    """Abstract interface for pathway over-representation analysis."""

    @abstractmethod
    def enrich_pathways(
        self,
        genes: List[str],
        species: str = "homo_sapiens",
        fdr_threshold: float = 0.10,
    ) -> Tuple[List[EnrichedPathway], KnowledgeStatus]:
        """Computes statistical pathway enrichment for candidate genes."""
        pass


class DatasetProvider(ABC):
    """Abstract interface for discovering public omics cohorts."""

    @abstractmethod
    def search_datasets(self, query: str, max_results: int = 10) -> List[GeoDatasetMetadata]:
        """Searches public repositories for datasets matching query."""
        pass

    @abstractmethod
    def get_dataset_metadata(self, accession: str) -> Optional[GeoDatasetMetadata]:
        """Fetches detailed study metadata and pre-flight compatibility evaluation."""
        pass
