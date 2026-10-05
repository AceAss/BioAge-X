"""
DNA Methylation Preprocessing Pipeline for BioAge-X.
Handles Illumina 450K/EPIC beta-value matrices:
- Beta value validation and range checking [0.0, 1.0]
- Missingness filtering and imputation (median, mean, or constant)
- Low-variance probe removal
- CpG identifier validation and filtering
- Optional standardization or M-value conversion: M = log2(beta / (1 - beta))
- Detailed QC and transformation provenance
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from bioage.utils.logger import get_logger

logger = get_logger("bioage.preprocessing.methylation")


class MethylationPreprocessor:
    """Configurable preprocessing pipeline for DNA methylation microarray/sequencing data."""

    def __init__(
        self,
        max_missing_sample_rate: float = 0.20,
        max_missing_probe_rate: float = 0.10,
        min_variance: float = 0.002,
        imputation_strategy: str = "median",  # "median", "mean", "zero"
        convert_to_m_values: bool = False,
        standardize: bool = False,
        filter_cg_only: bool = True,
        cpg_whitelist: Optional[List[str]] = None,
    ):
        self.max_missing_sample_rate = max_missing_sample_rate
        self.max_missing_probe_rate = max_missing_probe_rate
        self.min_variance = min_variance
        self.imputation_strategy = imputation_strategy
        self.convert_to_m_values = convert_to_m_values
        self.standardize = standardize
        self.filter_cg_only = filter_cg_only
        self.cpg_whitelist = set(cpg_whitelist) if cpg_whitelist else None
        
        self.provenance: Dict[str, Any] = {}
        self.fitted_means_: Optional[pd.Series] = None
        self.fitted_stds_: Optional[pd.Series] = None
        self.impute_values_: Optional[pd.Series] = None
        self.selected_probes_: Optional[List[str]] = None

    def fit_transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Fits preprocessing parameters on the input DataFrame and transforms it."""
        return self.fit(df).transform(df)

    def fit(self, df: pd.DataFrame) -> "MethylationPreprocessor":
        """Computes filtering masks, imputation statistics, and normalization parameters."""
        raw_samples, raw_features = df.shape
        logger.info(f"Fitting MethylationPreprocessor on {raw_samples} samples, {raw_features} features")

        working_df = df.copy()

        # Step 1: Filter to CpG probes if requested
        if self.filter_cg_only:
            cg_cols = [c for c in working_df.columns if str(c).startswith("cg")]
            if len(cg_cols) > 0:
                working_df = working_df[cg_cols]
                logger.info(f"Retained {len(cg_cols)} probes starting with 'cg'")

        if self.cpg_whitelist:
            valid_cols = [c for c in working_df.columns if c in self.cpg_whitelist]
            if len(valid_cols) > 0:
                working_df = working_df[valid_cols]
                logger.info(f"Filtered to {len(valid_cols)} whitelist probes")

        # Step 2: Probe missingness filter
        probe_missing = working_df.isna().mean()
        valid_probes = probe_missing[probe_missing <= self.max_missing_probe_rate].index
        working_df = working_df[valid_probes]

        # Step 3: Compute imputation values
        if self.imputation_strategy == "median":
            self.impute_values_ = working_df.median()
        elif self.imputation_strategy == "mean":
            self.impute_values_ = working_df.mean()
        else:
            self.impute_values_ = pd.Series(0.0, index=working_df.columns)

        imputed_df = working_df.fillna(self.impute_values_)

        # Step 4: Low-variance filtering
        variances = imputed_df.var()
        high_var_probes = variances[variances >= self.min_variance].index.tolist()
        self.selected_probes_ = high_var_probes

        if not self.selected_probes_:
            logger.warning("No probes passed the variance threshold! Keeping top 50 highest variance probes.")
            self.selected_probes_ = variances.nlargest(min(50, len(variances))).index.tolist()

        filtered_df = imputed_df[self.selected_probes_]

        # Step 5: Standardization parameters
        if self.standardize:
            self.fitted_means_ = filtered_df.mean()
            self.fitted_stds_ = filtered_df.std().replace(0, 1.0)

        # Record provenance
        self.provenance = {
            "modality": "methylation",
            "initial_samples": raw_samples,
            "initial_probes": raw_features,
            "probes_after_cg_filter": len(working_df.columns),
            "probes_after_missing_filter": len(valid_probes),
            "probes_after_variance_filter": len(self.selected_probes_),
            "imputation_strategy": self.imputation_strategy,
            "min_variance_applied": self.min_variance,
            "converted_to_m_values": self.convert_to_m_values,
            "standardized": self.standardize,
        }
        return self

    def transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Applies the fitted preprocessing steps to a dataset."""
        if self.selected_probes_ is None or self.impute_values_ is None:
            raise RuntimeError("Preprocessor has not been fitted yet. Call fit() first.")

        # Align columns
        cols = [c for c in self.selected_probes_ if c in df.columns]
        missing_in_input = set(self.selected_probes_) - set(cols)
        
        working_df = df[cols].copy()
        
        # Add any missing expected probes with imputed mean
        for missing_col in missing_in_input:
            working_df[missing_col] = self.impute_values_[missing_col]

        # Reorder to match fit order
        working_df = working_df[self.selected_probes_]

        # Clip beta values to [0.0, 1.0] if biologically valid
        working_df = working_df.clip(lower=0.0, upper=1.0)

        # Impute
        working_df = working_df.fillna(self.impute_values_[self.selected_probes_])

        # Optional M-value conversion: M = log2(beta / (1 - beta)) with epsilon
        if self.convert_to_m_values:
            eps = 1e-4
            beta_clipped = working_df.clip(lower=eps, upper=1.0 - eps)
            working_df = np.log2(beta_clipped / (1.0 - beta_clipped))

        # Optional standardization
        if self.standardize and self.fitted_means_ is not None and self.fitted_stds_ is not None:
            working_df = (working_df - self.fitted_means_) / self.fitted_stds_

        return working_df, self.provenance
