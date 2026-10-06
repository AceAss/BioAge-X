"""
Dataset Normalization Engine for BioAge-X.
Translates diverse repository matrices (GEO series matrices, GDC TSVs,
ArrayExpress SDRF alignments, generic TSVs/CSVs) into canonical BioAge-X orientation.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np

from bioage.ingestion.profiler import DatasetProfiler
from bioage.utils.logger import get_logger

logger = get_logger("bioage.acquisition.normalizer")


class DatasetNormalizer:
    """Standardizes row/column orientations, feature IDs, and clinical age mappings."""

    AGE_ALIASES = [
        "chronological_age",
        "age",
        "donor_age",
        "age_years",
        "age_at_index",
        "characteristics[age]",
        "age:ch1",
        "characteristics_ch1.age",
    ]

    SAMPLE_ID_ALIASES = [
        "sample_id",
        "sample",
        "id",
        "subject_id",
        "geo_accession",
        "sample_name",
        "barcode",
        "case_id",
    ]

    @classmethod
    def normalize_tabular_file(
        cls,
        source_path: Path,
        output_path: Path,
        target_age_col: Optional[str] = None,
        target_sample_id_col: Optional[str] = None,
    ) -> Tuple[Path, Dict[str, Any]]:
        """
        Loads, checks orientation, normalizes sample and feature identifiers,
        and saves standardized CSV representation.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        name_lower = source_path.name.lower()
        sep = "\t" if (name_lower.endswith(".tsv") or name_lower.endswith(".tab") or name_lower.endswith(".txt")) else ","

        # Load dataframe
        if name_lower.endswith(".parquet"):
            df = pd.read_parquet(source_path)
        elif name_lower.endswith(".xlsx") or name_lower.endswith(".xls"):
            df = pd.read_excel(source_path)
        else:
            # Handle comment lines (e.g. GEO series matrix headers starting with ! or #)
            df = pd.read_csv(source_path, sep=sep, comment="!", low_memory=False)

        # 1. Detect orientation: features-by-samples vs samples-by-features
        # If the first column contains gene symbols or CpG IDs and columns look like sample barcodes (GSM, TCGA, S01...)
        cols = list(df.columns)
        first_col = cols[0]
        first_col_vals = [str(v) for v in df[first_col].dropna().head(20)]

        is_cpg_probe_index = any(re.match(r"^cg\d+", v, re.I) for v in first_col_vals)
        is_gene_index = any(re.match(r"^(ENSG|ILMN|\b[A-Z0-9]{3,8}\b)", v) for v in first_col_vals)
        num_cols = len(cols)
        num_rows = len(df)

        # If thousands of rows (e.g. 20,000 genes) and few columns (e.g. 50 samples)
        if (num_rows > 200 and num_cols < 200) and (is_cpg_probe_index or is_gene_index):
            logger.info("Detected features-by-samples orientation. Transposing matrix to samples-by-features...")
            df = df.set_index(first_col).T
            df.index.name = "sample_id"
            df = df.reset_index()
            cols = list(df.columns)

        # 2. Harmonize sample_id column
        sample_col_found = target_sample_id_col
        if not sample_col_found:
            for alias in cls.SAMPLE_ID_ALIASES:
                matches = [c for c in cols if c.lower() == alias.lower()]
                if matches:
                    sample_col_found = matches[0]
                    break

        if sample_col_found and sample_col_found != "sample_id":
            df = df.rename(columns={sample_col_found: "sample_id"})
        elif "sample_id" not in df.columns:
            # Create synthetic sample_id
            df.insert(0, "sample_id", [f"SAMPLE_{i+1:04d}" for i in range(len(df))])

        # 3. Harmonize chronological_age column
        age_col_found = target_age_col
        if not age_col_found:
            for alias in cls.AGE_ALIASES:
                matches = [c for c in cols if alias.lower() in c.lower()]
                if matches:
                    age_col_found = matches[0]
                    break

        if age_col_found and age_col_found != "chronological_age":
            # Extract numeric age from strings like "age: 45" or "45 years"
            try:
                def clean_age(val):
                    if pd.isna(val):
                        return np.nan
                    m = re.search(r"(\d+(\.\d+)?)", str(val))
                    return float(m.group(1)) if m else np.nan

                df["chronological_age"] = df[age_col_found].apply(clean_age)
                if age_col_found in df.columns and age_col_found != "chronological_age":
                    df = df.drop(columns=[age_col_found])
            except Exception as e:
                logger.warning(f"Could not convert age column {age_col_found}: {e}")

        # Ensure age column is float if present
        if "chronological_age" in df.columns:
            df["chronological_age"] = pd.to_numeric(df["chronological_age"], errors="coerce")

        # Save normalized CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Saved normalized dataset ({len(df)} samples, {df.shape[1]} features) to {output_path}")

        # Generate comprehensive DatasetProfile
        profiler = DatasetProfiler()
        profile = profiler.profile_dataset(output_path)

        return output_path, profile.to_dict()
