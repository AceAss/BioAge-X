"""Models module for BioAge-X."""
from bioage.models.base import BaseBioAgeModel
from bioage.models.elasticnet import BioAgeElasticNet
from bioage.models.random_forest import BioAgeRandomForest
from bioage.models.xgboost_model import BioAgeXGBoost
from bioage.models.fusion import (
    MultiOmicsEarlyFusion,
    MultiOmicsLateFusion,
    MultiOmicsWeightedEnsemble,
)

__all__ = [
    "BaseBioAgeModel",
    "BioAgeElasticNet",
    "BioAgeRandomForest",
    "BioAgeXGBoost",
    "MultiOmicsEarlyFusion",
    "MultiOmicsLateFusion",
    "MultiOmicsWeightedEnsemble",
]
