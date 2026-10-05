"""
XGBoost Biological Age Predictor for BioAge-X.
Extreme Gradient Boosting for non-linear multi-omics aging prediction with regularized trees.
"""

import time
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

from bioage.models.base import BaseBioAgeModel
from bioage.utils.logger import get_logger

logger = get_logger("bioage.models.xgboost")


class BioAgeXGBoost(BaseBioAgeModel):
    """XGBoost regressor for biological age estimation with fallback to GradientBoostingRegressor."""

    def __init__(
        self,
        n_estimators: int = 150,
        learning_rate: float = 0.05,
        max_depth: int = 4,
        subsample: float = 0.85,
        colsample_bytree: float = 0.85,
        random_state: int = 42,
        params: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(name="XGBoost", params=params)
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.random_state = random_state
        self.model_: Any = None
        self.backend_: str = "xgboost"

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "BioAgeXGBoost":
        start_time = time.time()
        self.feature_names_ = list(X.columns)

        logger.info(f"Fitting XGBoost on {X.shape[0]} samples with {len(self.feature_names_)} features")

        try:
            import xgboost as xgb
            self.model_ = xgb.XGBRegressor(
                n_estimators=self.n_estimators,
                learning_rate=self.learning_rate,
                max_depth=self.max_depth,
                subsample=self.subsample,
                colsample_bytree=self.colsample_bytree,
                random_state=self.random_state,
                n_jobs=-1,
            )
            self.backend_ = "xgboost"
        except ImportError:
            logger.warning("xgboost not installed, falling back to scikit-learn GradientBoostingRegressor")
            from sklearn.ensemble import GradientBoostingRegressor
            self.model_ = GradientBoostingRegressor(
                n_estimators=self.n_estimators,
                learning_rate=self.learning_rate,
                max_depth=self.max_depth,
                subsample=self.subsample,
                random_state=self.random_state,
            )
            self.backend_ = "sklearn_gradient_boosting"

        self.model_.fit(X.values, y.values)
        self.training_time_sec_ = round(time.time() - start_time, 3)
        self.is_fitted_ = True

        logger.info(f"{self.name} ({self.backend_}) fitted in {self.training_time_sec_}s")
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted_ or self.model_ is None:
            raise RuntimeError("XGBoost model is not fitted yet.")
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
