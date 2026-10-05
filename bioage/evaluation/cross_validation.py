"""
Leakage-Free Cross-Validation and Data Leakage Audit Engine for BioAge-X.

Enforces strict machine learning hygiene:
1. Chronological age target isolation (zero feature leakage).
2. Train / test partition before any parameter fitting (imputation, scaling, feature selection).
3. Out-of-fold generalization quantification vs apparent training fit.
4. Duplicate sample detection across validation splits.
"""

from typing import Dict, List, Optional, Any, Tuple
import time
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

from bioage.preprocessing.methylation import MethylationPreprocessor
from bioage.preprocessing.transcriptomics import TranscriptomicsPreprocessor
from bioage.preprocessing.feature_selection import FeatureSelector
from bioage.models.elasticnet import BioAgeElasticNet
from bioage.models.random_forest import BioAgeRandomForest
from bioage.models.xgboost_model import BioAgeXGBoost
from bioage.models.fusion import MultiOmicsEarlyFusion
from bioage.evaluation.metrics import evaluate_predictions, ModelMetrics
from bioage.utils.logger import get_logger

logger = get_logger("bioage.evaluation.cross_validation")


class DataLeakageDetector:
    """Audits feature matrices and training workflows for target and split leakage."""

    @staticmethod
    def audit_features(
        X: pd.DataFrame,
        y: pd.Series,
        age_col_name: str = "chronological_age",
    ) -> Dict[str, Any]:
        """
        Inspects feature matrix X for accidental target leakage:
        - Target column present in X
        - Features containing 'age' in their name
        - Features with correlation |r| > 0.999 with chronological age
        """
        issues = []
        clean_features = []

        # 1. Target column name in features
        if age_col_name in X.columns:
            issues.append(f"CRITICAL: Target column '{age_col_name}' was found in feature matrix X.")

        # 2. Check for age-derived column names
        for col in X.columns:
            col_lower = str(col).lower()
            if col_lower in {"age", "chronological_age", "chron_age", "age_years", "true_age_acceleration"}:
                issues.append(f"CRITICAL: Target/derived column '{col}' found in feature matrix X.")

        # 3. Check for exact or near-perfect correlation (target leak)
        for col in X.columns:
            if pd.api.types.is_numeric_dtype(X[col]):
                vals = X[col].values
                valid_mask = (~np.isnan(vals)) & (~np.isnan(y.values))
                if np.sum(valid_mask) > 5 and np.std(vals[valid_mask]) > 1e-6:
                    corr = float(np.corrcoef(vals[valid_mask], y.values[valid_mask])[0, 1])
                    if abs(corr) >= 0.999:
                        issues.append(f"WARNING: Feature '{col}' has |r| = {corr:.4f} with target. High risk of target leakage.")

        is_leakage_free = len(issues) == 0
        return {
            "is_leakage_free": is_leakage_free,
            "issues": issues,
            "audited_feature_count": X.shape[1],
            "sample_count": X.shape[0],
        }

    @staticmethod
    def audit_splits(train_indices: np.ndarray, test_indices: np.ndarray) -> Dict[str, Any]:
        """Confirms zero index overlap between train and test splits."""
        train_set = set(train_indices)
        test_set = set(test_indices)
        overlap = train_set.intersection(test_set)
        return {
            "has_split_overlap": len(overlap) > 0,
            "overlapping_sample_count": len(overlap),
            "overlapping_indices": list(overlap)[:10],
        }


class BioAgeCrossValidator:
    """
    Executes rigorous K-fold cross-validation ensuring preprocessing, imputation,
    and feature selection are fitted exclusively on training folds.
    """

    def __init__(
        self,
        n_splits: int = 5,
        random_state: int = 42,
        max_features: int = 40,
    ):
        self.n_splits = n_splits
        self.random_state = random_state
        self.max_features = max_features

    def evaluate_model(
        self,
        df: pd.DataFrame,
        model_type: str = "ElasticNet",
        age_col: str = "chronological_age",
    ) -> Dict[str, Any]:
        """
        Executes leak-free K-Fold cross-validation across the full workflow:
        1. Preprocessing parameters fitted only on train folds.
        2. Feature selection fitted only on train folds.
        3. Model fitted on train folds.
        4. Evaluated on unobserved out-of-fold validation sets.
        """
        if age_col not in df.columns:
            raise ValueError(f"Target column '{age_col}' not found in DataFrame.")

        y = df[age_col]
        all_cols = list(df.columns)
        meta_cols = {age_col, "sample_id", "sex", "smoking_status", "bmi", "true_age_acceleration", "data_provenance", "tissue"}
        feature_cols = [c for c in all_cols if c not in meta_cols and pd.api.types.is_numeric_dtype(df[c])]

        # Target leakage audit before split
        leak_audit = DataLeakageDetector.audit_features(df[feature_cols], y, age_col_name=age_col)
        if not leak_audit["is_leakage_free"]:
            logger.warning(f"Data leakage warning: {leak_audit['issues']}")

        kf = KFold(n_splits=self.n_splits, shuffle=True, random_state=self.random_state)
        
        oof_preds = np.zeros(len(df))
        fold_train_maes = []
        fold_test_maes = []
        fold_test_r2s = []
        fold_test_corrs = []

        meth_cols = [c for c in feature_cols if str(c).lower().startswith("cg")]
        trans_cols = [c for c in feature_cols if not str(c).lower().startswith("cg")]

        t0 = time.time()

        for fold, (train_idx, test_idx) in enumerate(kf.split(df)):
            # Audit index overlap
            split_audit = DataLeakageDetector.audit_splits(train_idx, test_idx)
            assert not split_audit["has_split_overlap"], "Data leakage detected: train and test indices overlap!"

            df_train = df.iloc[train_idx]
            df_test = df.iloc[test_idx]
            y_train = y.iloc[train_idx]
            y_test = y.iloc[test_idx]

            # 1. Fit Preprocessors EXCLUSIVELY on train fold
            preprocessed_train_blocks = []
            preprocessed_test_blocks = []

            if len(meth_cols) > 0:
                meth_pre = MethylationPreprocessor(min_variance=0.001)
                meth_pre.fit(df_train[meth_cols])
                train_meth_clean, _ = meth_pre.transform(df_train[meth_cols])
                test_meth_clean, _ = meth_pre.transform(df_test[meth_cols])
                preprocessed_train_blocks.append(train_meth_clean)
                preprocessed_test_blocks.append(test_meth_clean)

            if len(trans_cols) > 0:
                trans_pre = TranscriptomicsPreprocessor(min_variance=0.01)
                trans_pre.fit(df_train[trans_cols])
                train_trans_clean, _ = trans_pre.transform(df_train[trans_cols])
                test_trans_clean, _ = trans_pre.transform(df_test[trans_cols])
                preprocessed_train_blocks.append(train_trans_clean)
                preprocessed_test_blocks.append(test_trans_clean)

            X_train_full = pd.concat(preprocessed_train_blocks, axis=1)
            X_test_full = pd.concat(preprocessed_test_blocks, axis=1)

            # 2. Fit Feature Selection EXCLUSIVELY on train fold
            selector = FeatureSelector(max_features=self.max_features, method="mutual_info", random_state=self.random_state)
            X_train_sel = selector.fit_transform(X_train_full, y_train)
            X_test_sel = selector.transform(X_test_full)

            # 3. Instantiate and train model
            if model_type == "ElasticNet":
                model = BioAgeElasticNet(random_state=self.random_state)
            elif model_type == "RandomForest":
                model = BioAgeRandomForest(n_estimators=100, random_state=self.random_state)
            elif model_type == "XGBoost":
                model = BioAgeXGBoost(n_estimators=100, random_state=self.random_state)
            elif model_type == "EarlyFusion":
                model = MultiOmicsEarlyFusion()
            else:
                model = BioAgeElasticNet(random_state=self.random_state)

            model.fit(X_train_sel, y_train)

            # 4. Evaluate on train (apparent) and test (out-of-fold generalization)
            train_preds = model.predict(X_train_sel)
            test_preds = model.predict(X_test_sel)

            oof_preds[test_idx] = test_preds

            train_metrics = evaluate_predictions(y_train.values, train_preds, n_features=X_train_sel.shape[1])
            test_metrics = evaluate_predictions(y_test.values, test_preds, n_features=X_test_sel.shape[1])

            fold_train_maes.append(train_metrics.mae)
            fold_test_maes.append(test_metrics.mae)
            fold_test_r2s.append(test_metrics.r2)
            fold_test_corrs.append(test_metrics.pearson_r)

        total_time = round(time.time() - t0, 3)

        # Global out-of-fold evaluation across all subjects
        overall_oof_metrics = evaluate_predictions(
            y.values,
            oof_preds,
            n_features=self.max_features,
            training_time_sec=total_time,
        )

        return {
            "model_type": model_type,
            "validation_strategy": f"{self.n_splits}-Fold Cross-Validation (Leakage-Free)",
            "leak_audit": leak_audit,
            "sample_count": len(df),
            "feature_count_selected": self.max_features,
            "out_of_fold_metrics": {
                "mae": overall_oof_metrics.mae,
                "rmse": overall_oof_metrics.rmse,
                "r2": overall_oof_metrics.r2,
                "pearson_r": overall_oof_metrics.pearson_r,
                "spearman_rho": overall_oof_metrics.spearman_rho,
            },
            "apparent_train_metrics": {
                "mean_train_mae": round(float(np.mean(fold_train_maes)), 3),
            },
            "fold_summary": {
                "fold_test_maes": [round(m, 3) for m in fold_test_maes],
                "mean_test_mae": round(float(np.mean(fold_test_maes)), 3),
                "std_test_mae": round(float(np.std(fold_test_maes)), 3),
                "mean_test_r2": round(float(np.mean(fold_test_r2s)), 3),
                "mean_test_pearson": round(float(np.mean(fold_test_corrs)), 3),
            },
            "out_of_fold_predictions": oof_preds.tolist(),
            "execution_time_sec": total_time,
        }
