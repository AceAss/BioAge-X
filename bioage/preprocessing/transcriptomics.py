"""
Transcriptomics Preprocessing Pipeline for BioAge-X.
Handles RNA-seq counts, TPM, or microarray gene expression matrices:
- Expression validation (non-negativity, missingness)
- Low-expression gene filtering (min counts, min expressing samples)
- Log transformation: log2(expression + 1)
- Library-size / CPM normalization
- Highly variable gene (HVG) selection / variance filtering
- Full QC summary & transformation provenance
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from bioage.utils.logger import get_logger

logger = get_logger("bioage.preprocessing.transcriptomics")


class TranscriptomicsPreprocessor:
    """Configurable pipeline for transcriptomic expression matrices."""

    def __init__(
        self,
        min_samples_expressed: float = 0.10,  # Expressed in at least 10% of samples
        min_expression_threshold: float = 1.0,
        apply_cpm_normalization: bool = True,
        target_counts: float = 1e6,  # CPM standard (Counts Per Million)
        apply_log1p: bool = True,
        min_variance: float = 0.05,
        imputation_strategy: str = "zero",  # "zero", "median", "mean"
    ):
        self.min_samples_expressed = min_samples_expressed
        self.min_expression_threshold = min_expression_threshold
        self.apply_cpm_normalization = apply_cpm_normalization
        self.target_counts = target_counts
        self.apply_log1p = apply_log1p
        self.min_variance = min_variance
        self.imputation_strategy = imputation_strategy

        self.provenance: Dict[str, Any] = {}
        self.selected_genes_: Optional[List[str]] = None
        self.impute_values_: Optional[pd.Series] = None
        self.fitted_means_: Optional[pd.Series] = None
        self.fitted_stds_: Optional[pd.Series] = None

    def fit_transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Fits preprocessing parameters and transforms the dataset."""
        return self.fit(df).transform(df)

    def fit(self, df: pd.DataFrame) -> "TranscriptomicsPreprocessor":
        """Identifies genes meeting expression and variance criteria."""
        raw_samples, raw_features = df.shape
        logger.info(f"Fitting TranscriptomicsPreprocessor on {raw_samples} samples, {raw_features} genes")

        working_df = df.copy()

        # Step 1: Missing value handling
        if self.imputation_strategy == "median":
            self.impute_values_ = working_df.median()
        elif self.imputation_strategy == "mean":
            self.impute_values_ = working_df.mean()
        else:
            self.impute_values_ = pd.Series(0.0, index=working_df.columns)

        working_df = working_df.fillna(self.impute_values_)

        # Ensure non-negative expression
        working_df = working_df.clip(lower=0.0)

        # Step 2: Low-expression filtering
        n_samples = working_df.shape[0]
        min_sample_count = max(1, int(self.min_samples_expressed * n_samples))
        is_expressed = (working_df >= self.min_expression_threshold).sum(axis=0) >= min_sample_count
        expressed_genes = working_df.columns[is_expressed].tolist()

        if len(expressed_genes) == 0:
            logger.warning("No genes passed expression threshold; keeping top 50 by mean expression.")
            expressed_genes = working_df.mean().nlargest(min(50, raw_features)).index.tolist()

        working_df = working_df[expressed_genes]

        # Step 3: CPM normalization
        if self.apply_cpm_normalization:
            lib_sizes = working_df.sum(axis=1)
            # Avoid division by zero
            lib_sizes = lib_sizes.replace(0, 1.0)
            working_df = working_df.div(lib_sizes, axis=0) * self.target_counts

        # Step 4: Log transformation
        if self.apply_log1p:
            working_df = np.log2(working_df + 1.0)

        # Step 5: High variance filtering
        variances = working_df.var()
        high_var_genes = variances[variances >= self.min_variance].index.tolist()
        if not high_var_genes:
            high_var_genes = variances.nlargest(min(50, len(variances))).index.tolist()

        self.selected_genes_ = high_var_genes

        self.provenance = {
            "modality": "transcriptomics",
            "initial_samples": raw_samples,
            "initial_genes": raw_features,
            "genes_after_expression_filter": len(expressed_genes),
            "genes_after_variance_filter": len(self.selected_genes_),
            "cpm_normalized": self.apply_cpm_normalization,
            "log1p_transformed": self.apply_log1p,
            "min_variance": self.min_variance,
            "imputation_strategy": self.imputation_strategy,
        }
        return self

    def transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Transforms new transcriptomic data according to fitted parameters."""
        if self.selected_genes_ is None or self.impute_values_ is None:
            raise RuntimeError("Preprocessor has not been fitted yet. Call fit() first.")

        cols = [c for c in self.selected_genes_ if c in df.columns]
        missing_in_input = set(self.selected_genes_) - set(cols)

        working_df = df[cols].copy()
        for missing_col in missing_in_input:
            working_df[missing_col] = self.impute_values_[missing_col]

        working_df = working_df[self.selected_genes_]
        working_df = working_df.fillna(self.impute_values_[self.selected_genes_])
        working_df = working_df.clip(lower=0.0)

        if self.apply_cpm_normalization:
            lib_sizes = working_df.sum(axis=1).replace(0, 1.0)
            working_df = working_df.div(lib_sizes, axis=0) * self.target_counts

        if self.apply_log1p:
            working_df = np.log2(working_df + 1.0)

        return working_df, self.provenance
