"""
Biological Data Acquisition Providers for BioAge-X.
Exposes repository-specific connector adapters and the generic web connector.
"""

from bioage.acquisition.providers.geo import GEOProvider
from bioage.acquisition.providers.ncbi import NCBIProvider
from bioage.acquisition.providers.sra import SRAProvider
from bioage.acquisition.providers.ena import ENAProvider
from bioage.acquisition.providers.arrayexpress import ArrayExpressProvider
from bioage.acquisition.providers.biostudies import BioStudiesProvider
from bioage.acquisition.providers.gdc import GDCProvider
from bioage.acquisition.providers.tcga import TCGAProvider
from bioage.acquisition.providers.pride import PRIDEProvider
from bioage.acquisition.providers.proteomexchange import ProteomeXchangeProvider
from bioage.acquisition.providers.metabolights import MetaboLightsProvider
from bioage.acquisition.providers.generic import GenericURLProvider

__all__ = [
    "GEOProvider",
    "NCBIProvider",
    "SRAProvider",
    "ENAProvider",
    "ArrayExpressProvider",
    "BioStudiesProvider",
    "GDCProvider",
    "TCGAProvider",
    "PRIDEProvider",
    "ProteomeXchangeProvider",
    "MetaboLightsProvider",
    "GenericURLProvider",
]
