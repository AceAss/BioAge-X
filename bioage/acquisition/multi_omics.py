"""
Multi-Omics Alignment and Dataset Assembly Service for BioAge-X.
Merges distinct single-modality datasets (DNA methylation, transcriptomics,
clinical metadata) across shared sample IDs with explicit overlap auditing.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np

from bioage.utils.logger import get_logger

logger = get_logger("bioage.acquisition.multi_omics")


class MultiOmicsAssembler:
    """
    Harmonizes multi-omics cohorts by aligning sample barcodes/IDs.
    Calculates exact cohort overlaps and executes intersection or union merges.
    """

    @staticmethod
    def inspect_sample_overlap(
        datasets: Dict[str, pd.DataFrame],
        sample_id_col: str = "sample_id",
    ) -> Dict[str, Any]:
        """
        Audits sample ID distributions across input modality datasets.
        Returns detailed set operations breakdown without mutating data.
        """
        sample_sets: Dict[str, set] = {}
        for name, df in datasets.items():
            if sample_id_col in df.columns:
                s_ids = set(df[sample_id_col].astype(str).str.strip())
            else:
                s_ids = set(df.index.astype(str).str.strip())
            sample_sets[name] = s_ids

        all_names = list(sample_sets.keys())
        all_samples = set.union(*sample_sets.values()) if sample_sets else set()
        intersection_samples = set.intersection(*sample_sets.values()) if sample_sets else set()

        # Modality-exclusive samples
        exclusive_breakdown: Dict[str, int] = {}
        for name, s_set in sample_sets.items():
            other_sets = [sample_sets[other] for other in all_names if other != name]
            other_union = set.union(*other_sets) if other_sets else set()
            exclusive = s_set - other_union
            exclusive_breakdown[f"{name}_only"] = len(exclusive)

        return {
            "total_unique_samples_union": len(all_samples),
            "complete_multiomics_intersection": len(intersection_samples),
            "per_modality_counts": {name: len(s_set) for name, s_set in sample_sets.items()},
            "exclusive_sample_counts": exclusive_breakdown,
            "intersection_sample_sample": sorted(list(intersection_samples))[:10],
        }

    @classmethod
    def assemble_cohort(
        cls,
        datasets: Dict[str, pd.DataFrame],
        strategy: str = "intersection",  # "intersection" or "union"
        sample_id_col: str = "sample_id",
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Merges datasets according to specified scientific strategy:
        - 'intersection': Retains only complete cases with all omics layers present.
        - 'union': Retains all observed subjects, filling unobserved layers with NaN.
        """
        overlap_audit = cls.inspect_sample_overlap(datasets, sample_id_col=sample_id_col)
        all_names = list(datasets.keys())
        if not all_names:
            return pd.DataFrame(), overlap_audit

        # Ensure sample_id is present as column in all dataframes
        prepared = {}
        for name, df in datasets.items():
            df_copy = df.copy()
            if sample_id_col not in df_copy.columns:
                df_copy.insert(0, sample_id_col, df_copy.index.astype(str))
            df_copy[sample_id_col] = df_copy[sample_id_col].astype(str).str.strip()
            prepared[name] = df_copy

        # First dataset
        base_name = all_names[0]
        merged_df = prepared[base_name]

        join_how = "inner" if strategy == "intersection" else "outer"

        for other_name in all_names[1:]:
            other_df = prepared[other_name]
            # Avoid duplicate non-sample columns by suffixing if duplicate
            overlap_cols = [c for c in other_df.columns if c in merged_df.columns and c != sample_id_col]
            if overlap_cols:
                # If chronological_age is present in both, keep the first non-null
                if "chronological_age" in overlap_cols:
                    overlap_cols.remove("chronological_age")
                other_df = other_df.rename(columns={c: f"{c}_{other_name}" for c in overlap_cols})

            merged_df = pd.merge(merged_df, other_df, on=sample_id_col, how=join_how)

        # Move sample_id and chronological_age to front
        front_cols = [sample_id_col]
        if "chronological_age" in merged_df.columns:
            front_cols.append("chronological_age")
        other_cols = [c for c in merged_df.columns if c not in front_cols]
        merged_df = merged_df[front_cols + other_cols]

        result_meta = {
            "strategy": strategy,
            "assembled_samples": len(merged_df),
            "assembled_features": merged_df.shape[1],
            "overlap_audit": overlap_audit,
        }
        logger.info(
            f"Assembled multi-omics cohort ({strategy}): {len(merged_df)} samples, {merged_df.shape[1]} features"
        )
        return merged_df, result_meta
