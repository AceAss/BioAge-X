"""Unit tests for DatasetProfiler and Ingestion in BioAge-X."""

import numpy as np
import pandas as pd
import pytest

from bioage.ingestion.profiler import DatasetProfiler


def test_profiler_samples_by_features():
    df = pd.DataFrame({
        "sample_id": ["S1", "S2", "S3", "S4"],
        "chronological_age": [25.0, 45.0, 65.0, 80.0],
        "cg16867657": [0.2, 0.4, 0.6, 0.8],
        "cg06639320": [0.3, 0.5, 0.7, 0.9],
        "GENE_TP53": [5.1, 5.8, 6.2, 7.1],
    })

    profiler = DatasetProfiler()
    std_df, profile = profiler.profile_dataframe(df)

    assert profile.n_samples == 4
    assert profile.n_features == 3
    assert profile.orientation == "samples_by_features"
    assert profile.age_column == "chronological_age"
    assert profile.detected_modality in {"methylation", "transcriptomics", "multimodal"}
    assert profile.missing_fraction == 0.0


def test_profiler_transposed_features_by_samples():
    # Rows are probes, columns are GSM sample IDs
    df = pd.DataFrame(
        {
            "GSM001": [0.2, 0.3, 0.4],
            "GSM002": [0.5, 0.6, 0.7],
            "GSM003": [0.8, 0.9, 0.95],
        },
        index=["cg0001", "cg0002", "cg0003"],
    )

    profiler = DatasetProfiler()
    std_df, profile = profiler.profile_dataframe(df, assumed_orientation="features_by_samples")

    assert profile.n_samples == 3
    assert profile.n_features == 3
    assert profile.orientation == "features_by_samples"
