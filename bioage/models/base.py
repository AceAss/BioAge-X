"""
Base Model Interface for BioAge-X.
Defines standardized contract for biological age predictors across regression algorithms.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from bioage.utils.logger import get_logger

logger = get_logger("bioage.models.base")


class BaseBioAgeModel(ABC):
    """Abstract base class for biological age estimation algorithms."""

    def __init__(self, name: str, params: Optional[Dict[str, Any]] = None):
        self.name = name
        self.params = params or {}
        self.feature_names_: List[str] = []
        self.is_fitted_: bool = False
        self.training_time_sec_: float = 0.0

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> "BaseBioAgeModel":
        """Fits biological age model on feature matrix X and chronological age y."""
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predicts biological age for input features X."""
        pass

    @abstractmethod
    def get_feature_importance(self) -> Dict[str, float]:
        """Returns sorted feature importance dictionary: {feature_name: score}."""
        pass

    def save(self, filepath: str | Path) -> None:
        """Serializes model artifact to disk."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        logger.info(f"Saved {self.name} model to {path}")

    @classmethod
    def load(cls, filepath: str | Path) -> "BaseBioAgeModel":
        """Loads serialized model artifact from disk."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")
        model = joblib.load(path)
        logger.info(f"Loaded {model.name} model from {path}")
        return model
