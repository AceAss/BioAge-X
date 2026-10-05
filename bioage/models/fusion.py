"""
Multi-Omics Fusion Architecture for BioAge-X.
Implements:
1. Early Fusion (Feature Concatenation)
2. Late Fusion (Stacking Meta-Regressor)
3. Weighted Ensemble (Robust to Missing Modalities)
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from bioage.models.base import BaseBioAgeModel
from bioage.models.elasticnet import BioAgeElasticNet
from bioage.models.random_forest import BioAgeRandomForest
from bioage.utils.logger import get_logger

logger = get_logger("bioage.models.fusion")


class MultiOmicsEarlyFusion(BaseBioAgeModel):
    """Early Fusion: concatenates features from all available modalities into a single matrix."""

    def __init__(
        self,
        base_model_cls: Any = BioAgeElasticNet,
        model_kwargs: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(name="MultiOmics_EarlyFusion")
        self.base_model_cls = base_model_cls
        self.model_kwargs = model_kwargs or {}
        self.inner_model_: Optional[BaseBioAgeModel] = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "MultiOmicsEarlyFusion":
        self.feature_names_ = list(X.columns)
        self.inner_model_ = self.base_model_cls(**self.model_kwargs)
        self.inner_model_.fit(X, y)
        self.training_time_sec_ = self.inner_model_.training_time_sec_
        self.is_fitted_ = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted_ or self.inner_model_ is None:
            raise RuntimeError("Early fusion model is not fitted.")
        return self.inner_model_.predict(X)

    def get_feature_importance(self) -> Dict[str, float]:
        if self.inner_model_ is None:
            return {}
        return self.inner_model_.get_feature_importance()


class MultiOmicsLateFusion(BaseBioAgeModel):
    """
    Late Fusion: trains distinct modality-specific sub-models,
    then trains a meta-regressor on sub-model biological age predictions.
    Handles missing modalities by imputing modality predictions with cohort mean.
    """

    def __init__(
        self,
        sub_model_map: Optional[Dict[str, BaseBioAgeModel]] = None,
    ):
        super().__init__(name="MultiOmics_LateFusion")
        self.sub_model_map = sub_model_map or {}
        self.meta_regressor_: Optional[Ridge] = None
        self.modalities_: List[str] = []
        self.modality_means_: Dict[str, float] = {}

    def fit_modalities(
        self,
        modality_data: Dict[str, pd.DataFrame],
        y: pd.Series,
    ) -> "MultiOmicsLateFusion":
        """
        modality_data: e.g. {"methylation": df_meth, "transcriptomics": df_trans}
        """
        logger.info(f"Fitting Late Fusion across modalities: {list(modality_data.keys())}")
        self.modalities_ = list(modality_data.keys())

        # Fit each sub-model
        sub_preds = {}
        for mod, df_mod in modality_data.items():
            if mod not in self.sub_model_map:
                # Default to ElasticNet
                self.sub_model_map[mod] = BioAgeElasticNet()
            
            self.sub_model_map[mod].fit(df_mod, y)
            preds = self.sub_model_map[mod].predict(df_mod)
            sub_preds[mod] = preds
            self.modality_means_[mod] = float(np.mean(preds))

        # Train meta-regressor on combined predictions
        meta_X = pd.DataFrame(sub_preds, index=y.index)
        self.meta_regressor_ = Ridge(alpha=1.0)
        self.meta_regressor_.fit(meta_X.values, y.values)
        self.is_fitted_ = True
        return self

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "MultiOmicsLateFusion":
        # If single dataframe is passed, partition columns by modality prefix
        meth_cols = [c for c in X.columns if c.startswith("cg")]
        trans_cols = [c for c in X.columns if not c.startswith("cg") and c not in {"sample_id", "chronological_age"}]

        modality_data = {}
        if meth_cols:
            modality_data["methylation"] = X[meth_cols]
        if trans_cols:
            modality_data["transcriptomics"] = X[trans_cols]

        if not modality_data:
            modality_data["all_features"] = X

        return self.fit_modalities(modality_data, y)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted_ or self.meta_regressor_ is None:
            raise RuntimeError("Late fusion model is not fitted.")

        meth_cols = [c for c in X.columns if c.startswith("cg")]
        trans_cols = [c for c in X.columns if not c.startswith("cg") and c not in {"sample_id", "chronological_age"}]

        meta_features = []
        for mod in self.modalities_:
            if mod == "methylation" and meth_cols and mod in self.sub_model_map:
                p = self.sub_model_map[mod].predict(X[meth_cols])
            elif mod == "transcriptomics" and trans_cols and mod in self.sub_model_map:
                p = self.sub_model_map[mod].predict(X[trans_cols])
            else:
                # Modality missing for these samples - impute with training mean
                p = np.full(X.shape[0], self.modality_means_.get(mod, 50.0))
            meta_features.append(p)

        meta_X = np.column_stack(meta_features)
        return self.meta_regressor_.predict(meta_X)

    def get_feature_importance(self) -> Dict[str, float]:
        """Combines feature importances across modality sub-models."""
        combined = {}
        for mod, model in self.sub_model_map.items():
            importances = model.get_feature_importance()
            for feat, score in importances.items():
                combined[f"{mod}:{feat}"] = score
        return dict(sorted(combined.items(), key=lambda item: item[1], reverse=True))


class MultiOmicsWeightedEnsemble(BaseBioAgeModel):
    """Weighted ensemble combining modality predictions, robust to missing modalities."""

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
    ):
        super().__init__(name="MultiOmics_WeightedEnsemble")
        # Default weights: 60% methylation (epigenetic clock), 40% transcriptomics
        self.weights = weights or {"methylation": 0.60, "transcriptomics": 0.40}
        self.sub_models_: Dict[str, BaseBioAgeModel] = {}

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "MultiOmicsWeightedEnsemble":
        meth_cols = [c for c in X.columns if c.startswith("cg")]
        trans_cols = [c for c in X.columns if not c.startswith("cg") and c not in {"sample_id", "chronological_age"}]

        if meth_cols:
            m_model = BioAgeElasticNet()
            m_model.fit(X[meth_cols], y)
            self.sub_models_["methylation"] = m_model

        if trans_cols:
            t_model = BioAgeRandomForest()
            t_model.fit(X[trans_cols], y)
            self.sub_models_["transcriptomics"] = t_model

        self.is_fitted_ = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted_:
            raise RuntimeError("Ensemble is not fitted.")

        meth_cols = [c for c in X.columns if c.startswith("cg")]
        trans_cols = [c for c in X.columns if not c.startswith("cg") and c not in {"sample_id", "chronological_age"}]

        predictions = {}
        active_weights = {}

        if "methylation" in self.sub_models_ and meth_cols:
            predictions["methylation"] = self.sub_models_["methylation"].predict(X[meth_cols])
            active_weights["methylation"] = self.weights.get("methylation", 0.5)

        if "transcriptomics" in self.sub_models_ and trans_cols:
            predictions["transcriptomics"] = self.sub_models_["transcriptomics"].predict(X[trans_cols])
            active_weights["transcriptomics"] = self.weights.get("transcriptomics", 0.5)

        if not predictions:
            raise ValueError("No recognizable modality columns in input DataFrame.")

        # Normalize weights if one modality is missing
        total_weight = sum(active_weights.values())
        norm_weights = {k: v / total_weight for k, v in active_weights.items()}

        final_pred = np.zeros(X.shape[0])
        for mod, preds in predictions.items():
            final_pred += norm_weights[mod] * preds

        return final_pred

    def get_feature_importance(self) -> Dict[str, float]:
        combined = {}
        for mod, model in self.sub_models_.items():
            weight = self.weights.get(mod, 0.5)
            for feat, score in model.get_feature_importance().items():
                combined[f"{mod}:{feat}"] = score * weight
        return dict(sorted(combined.items(), key=lambda item: item[1], reverse=True))
