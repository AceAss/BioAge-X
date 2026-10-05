"""
Random Forest Biological Age Predictor for BioAge-X.
Non-linear ensemble learning capturing complex epistasis and non-monotonic aging dynamics.
"""

import time
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from bioage.models.base import BaseBioAgeModel
from bioage.utils.logger import get_logger

logger = get_logger("bioage.models.random_forest")


class BioAgeRandomForest(BaseBioAgeModel):
    """Random Forest regressor for multi-omics age estimation."""

    def __init__(
        self,
        n_estimators: int = 150,
        max_depth: Optional[int] = 8,
        min_samples_split: int = 4,
        random_state: int = 42,
        params: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(name="RandomForest", params=params)
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.random_state = random_state
        self.model_: Optional[RandomForestRegressor] = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "BioAgeRandomForest":
        start_time = time.time()
        self.feature_names_ = list(X.columns)

        logger.info(f"Fitting RandomForest on {X.shape[0]} samples with {len(self.feature_names_)} features")
        self.model_ = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            random_state=self.random_state,
            n_jobs=-1,
        )
        self.model_.fit(X.values, y.values)
        self.training_time_sec_ = round(time.time() - start_time, 3)
        self.is_fitted_ = True

        logger.info(f"RandomForest fitted in {self.training_time_sec_}s")
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted_ or self.model_ is None:
            raise RuntimeError("RandomForest model is not fitted yet.")
        aligned_X = X[self.feature_names_]
        return self.model_.predict(aligned_X.values)

    def get_feature_importance(self) -> Dict[str, float]:
        if not self.is_fitted_ or self.model_ is None:
            return {}
        importances = self.model_.feature_importances_
        importance_dict = {
            feat: float(imp)
            for feat, imp in zip(self.feature_names_, importances)
        }
        return dict(sorted(importance_dict.items(), key=lambda item: item[1], reverse=True))
