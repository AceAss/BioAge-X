"""
The Cancer Genome Atlas (TCGA) Dedicated Provider for BioAge-X.
Accessions: TCGA-*.
Direct adapter connecting to TCGA cohorts hosted on NCI GDC.
"""

from bioage.acquisition.base import AccessType
from bioage.acquisition.providers.gdc import GDCProvider


class TCGAProvider(GDCProvider):
    """TCGA dedicated connector extending GDCProvider."""

    name = "TCGA"
    category = "Cancer Genomics / Clinical Cohorts"
    description = "The Cancer Genome Atlas multi-center clinical and multi-omics research cohort."
    access_type = AccessType.PUBLIC
    supported_accession_patterns = [r"^TCGA-[A-Z]+"]
