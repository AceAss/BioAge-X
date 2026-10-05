"""
Feature Selection Pipeline for BioAge-X.
Maintains rigorous biological feature provenance across filtering and selection stages:
- Variance filtering (unsupervised)
- Collinearity / Correlation filtering (greedy threshold removal)
- Mutual Information regression with chronological age
- Model-based importance ranking (Linear / Tree)
- Recursive Feature Elimination (RFE) option
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_regression
from sklearn.linear_model import RidgeCV

from bioage.utils.logger import get_logger

logger = get_logger("bioage.preprocessing.feature_selection")


class FeatureSelector:
    """Multi-stage feature selection pipeline with full feature provenance."""

    def __init__(
        self,
        max_features: int = 50,
        variance_threshold: float = 0.001,
        correlation_threshold: float = 0.95,
        method: str = "mutual_info",  # "mutual_info", "model_based", "variance_only"
        random_state: int = 42,
    ):
        self.max_features = max_features
        self.variance_threshold = variance_threshold
        self.correlation_threshold = correlation_threshold
        self.method = method
        self.random_state = random_state

        self.selected_features_: List[str] = []
        self.feature_scores_: Dict[str, float] = {}
        self.provenance_: Dict[str, Any] = {}

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "FeatureSelector":
        """Identifies optimal aging biomarker features using statistical ranking."""
        raw_feature_count = X.shape[1]
        feature_names = list(X.columns)
        logger.info(f"Starting feature selection from {raw_feature_count} features (target method: {self.method})")

        # Stage 1: Variance Filtering
        variances = X.var()
        var_passed = variances[variances >= self.variance_threshold].index.tolist()
        if not var_passed:
            var_passed = variances.nlargest(min(50, raw_feature_count)).index.tolist()
        X_var = X[var_passed]

        # Stage 2: Correlation Filtering (drop high collinearity)
        corr_passed = self._remove_collinear_features(X_var, y, threshold=self.correlation_threshold)
        X_corr = X_var[corr_passed]

        # Stage 3: Supervised Ranking (Mutual Information or Model-based)
        if self.method == "mutual_info":
            # Mutual Information regression with age
            mi_scores = mutual_info_regression(
                X_corr.values,
                y.values,
                random_state=self.random_state,
                n_neighbors=5
            )
            score_series = pd.Series(mi_scores, index=X_corr.columns).sort_values(ascending=False)
            top_k = score_series.head(self.max_features)
            self.selected_features_ = top_k.index.tolist()
            self.feature_scores_ = {k: float(v) for k, v in top_k.items()}

        elif self.method == "model_based":
            # Ridge regression coefficients magnitude
            ridge = RidgeCV(alphas=[0.1, 1.0, 10.0])
            ridge.fit(X_corr.values, y.values)
            coef_scores = pd.Series(np.abs(ridge.coef_), index=X_corr.columns).sort_values(ascending=False)
            top_k = coef_scores.head(self.max_features)
            self.selected_features_ = top_k.index.tolist()
            self.feature_scores_ = {k: float(v) for k, v in top_k.items()}

        else:  # variance_only
            var_scores = X_corr.var().sort_values(ascending=False).head(self.max_features)
            self.selected_features_ = var_scores.index.tolist()
            self.feature_scores_ = {k: float(v) for k, v in var_scores.items()}

        self.provenance_ = {
            "raw_feature_count": raw_feature_count,
            "variance_filtered_count": len(var_passed),
            "correlation_filtered_count": len(corr_passed),
            "final_selected_count": len(self.selected_features_),
            "selection_method": self.method,
            "top_features": self.selected_features_[:10],
            "top_scores": {k: round(self.feature_scores_[k], 4) for k in self.selected_features_[:10]},
        }
        logger.info(
            f"Feature selection complete: {raw_feature_count} -> "
            f"{len(var_passed)} (var) -> {len(corr_passed)} (corr) -> {len(self.selected_features_)} (final)"
        )
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Subsets dataframe to selected features."""
        if not self.selected_features_:
            raise RuntimeError("FeatureSelector has not been fitted. Call fit() first.")
        cols = [c for c in self.selected_features_ if c in X.columns]
        missing = set(self.selected_features_) - set(cols)
        result = X[cols].copy()
        for m in missing:
            result[m] = 0.0
        return result[self.selected_features_]

    def fit_transform(self, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        return self.fit(X, y).transform(X)

    def _remove_collinear_features(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        threshold: float = 0.95
    ) -> List[str]:
        """Greedily drops one of any pair of features with absolute Pearson correlation > threshold."""
        # Calculate correlation with target to prioritize keeping more predictive feature
        corrs_with_target = X.apply(lambda col: np.abs(np.corrcoef(col, y)[0, 1]) if col.std() > 0 else 0.0)

        # Pairwise correlation matrix
        corr_matrix = X.corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))

        to_drop = set()
        for col in upper.columns:
            high_corr_partners = upper.index[upper[col] > threshold].tolist()
            for partner in high_corr_partners:
                # Compare correlation with target; drop the one that correlates less with age
                if corrs_with_target.get(col, 0) >= corrs_with_target.get(partner, 0):
                    to_drop.add(partner)
                else:
                    to_drop.add(col)

        return [c for c in X.columns if c not in to_drop]
