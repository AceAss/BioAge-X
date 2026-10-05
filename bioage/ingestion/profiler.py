"""
Dataset Profiler for BioAge-X.
Analyzes uploaded multi-omics datasets: checks orientation, detects sample/feature IDs,
computes missingness, duplicate rates, and detects metadata columns like chronological age.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

from bioage.utils.logger import get_logger

logger = get_logger("bioage.ingestion.profiler")


@dataclass
class DatasetProfile:
    """Standardized profile representation of an ingested dataset."""
    n_samples: int
    n_features: int
    orientation: str  # "samples_by_features" or "features_by_samples"
    missing_fraction: float
    duplicate_features: int
    duplicate_samples: int
    sample_id_column: Optional[str] = None
    age_column: Optional[str] = None
    detected_modality: str = "unknown"  # "methylation", "transcriptomics", "multimodal", "clinical"
    numeric_feature_count: int = 0
    metadata_columns: List[str] = field(default_factory=list)
    feature_id_sample: List[str] = field(default_factory=list)
    sample_id_sample: List[str] = field(default_factory=list)
    suspicious_columns: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DatasetProfiler:
    """Profiles multi-omics tabular datasets before preprocessing."""

    AGE_COLUMN_CANDIDATES = [
        "age", "chronological_age", "age_years", "chron_age",
        "sample_age", "host_age", "patient_age"
    ]
    SAMPLE_ID_CANDIDATES = [
        "sample_id", "sampleid", "id", "sample", "subject_id",
        "patient_id", "barcode", "gsm", "tcga_id"
    ]

    def __init__(self, cpg_prefix: str = "cg", max_sample_preview: int = 10):
        self.cpg_prefix = cpg_prefix
        self.max_sample_preview = max_sample_preview

    def profile_dataframe(
        self,
        df: pd.DataFrame,
        assumed_orientation: Optional[str] = None
    ) -> Tuple[pd.DataFrame, DatasetProfile]:
        """
        Profiles the DataFrame and returns a standardized (samples as rows) DataFrame
        along with the DatasetProfile.
        """
        warnings = []
        suspicious_columns = []

        # 1. Orientation inference
        # If columns start with 'cg' or typical gene symbols, or num_rows is small (< 500) and num_cols is huge (> 1000),
        # standard is samples_by_features.
        # Conversely, if row index looks like gene symbols/CpGs and columns are sample IDs (e.g. GSM123, Sample_1),
        # it's features_by_samples.
        orientation = assumed_orientation or self._infer_orientation(df)
        
        working_df = df.copy()
        if orientation == "features_by_samples":
            warnings.append(
                "Inferred features_by_samples orientation; transposed so samples are rows."
            )
            working_df = working_df.T
            orientation_detected = "features_by_samples"
        else:
            orientation_detected = "samples_by_features"

        # 2. Identify Sample ID column if present as a column
        sample_id_col = self._detect_candidate_column(working_df, self.SAMPLE_ID_CANDIDATES)
        if sample_id_col is not None:
            working_df = working_df.set_index(sample_id_col)
            working_df.index.name = "sample_id"

        # 3. Identify Chronological Age column if present
        age_col = self._detect_candidate_column(working_df, self.AGE_COLUMN_CANDIDATES)

        # 4. Separate metadata vs omics numeric features
        metadata_cols = []
        numeric_cols = []
        for col in working_df.columns:
            if col == age_col:
                metadata_cols.append(col)
                continue
            is_num = pd.api.types.is_numeric_dtype(working_df[col])
            if is_num:
                numeric_cols.append(col)
            else:
                metadata_cols.append(col)

        # 5. Missingness analysis
        total_cells = working_df.shape[0] * working_df.shape[1]
        missing_count = working_df.isna().sum().sum()
        missing_fraction = float(missing_count / total_cells) if total_cells > 0 else 0.0

        if missing_fraction > 0.30:
            warnings.append(f"High missingness detected ({missing_fraction:.1%}). Substantial imputation required.")

        # 6. Duplicates
        duplicate_samples = int(working_df.index.duplicated().sum())
        duplicate_features = int(pd.Series(working_df.columns).duplicated().sum())
        if duplicate_samples > 0:
            warnings.append(f"Found {duplicate_samples} duplicate sample IDs.")
        if duplicate_features > 0:
            warnings.append(f"Found {duplicate_features} duplicate feature IDs.")

        # 7. Check for suspicious / zero variance columns in numeric features
        if numeric_cols:
            variances = working_df[numeric_cols].var()
            zero_var_cols = variances[variances == 0].index.tolist()
            if zero_var_cols:
                suspicious_columns.extend(zero_var_cols[:20])
                warnings.append(f"Found {len(zero_var_cols)} invariant features with zero variance.")

        # 8. Modality detection
        detected_modality = self._detect_modality(numeric_cols, working_df)

        # 9. Previews
        feature_preview = [str(c) for c in numeric_cols[:self.max_sample_preview]]
        sample_preview = [str(s) for s in working_df.index[:self.max_sample_preview]]

        n_samples = working_df.shape[0]
        n_features = len(numeric_cols)

        profile = DatasetProfile(
            n_samples=n_samples,
            n_features=n_features,
            orientation=orientation_detected,
            missing_fraction=round(missing_fraction, 4),
            duplicate_features=duplicate_features,
            duplicate_samples=duplicate_samples,
            sample_id_column=sample_id_col,
            age_column=age_col,
            detected_modality=detected_modality,
            numeric_feature_count=n_features,
            metadata_columns=metadata_cols,
            feature_id_sample=feature_preview,
            sample_id_sample=sample_preview,
            suspicious_columns=suspicious_columns,
            warnings=warnings,
        )

        logger.info(
            f"Profiled dataset: {n_samples} samples, {n_features} features, "
            f"modality={detected_modality}, missing={missing_fraction:.2%}"
        )
        return working_df, profile

    def _infer_orientation(self, df: pd.DataFrame) -> str:
        """Heuristically infers whether matrix is samples_by_features or features_by_samples."""
        n_rows, n_cols = df.shape
        # Check column names: do they look like CpG probes or genes?
        col_cpg_count = sum(1 for c in df.columns[:50] if str(c).lower().startswith(self.cpg_prefix))
        row_cpg_count = sum(1 for r in df.index[:50] if str(r).lower().startswith(self.cpg_prefix))

        if col_cpg_count > 5:
            return "samples_by_features"
        if row_cpg_count > 5:
            return "features_by_samples"

        # If columns are mostly string sample IDs and rows are thousands of features:
        if n_rows > n_cols and n_cols < 300 and n_rows > 1000:
            return "features_by_samples"

        return "samples_by_features"

    def _detect_candidate_column(self, df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
        """Finds if any column matches common metadata candidate names (case-insensitive)."""
        lower_cols = {str(col).lower().strip(): col for col in df.columns}
        for cand in candidates:
            if cand in lower_cols:
                return lower_cols[cand]
        return None

    def _detect_modality(self, numeric_cols: List[str], df: pd.DataFrame) -> str:
        """Determines if data is methylation (beta values 0-1, cg probes) or transcriptomics (counts/TPM)."""
        if not numeric_cols:
            return "clinical"

        cpg_matches = sum(1 for c in numeric_cols[:100] if str(c).lower().startswith(self.cpg_prefix))
        if cpg_matches > 10:
            return "methylation"

        # Check numerical distribution (beta values lie between 0.0 and 1.0)
        sample_subset = df[numeric_cols[:min(30, len(numeric_cols))]].dropna()
        if not sample_subset.empty:
            q_min = sample_subset.min().min()
            q_max = sample_subset.max().max()
            if 0.0 <= q_min and q_max <= 1.05:
                return "methylation"

        return "transcriptomics"
