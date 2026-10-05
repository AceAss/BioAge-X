"""Explainability module for BioAge-X."""
from bioage.explainability.shap_engine import (
    BioAgeShapExplainer,
    GENE_ANNOTATIONS,
)

__all__ = ["BioAgeShapExplainer", "GENE_ANNOTATIONS"]
