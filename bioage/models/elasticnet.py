"""
ElasticNet Biological Age Predictor for BioAge-X.
Standardized regularized linear regression (Horvath/Hannum epigenetic clock paradigm).
"""

import time
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import ElasticNetCV, ElasticNet

from bioage.models.base import BaseBioAgeModel
from bioage.utils.logger import get_logger

logger = get_logger("bioage.models.elasticnet")


class BioAgeElasticNet(BaseBioAgeModel):
    """ElasticNet regression with automatic l1_ratio and alpha cross-validation."""

    def __init__(
        self,
        l1_ratios: Optional[list] = None,
        cv: int = 5,
        max_iter: int = 2000,
        random_state: int = 42,
        params: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(name="ElasticNet", params=params)
        self.l1_ratios = l1_ratios or [0.1, 0.5, 0.7, 0.9, 0.95, 0.99]
        self.cv = cv
        self.max_iter = max_iter
        self.random_state = random_state
        self.model_: Optional[ElasticNetCV] = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "BioAgeElasticNet":
        start_time = time.time()
        self.feature_names_ = list(X.columns)

        logger.info(f"Fitting ElasticNet on {X.shape[0]} samples with {len(self.feature_names_)} features")
        
        cv_folds = min(self.cv, max(2, len(y) // 5))
        self.model_ = ElasticNetCV(
            l1_ratio=self.l1_ratios,
            cv=cv_folds,
            max_iter=self.max_iter,
            random_state=self.random_state,
            n_jobs=-1,
        )
        self.model_.fit(X.values, y.values)
        self.training_time_sec_ = round(time.time() - start_time, 3)
        self.is_fitted_ = True

        logger.info(
            f"ElasticNet fitted in {self.training_time_sec_}s: "
            f"best_alpha={self.model_.alpha_:.4f}, best_l1_ratio={self.model_.l1_ratio_:.2f}, "
            f"non-zero features={(self.model_.coef_ != 0).sum()}/{len(self.feature_names_)}"
        )
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted_ or self.model_ is None:
            raise RuntimeError("ElasticNet model is not fitted yet.")
        aligned_X = X[self.feature_names_]
        return self.model_.predict(aligned_X.values)

    def get_feature_importance(self) -> Dict[str, float]:
        if not self.is_fitted_ or self.model_ is None:
            return {}
        coefs = self.model_.coef_
        importance_dict = {
            feat: float(abs(coef))
            for feat, coef in zip(self.feature_names_, coefs)
        }
        # Sort descending
        return dict(sorted(importance_dict.items(), key=lambda item: item[1], reverse=True))
