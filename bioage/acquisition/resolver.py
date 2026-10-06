"""
Repository and Accession Resolver for BioAge-X.
Automatically routes accessions, identifiers, and URLs to their optimal repository provider.
"""

import re
from typing import Optional, Tuple, Dict, Any

from bioage.utils.logger import get_logger

logger = get_logger("bioage.acquisition.resolver")


class RepositoryResolver:
    """Dispatches accession strings and public URLs to matching biological database providers."""

    ROUTING_PATTERNS = [
        # GEO
        (r"^(GSE\d+|GDS\d+|GSM\d+)", "GEO"),
        # NCBI BioProject / BioSample
        (r"^(PRJNA\d+|SAMN\d+)", "NCBI"),
        # SRA
        (r"^(SRP\d+|SRX\d+|SRR\d+)", "SRA"),
        # ENA
        (r"^(PRJEB\d+|ERP\d+|ERX\d+|ERR\d+)", "ENA"),
        # ArrayExpress
        (r"^(E-MTAB-\d+|E-GEOD-\d+|E-MEXP-\d+)", "ArrayExpress"),
        # BioStudies
        (r"^(S-BSST\d+|S-EPMC\d+)", "BioStudies"),
        # TCGA
        (r"^TCGA-[A-Z0-9]+", "TCGA"),
        # GDC
        (r"^(GDC-[A-Z0-9]+|[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})", "GDC"),
        # PRIDE / ProteomeXchange
        (r"^(PXD\d+|PRD\d+)", "PRIDE"),
        # MetaboLights
        (r"^MTBLS\d+", "MetaboLights"),
    ]

    @classmethod
    def resolve_provider_name(cls, query_or_url: str) -> Tuple[str, str]:
        """
        Determines the appropriate provider and canonical accession.
        Returns: (provider_name, canonical_accession)
        """
        raw = query_or_url.strip()

        # 1. Direct URLs
        if raw.startswith("http://") or raw.startswith("https://") or raw.startswith("ftp://"):
            raw_upper = raw.upper()
            if "NCBI.NLM.NIH.GOV/GEO" in raw_upper:
                m = re.search(r"(GSE\d+)", raw, re.I)
                if m:
                    return "GEO", m.group(1).upper()
            elif "PORTAL.GDC.CANCER.GOV/PROJECTS" in raw_upper:
                m = re.search(r"(TCGA-[A-Z0-9]+)", raw, re.I)
                if m:
                    return "GDC", m.group(1).upper()
            elif "EBI.AC.UK/PRIDE" in raw_upper:
                m = re.search(r"(PXD\d+)", raw, re.I)
                if m:
                    return "PRIDE", m.group(1).upper()
            elif "EBI.AC.UK/METABOLIGHTS" in raw_upper:
                m = re.search(r"(MTBLS\d+)", raw, re.I)
                if m:
                    return "MetaboLights", m.group(1).upper()
            elif "EBI.AC.UK/BIOSTUDIES" in raw_upper:
                m = re.search(r"(E-MTAB-\d+|S-BSST\d+)", raw, re.I)
                if m:
                    return "ArrayExpress", m.group(1).upper()

            # Generic URL
            return "Generic URL", raw

        # 2. Pattern matching against accessions
        clean_upper = raw.upper()
        for pattern, provider in cls.ROUTING_PATTERNS:
            if re.match(pattern, clean_upper, re.I):
                return provider, clean_upper

        # Default fallback to Generic URL or closest
        return "Generic URL", raw

    @classmethod
    def resolve_accession(cls, accession: str):
        """Resolves accession and returns the matching DatasetProvider instance."""
        provider_name, _ = cls.resolve_provider_name(accession)
        from bioage.acquisition.registry import DatasetProviderRegistry
        return DatasetProviderRegistry.get_instance().get(provider_name)

    @classmethod
    def resolve_url(cls, url: str):
        """Resolves URL and returns the matching DatasetProvider instance."""
        provider_name, _ = cls.resolve_provider_name(url)
        from bioage.acquisition.registry import DatasetProviderRegistry
        return DatasetProviderRegistry.get_instance().get(provider_name)

