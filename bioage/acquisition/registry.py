"""
Central Registries for BioAge-X Data Acquisition and Knowledge Integration.

Implements:
1. DatasetProviderRegistry - Central registry for all biological data repository connectors.
2. BiologicalKnowledgeProviderRegistry - Separate registry for biological annotation & pathway providers (STRING, Reactome, Ensembl).
"""

from typing import Dict, List, Optional, Any
from bioage.acquisition.base import DatasetProvider, AccessType
from bioage.acquisition.resolver import RepositoryResolver
from bioage.acquisition.providers import (
    GEOProvider,
    NCBIProvider,
    SRAProvider,
    ENAProvider,
    ArrayExpressProvider,
    BioStudiesProvider,
    GDCProvider,
    TCGAProvider,
    PRIDEProvider,
    ProteomeXchangeProvider,
    MetaboLightsProvider,
    GenericURLProvider,
)
from bioage.utils.logger import get_logger

logger = get_logger("bioage.acquisition.registry")


class DatasetProviderRegistry:
    """Registry managing external dataset acquisition providers."""

    _instance: Optional["DatasetProviderRegistry"] = None

    def __init__(self):
        self._providers: Dict[str, DatasetProvider] = {}
        self._init_defaults()

    def _init_defaults(self):
        """Registers default biological repository connectors."""
        self.register(GEOProvider())
        self.register(NCBIProvider())
        self.register(SRAProvider())
        self.register(ENAProvider())
        self.register(ArrayExpressProvider())
        self.register(BioStudiesProvider())
        self.register(GDCProvider())
        self.register(TCGAProvider())
        self.register(PRIDEProvider())
        self.register(ProteomeXchangeProvider())
        self.register(MetaboLightsProvider())
        self.register(GenericURLProvider())

    @classmethod
    def get_instance(cls) -> "DatasetProviderRegistry":
        if cls._instance is None:
            cls._instance = DatasetProviderRegistry()
        return cls._instance

    def register(self, provider: DatasetProvider) -> None:
        """Registers a new dataset acquisition connector."""
        self._providers[provider.name.lower()] = provider
        logger.info(f"Registered Dataset Provider: {provider.name} ({provider.category})")

    def get(self, name: str) -> Optional[DatasetProvider]:
        """Looks up a provider by name or alias."""
        norm_name = name.lower().strip()
        # Aliases
        if norm_name == "biostudies":
            norm_name = "biostudies"
        elif norm_name == "tcga":
            norm_name = "tcga"
        elif norm_name == "proteomexchange":
            norm_name = "proteomexchange"
        return self._providers.get(norm_name)

    def list_providers(self) -> List[DatasetProvider]:
        return list(self._providers.values())

    def resolve_for_input(self, accession_or_url: str) -> DatasetProvider:
        """Automatically routes an accession or URL to its matching registered provider."""
        provider_name, canonical_id = RepositoryResolver.resolve_provider_name(accession_or_url)
        provider = self.get(provider_name)
        if not provider:
            provider = self.get("generic url") or GenericURLProvider()
        return provider

    def get_capabilities_table(self) -> List[Dict[str, Any]]:
        """
        Returns structured matrix of supported repositories and operational capabilities.
        Used by the frontend to render the repository availability table.
        """
        records = []
        for p in self.list_providers():
            auto_ingest = (
                "yes" if p.access_type == AccessType.PUBLIC
                else ("conditional" if p.access_type == AccessType.CONDITIONAL else "restricted")
            )
            records.append({
                "repository": p.name,
                "category": p.category,
                "description": p.description,
                "search_supported": True if p.name != "Generic URL" else False,
                "download_supported": True,
                "auto_ingest": auto_ingest,
                "access_type": p.access_type.value,
                "supported_accessions": p.supported_accession_patterns,
            })
        return records


class BiologicalKnowledgeProviderRegistry:
    """Registry managing external biological knowledge and interaction providers (STRING, Reactome, Ensembl)."""

    _instance: Optional["BiologicalKnowledgeProviderRegistry"] = None

    def __init__(self):
        self._knowledge_providers: Dict[str, Any] = {}
        self._init_defaults()

    def _init_defaults(self):
        try:
            from bioage.integrations.string_client import STRINGClient
            from bioage.integrations.reactome_client import ReactomeClient
            from bioage.integrations.ensembl_client import EnsemblClient

            self.register("STRING", STRINGClient())
            self.register("Reactome", ReactomeClient())
            self.register("Ensembl", EnsemblClient())
        except Exception as e:
            logger.warning(f"Knowledge provider initialization notice: {e}")

    @classmethod
    def get_instance(cls) -> "BiologicalKnowledgeProviderRegistry":
        if cls._instance is None:
            cls._instance = BiologicalKnowledgeProviderRegistry()
        return cls._instance

    def register(self, name: str, client_instance: Any) -> None:
        self._knowledge_providers[name.upper()] = client_instance
        logger.info(f"Registered Biological Knowledge Provider: {name}")

    def get(self, name: str) -> Optional[Any]:
        return self._knowledge_providers.get(name.upper())

    def list_providers(self) -> List[str]:
        return list(self._knowledge_providers.keys())


def get_dataset_provider_registry() -> DatasetProviderRegistry:
    """Returns the singleton instance of DatasetProviderRegistry."""
    return DatasetProviderRegistry.get_instance()


def get_biological_knowledge_provider_registry() -> BiologicalKnowledgeProviderRegistry:
    """Returns the singleton instance of BiologicalKnowledgeProviderRegistry."""
    return BiologicalKnowledgeProviderRegistry.get_instance()


def register_dataset_provider(provider: DatasetProvider) -> None:
    """Convenience helper to register dataset providers."""
    DatasetProviderRegistry.get_instance().register(provider)


def register_knowledge_provider(name: str, client_instance: Any) -> None:
    """Convenience helper to register biological knowledge providers."""
    BiologicalKnowledgeProviderRegistry.get_instance().register(name, client_instance)
