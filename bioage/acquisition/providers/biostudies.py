"""
BioStudies Umbrella Provider for BioAge-X.
Accessions: S-BSST, S-EPMC.
EMBL-EBI integrated repository for multi-omics study packages and life science literature data.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from bioage.acquisition.base import AccessType
from bioage.acquisition.providers.arrayexpress import ArrayExpressProvider


class BioStudiesProvider(ArrayExpressProvider):
    """BioStudies umbrella adapter connecting to EBI BioStudies data packages."""

    name = "BioStudies"
    category = "Multi-Omics / Data Packages"
    description = "EMBL-EBI BioStudies repository organizing multi-layer biological and clinical data packages."
    access_type = AccessType.PUBLIC
    supported_accession_patterns = [r"^S-BSST\d+", r"^S-EPMC\d+"]
