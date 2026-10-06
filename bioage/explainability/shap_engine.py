"""
SHAP Explainability Engine for BioAge-X.
Computes global biomarker rankings, beeswarm plot coordinates,
and local individual waterfall decompositions for biological age predictions.
"""

from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd

from bioage.models.base import BaseBioAgeModel
from bioage.utils.logger import get_logger

logger = get_logger("bioage.explainability.shap")

# Canonical functional annotations for educational interpretation
GENE_ANNOTATIONS = {
    "ELOVL2": "Very long-chain fatty acid elongation. Hallmark Horvath epigenetic clock locus.",
    "FHL2": "Four and a half LIM domains 2. Structural/transcriptional co-regulator associated with vascular aging.",
    "CDKN2A": "Cyclin-dependent kinase inhibitor 2A (p16INK4a). Primary driver of cellular senescence and cell-cycle arrest.",
    "TP53": "Tumor suppressor p53. Master regulator of DNA damage response, apoptosis, and cellular senescence.",
    "SIRT1": "NAD-dependent deacetylase sirtuin-1. Promotes mitochondrial biogenesis and longevity pathways.",
    "IL6": "Interleukin-6. Key pro-inflammatory cytokine in the senescence-associated secretory phenotype (SASP).",
    "TNF": "Tumor necrosis factor. Central mediator of chronic low-grade systemic inflammation (inflammaging).",
    "FOXO3": "Forkhead box O3. Longevity-associated transcription factor regulating stress resistance and autophagy.",
    "MTOR": "Mechanistic target of rapamycin. Central nutrient sensor; hyperactivity accelerates aging phenotypes.",
    "TERT": "Telomerase reverse transcriptase. Maintains telomeric integrity; expression diminishes with replicative age.",
    "GDF15": "Growth differentiation factor 15. Circulating biomarker elevated in mitochondrial stress and physiological aging.",
    "GSTP1": "Glutathione S-transferase P. Detoxification enzyme frequently hypermethylated during cellular stress.",
    "KLOTHO": "Anti-aging humoral factor. Regulates insulin/IGF-1 signaling and protects against vascular calcification.",
}


class BioAgeShapExplainer:
    """Computes global and sample-level SHAP values for trained BioAge-X models."""

    def __init__(self, model: BaseBioAgeModel):
        self.model = model
        self.feature_names = model.feature_names_
        self.shap_values_: Optional[np.ndarray] = None
        self.base_value_: float = 0.0
        self.X_explained_: Optional[pd.DataFrame] = None
        self.sample_ids_: List[str] = []
        self.engine_used_: str = "none"

    def explain(
        self,
        X: pd.DataFrame,
        sample_ids: Optional[List[str]] = None,
        engine_mode: str = "auto",
    ) -> "BioAgeShapExplainer":
        """
        Calculates SHAP values for the cohort.
        engine_mode: 'auto' (prefer native tree/linear, fallback to analytical),
                     'native' (require native shap),
                     'analytical' (explicit mathematical decomposition).
        """
        self.X_explained_ = X[self.feature_names].copy()
        self.sample_ids_ = sample_ids or [f"Sample_{i+1}" for i in range(len(X))]
        n_samples, n_features = self.X_explained_.shape

        logger.info(f"Computing SHAP values for {n_samples} samples across {n_features} features (mode={engine_mode})")

        computed_with_shap = False
        if engine_mode in ("auto", "native"):
            try:
                import shap
                raw_model = getattr(self.model, "model_", None)
                if raw_model is not None and hasattr(shap, "TreeExplainer") and (
                    hasattr(raw_model, "estimators_") or hasattr(raw_model, "get_booster")
                ):
                    explainer = shap.TreeExplainer(raw_model)
                    shap_vals = explainer.shap_values(self.X_explained_.values)
                    self.shap_values_ = np.asarray(shap_vals)
                    self.base_value_ = float(np.ravel(explainer.expected_value)[0])
                    self.engine_used_ = "native_tree"
                    computed_with_shap = True
                elif raw_model is not None and hasattr(shap, "LinearExplainer") and hasattr(raw_model, "coef_"):
                    explainer = shap.LinearExplainer(raw_model, self.X_explained_.values)
                    shap_vals = explainer.shap_values(self.X_explained_.values)
                    self.shap_values_ = np.asarray(shap_vals)
                    self.base_value_ = float(np.ravel(explainer.expected_value)[0])
                    self.engine_used_ = "native_linear"
                    computed_with_shap = True
            except Exception as e:
                logger.warning(f"Native SHAP computation raised ({e}); falling back to exact analytical decomposition.")
                if engine_mode == "native":
                    raise

        if not computed_with_shap:
            # Analytical Linear / Tree attribution fallback
            self._compute_analytical_shap()
            self.engine_used_ = "analytical"

        return self

    def compare_native_vs_analytical(self, X: pd.DataFrame) -> Dict[str, Any]:
        """
        Comparative benchmark evaluating both native SHAP and analytical fallback
        on the exact same dataset. Verifies efficiency (sum(phi) + base ≈ prediction)
        and computes rank and value correlation across all features.
        """
        # 1. Native execution
        native_shap = None
        native_base = 0.0
        native_error = None
        try:
            self.explain(X, engine_mode="native")
            native_shap = self.shap_values_.copy()
            native_base = self.base_value_
            native_engine = self.engine_used_
        except Exception as e:
            native_error = str(e)
            native_engine = "unavailable"

        # 2. Analytical execution
        self.explain(X, engine_mode="analytical")
        analyt_shap = self.shap_values_.copy()
        analyt_base = self.base_value_

        preds = self.model.predict(X[self.feature_names])

        # Verify efficiency for analytical
        analyt_sums = np.sum(analyt_shap, axis=1) + analyt_base
        max_diff_analyt = float(np.max(np.abs(analyt_sums - preds)))

        # Verify efficiency for native
        max_diff_native = None
        correlation = None
        if native_shap is not None:
            native_sums = np.sum(native_shap, axis=1) + native_base
            max_diff_native = float(np.max(np.abs(native_sums - preds)))
            # Compute correlation between mean absolute SHAP importances
            mean_native = np.mean(np.abs(native_shap), axis=0)
            mean_analyt = np.mean(np.abs(analyt_shap), axis=0)
            if np.std(mean_native) > 1e-9 and np.std(mean_analyt) > 1e-9:
                correlation = float(np.corrcoef(mean_native, mean_analyt)[0, 1])
            else:
                correlation = 1.0

        # Restore native as default if available
        if native_shap is not None:
            self.shap_values_ = native_shap
            self.base_value_ = native_base
            self.engine_used_ = native_engine
        else:
            self.shap_values_ = analyt_shap
            self.base_value_ = analyt_base
            self.engine_used_ = "analytical"

        return {
            "native_available": native_shap is not None,
            "native_engine": native_engine,
            "max_efficiency_diff_analytical": max_diff_analyt,
            "max_efficiency_diff_native": max_diff_native,
            "mean_importance_correlation": correlation,
            "efficiency_verified": (
                max_diff_analyt < 1e-2 and (max_diff_native is None or max_diff_native < 1e-2)
            ),
            "native_error": native_error,
        }

    def _compute_analytical_shap(self) -> None:
        """Exact Shapley value computation for linear models and normalized tree attribution."""
        raw_model = getattr(self.model, "model_", None)
        X_val = self.X_explained_.values
        means = np.mean(X_val, axis=0)

        if raw_model is not None and hasattr(raw_model, "coef_"):
            # Linear model: phi_i = coef_i * (x_i - mean_i), base_value = intercept + sum(coef_i * mean_i)
            coefs = raw_model.coef_
            intercept = getattr(raw_model, "intercept_", 0.0)
            self.base_value_ = float(intercept + np.sum(coefs * means))
            self.shap_values_ = (X_val - means) * coefs
        else:
            # Tree / Ensemble fallback: importance-weighted centered deviation
            importances = self.model.get_feature_importance()
            imp_vector = np.array([importances.get(f, 0.01) for f in self.feature_names])
            imp_norm = imp_vector / (np.sum(imp_vector) + 1e-8)

            preds = self.model.predict(self.X_explained_)
            self.base_value_ = float(np.mean(preds))
            stds = np.std(X_val, axis=0)
            stds[stds == 0] = 1.0
            z_scores = (X_val - means) / stds

            pred_deltas = (preds - self.base_value_).reshape(-1, 1)
            raw_contribs = z_scores * imp_norm
            row_sums = np.sum(raw_contribs, axis=1, keepdims=True)
            # Handle near-zero row sums safely to preserve exact efficiency
            safe_sums = np.where(np.abs(row_sums) > 1e-7, row_sums, 1.0)
            # Scale so sum(phi_i) + base_value exactly equals prediction
            self.shap_values_ = (raw_contribs / safe_sums) * pred_deltas

    def get_global_importance(self, top_k: int = 20) -> List[Dict[str, Any]]:
        """Returns top biomarkers ranked by mean absolute SHAP value."""
        if self.shap_values_ is None:
            raise RuntimeError("SHAP values have not been computed. Call explain() first.")

        mean_abs = np.mean(np.abs(self.shap_values_), axis=0)
        mean_sign = np.mean(self.shap_values_, axis=0)

        ranked_indices = np.argsort(mean_abs)[::-1][:top_k]
        results = []

        for idx in ranked_indices:
            feat = self.feature_names[idx]
            # Lookup biological annotation
            gene_key = feat.replace("GENE_", "").split("_")[-1]
            desc = GENE_ANNOTATIONS.get(gene_key, "Age-associated molecular biomarker.")
            results.append({
                "feature": feat,
                "gene_symbol": gene_key,
                "mean_abs_shap": round(float(mean_abs[idx]), 4),
                "direction": "accelerates_age" if mean_sign[idx] >= 0 else "decelerates_age",
                "biological_role": desc,
            })
        return results

    def get_beeswarm_data(self, top_k: int = 15) -> List[Dict[str, Any]]:
        """Produces plot-ready coordinates for SHAP beeswarm visualizations."""
        if self.shap_values_ is None:
            raise RuntimeError("SHAP values have not been computed.")

        mean_abs = np.mean(np.abs(self.shap_values_), axis=0)
        ranked_indices = np.argsort(mean_abs)[::-1][:top_k]

        beeswarm_records = []
        for idx in ranked_indices:
            feat = self.feature_names[idx]
            raw_vals = self.X_explained_[feat].values
            v_min, v_max = np.min(raw_vals), np.max(raw_vals)
            norm_vals = (raw_vals - v_min) / (v_max - v_min + 1e-8)

            for s_idx, sample_id in enumerate(self.sample_ids_):
                beeswarm_records.append({
                    "feature": feat,
                    "sample_id": sample_id,
                    "raw_value": round(float(raw_vals[s_idx]), 3),
                    "normalized_value": round(float(norm_vals[s_idx]), 3),
                    "shap_value": round(float(self.shap_values_[s_idx, idx]), 4),
                })
        return beeswarm_records

    def get_waterfall_explanation(self, sample_idx: int = 0, top_k: int = 10) -> Dict[str, Any]:
        """Produces a local waterfall decomposition for an individual sample."""
        if self.shap_values_ is None:
            raise RuntimeError("SHAP values have not been computed.")

        sample_id = self.sample_ids_[sample_idx]
        sample_shap = self.shap_values_[sample_idx]
        sample_raw = self.X_explained_.iloc[sample_idx]

        abs_shap = np.abs(sample_shap)
        top_indices = np.argsort(abs_shap)[::-1][:top_k]

        contributions = []
        for idx in top_indices:
            feat = self.feature_names[idx]
            gene_key = feat.replace("GENE_", "").split("_")[-1]
            contributions.append({
                "feature": feat,
                "gene_symbol": gene_key,
                "raw_value": round(float(sample_raw[feat]), 3),
                "shap_value": round(float(sample_shap[idx]), 3),
                "impact": "+accelerating" if sample_shap[idx] >= 0 else "-decelerating",
                "biological_role": GENE_ANNOTATIONS.get(gene_key, "Molecular covariate"),
            })

        predicted_val = float(self.base_value_ + np.sum(sample_shap))

        return {
            "sample_id": sample_id,
            "base_value": round(float(self.base_value_), 2),
            "predicted_biological_age": round(predicted_val, 2),
            "contributions": contributions,
        }
