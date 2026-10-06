"""
Universal Biological Data Acquisition Layer for BioAge-X.
"""

from bioage.acquisition.base import (
    DatasetProvider,
    DatasetSearchResult,
    DatasetMetadata,
    DownloadOption,
    DownloadOptionType,
    DownloadResult,
    ValidationResult,
    IngestionResult,
    AccessType,
    CompatibilityLevel,
)
from bioage.acquisition.registry import (
    DatasetProviderRegistry,
    BiologicalKnowledgeProviderRegistry,
    register_dataset_provider,
    register_knowledge_provider,
)
from bioage.acquisition.resolver import RepositoryResolver
from bioage.acquisition.downloader import DownloadManager
from bioage.acquisition.extractor import SafeArchiveExtractor
from bioage.acquisition.validator import DatasetValidator
from bioage.acquisition.normalizer import DatasetNormalizer
from bioage.acquisition.manifest import ManifestImporter
from bioage.acquisition.multi_omics import MultiOmicsAssembler
from bioage.acquisition.provenance import DatasetProvenanceRecord
from bioage.acquisition.cache import AcquisitionCache, CacheStatus
from bioage.acquisition.jobs import JobManager, JobRecord, JobStatus

__all__ = [
    "DatasetProvider",
    "DatasetSearchResult",
    "DatasetMetadata",
    "DownloadOption",
    "DownloadOptionType",
    "DownloadResult",
    "ValidationResult",
    "IngestionResult",
    "AccessType",
    "CompatibilityLevel",
    "DatasetProviderRegistry",
    "BiologicalKnowledgeProviderRegistry",
    "register_dataset_provider",
    "register_knowledge_provider",
    "RepositoryResolver",
    "DownloadManager",
    "SafeArchiveExtractor",
    "DatasetValidator",
    "DatasetNormalizer",
    "ManifestImporter",
    "MultiOmicsAssembler",
    "DatasetProvenanceRecord",
    "AcquisitionCache",
    "CacheStatus",
    "JobManager",
    "JobRecord",
    "JobStatus",
]
