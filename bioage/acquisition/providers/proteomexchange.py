"""
ProteomeXchange Consortium Provider for BioAge-X.
Accessions: PXD, PRD.
Consortium umbrella connecting PRIDE, PeptideAtlas, jPOST, MassIVE, and iProX.
"""

from bioage.acquisition.base import AccessType
from bioage.acquisition.providers.pride import PRIDEProvider


class ProteomeXchangeProvider(PRIDEProvider):
    """ProteomeXchange consortium umbrella connector extending PRIDEProvider."""

    name = "ProteomeXchange"
    category = "Proteomics / Mass Spectrometry"
    description = "International ProteomeXchange consortium coordinating global public proteomics repositories."
    access_type = AccessType.CONDITIONAL
    supported_accession_patterns = [r"^PXD\d+", r"^PRD\d+"]
