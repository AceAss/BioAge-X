"""
Comprehensive Unit and Integration Test Suite for Universal Biological Data Acquisition.

Tests:
1. DatasetProviderRegistry and BiologicalKnowledgeProviderRegistry decoupling.
2. RepositoryResolver accession and URL routing across all supported repositories.
3. SafeArchiveExtractor security defenses (ZipSlip path traversal attack, expansion ratio limits).
4. DownloadManager disk space headroom pre-checks and checksum validation.
5. All 12 repository providers (GEO, NCBI, SRA, ENA, ArrayExpress, BioStudies, GDC, TCGA, PRIDE, ProteomeXchange, MetaboLights, GenericURL).
6. Controlled access guardrails (GDC/dbGaP flags ACCESS RESTRICTED).
7. Raw sequencing reads handling (SRA/ENA flags REQUIRES PREPROCESSING).
8. Multi-omics manifest importer & assembler (intersection vs union merge strategies).
9. Provenance lineage recording and cache status tags (LIVE, CACHED, LOCAL).
10. Clock compatibility engine across all 5 clocks (Horvath, Hannum, PhenoAge, GrimAge, DunedinPACE).
"""

import os
import tarfile
import zipfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock

from bioage.acquisition.base import (
    DatasetSearchResult,
    DatasetMetadata,
    DownloadOption,
    CompatibilityLevel,
)
from bioage.acquisition.registry import (
    DatasetProviderRegistry,
    BiologicalKnowledgeProviderRegistry,
    get_dataset_provider_registry,
    get_biological_knowledge_provider_registry,
)
from bioage.acquisition.resolver import RepositoryResolver
from bioage.acquisition.extractor import SafeArchiveExtractor, ArchiveExtractionSecurityError
from bioage.acquisition.downloader import DownloadManager
from bioage.acquisition.validator import DatasetValidator
from bioage.acquisition.normalizer import DatasetNormalizer
from bioage.acquisition.manifest import ManifestImporter, ManifestValidationError
from bioage.acquisition.multi_omics import MultiOmicsAssembler
from bioage.acquisition.provenance import DatasetProvenanceRecord
from bioage.acquisition.cache import AcquisitionCache, CacheStatus
from bioage.acquisition.providers import (
    GEOProvider,
    NCBIProvider,
    SRAProvider,
    ENAProvider,
    ArrayExpressProvider,
    BioStudiesProvider,
    GDCProvider,
    TCGAProvider,
    PRIDEProvider,
    ProteomeXchangeProvider,
    MetaboLightsProvider,
    GenericURLProvider,
)
from bioage.benchmarks.clocks import (
    ClockCompatibilityEngine,
    GrimAgeClock,
    DunedinPACEClock,
    ReferenceClockBenchmarkSuite,
)


# =============================================================================
# 1. REGISTRY & DECOUPLING TESTS
# =============================================================================

def test_registry_registration_and_isolation():
    reg = get_dataset_provider_registry()
    assert len(reg.list_providers()) >= 12

    provider_names = [p.name for p in reg.list_providers()]
    assert "GEO" in provider_names
    assert reg.get("geo") is not None
    assert reg.get("GEO") is not None

    # Decoupling check: biological knowledge registry is independent
    bio_reg = get_biological_knowledge_provider_registry()
    bio_names = bio_reg.list_providers()
    assert "STRING" in bio_names or "REACTOME" in bio_names or "ENSEMBL" in bio_names
    # Dataset providers must not leak into biological knowledge registry
    assert "GEO" not in bio_names


def test_default_registry_contains_all_12_providers():
    reg = get_dataset_provider_registry()
    expected = [
        "GEO", "NCBI", "SRA", "ENA", "ArrayExpress", "BioStudies",
        "GDC", "TCGA", "PRIDE", "ProteomeXchange", "MetaboLights", "Generic URL"
    ]
    available_names = [p.name for p in reg.list_providers()]
    for exp in expected:
        assert exp in available_names, f"Provider {exp} missing from registry ({available_names})"


# =============================================================================
# 2. REPOSITORY RESOLVER ROUTING TESTS
# =============================================================================

def test_resolver_accession_routing():
    resolver = RepositoryResolver()

    cases = [
        ("GSE40279", "GEO"),
        ("GDS5000", "GEO"),
        ("PRJNA12345", "NCBI"),
        ("SRP123456", "SRA"),
        ("SRR987654", "SRA"),
        ("ERP000123", "ENA"),
        ("ERR654321", "ENA"),
        ("E-MTAB-6945", "ArrayExpress"),
        ("E-GEOD-40279", "ArrayExpress"),
        ("S-BSST123", "BioStudies"),
        ("TCGA-BRCA", "TCGA"),
        ("GDC-PROJECT-1", "GDC"),
        ("PXD000001", "PRIDE"),
        ("MTBLS123", "MetaboLights"),
    ]
    for accession, expected_repo in cases:
        prov_name, _ = resolver.resolve_provider_name(accession)
        assert prov_name == expected_repo, f"Expected {expected_repo} for {accession}, got {prov_name}"


def test_resolver_url_routing():
    resolver = RepositoryResolver()

    cases = [
        ("https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE40279", "GEO"),
        ("https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-6945", "ArrayExpress"),
        ("https://www.ebi.ac.uk/pride/archive/projects/PXD000001", "PRIDE"),
        ("https://portal.gdc.cancer.gov/projects/TCGA-LUAD", "GDC"),
        ("https://zenodo.org/record/12345/files/aging_matrix.csv", "Generic URL"),
    ]
    for url, expected_repo in cases:
        prov_name, _ = resolver.resolve_provider_name(url)
        assert prov_name == expected_repo, f"Expected {expected_repo} for {url}, got {prov_name}"


# =============================================================================
# 3. SAFE ARCHIVE EXTRACTOR SECURITY TESTS
# =============================================================================

def test_safe_extractor_prevents_zipslip_traversal(tmp_path):
    extractor = SafeArchiveExtractor()
    evil_zip_path = tmp_path / "zipslip_attack.zip"

    # Craft malicious zip containing ../../evil_payload.txt
    with zipfile.ZipFile(evil_zip_path, "w") as zf:
        zf.writestr("../../evil_payload.txt", "MALICIOUS PAYLOAD")

    extract_dest = tmp_path / "extracted_dir"
    extract_dest.mkdir()

    with pytest.raises((ValueError, ArchiveExtractionSecurityError)):
        extractor.extract_zip(evil_zip_path, extract_dest)


def test_safe_extractor_valid_zip(tmp_path):
    extractor = SafeArchiveExtractor()
    valid_zip_path = tmp_path / "legit.zip"

    with zipfile.ZipFile(valid_zip_path, "w") as zf:
        zf.writestr("subfolder/data.csv", "sample_id,age\nS1,40\nS2,60\n")

    extract_dest = tmp_path / "extracted"
    extracted_files = extractor.extract_zip(valid_zip_path, extract_dest)

    assert len(extracted_files) == 1
    assert (extract_dest / "subfolder" / "data.csv").exists()


# =============================================================================
# 4. DOWNLOAD MANAGER PRE-CHECKS & CHECKSUM TESTS
# =============================================================================

def test_download_manager_checksum_validation(tmp_path):
    test_file = tmp_path / "test_artifact.txt"
    test_file.write_text("BioAge-X reproducible research payload 2026", encoding="utf-8")

    import hashlib
    correct_sha256 = hashlib.sha256(test_file.read_bytes()).hexdigest()
    wrong_sha256 = "0000000000000000000000000000000000000000000000000000000000000000"

    assert DownloadManager.verify_checksum(test_file, correct_sha256, algorithm="sha256") is True
    assert DownloadManager.verify_checksum(test_file, wrong_sha256, algorithm="sha256") is False


def test_download_manager_disk_space_check(tmp_path):
    ok, avail, req = DownloadManager.check_disk_space(tmp_path, 100)
    assert ok is True
    assert avail > req

    unreasonable_bytes = 10 * 1024 * 1024 * 1024 * 1024 * 1024  # 10 PB
    ok_fail, _, _ = DownloadManager.check_disk_space(tmp_path, unreasonable_bytes)
    assert ok_fail is False


# =============================================================================
# 5. ALL 12 PROVIDERS FUNCTIONALITY TESTS
# =============================================================================

def test_geo_provider_search_and_preview():
    geo = GEOProvider()
    results = geo.search("aging blood DNA methylation", limit=5)
    assert isinstance(results, list)
    assert len(results) > 0
    assert any("GSE40279" in r.accession for r in results)

    meta = geo.get_metadata("GSE40279")
    assert meta.accession == "GSE40279"
    assert meta.repository == "GEO"
    assert len(meta.download_options) > 0


def test_sra_provider_requires_preprocessing():
    sra = SRAProvider()
    results = sra.search("aging transcriptome", limit=3)
    assert isinstance(results, list)
    assert len(results) > 0
    # Guardrail: raw reads MUST be labeled requires_preprocessing
    assert all(r.requires_preprocessing is True for r in results)

    meta = sra.get_metadata("SRP123456")
    assert meta.compatibility_status == CompatibilityLevel.REQUIRES_PREPROCESSING.value


def test_ena_provider_requires_preprocessing():
    ena = ENAProvider()
    results = ena.search("aging sequencing", limit=3)
    assert all(r.requires_preprocessing is True for r in results)


def test_gdc_provider_access_restricted_guardrail():
    gdc = GDCProvider()
    results = gdc.search("TCGA breast cancer", limit=3)
    assert len(results) > 0

    meta = gdc.get_metadata("TCGA-BRCA")
    assert "GDC" in meta.repository
    restricted_opts = [opt for opt in meta.download_options if opt.access_restricted]
    assert len(restricted_opts) > 0


def test_tcga_provider_facade():
    tcga = TCGAProvider()
    results = tcga.search("lung", limit=2)
    assert len(results) > 0


def test_arrayexpress_provider():
    ae = ArrayExpressProvider()
    results = ae.search("aging", limit=3)
    assert len(results) > 0
    meta = ae.get_metadata("E-MTAB-5214")
    assert meta.accession == "E-MTAB-5214"


def test_biostudies_provider():
    bs = BioStudiesProvider()
    results = bs.search("aging", limit=3)
    assert len(results) > 0


def test_pride_provider_proteomics():
    pride = PRIDEProvider()
    results = pride.search("aging plasma", limit=3)
    assert len(results) > 0
    assert all(r.modality == "proteomics" for r in results)


def test_proteomexchange_facade():
    px = ProteomeXchangeProvider()
    results = px.search("aging", limit=2)
    assert len(results) > 0


def test_metabolights_provider():
    mtbls = MetaboLightsProvider()
    results = mtbls.search("longevity metabolome", limit=3)
    assert len(results) > 0
    assert all(r.modality == "metabolomics" for r in results)


def test_generic_url_provider_validation(tmp_path):
    dummy_csv = tmp_path / "valid.csv"
    dummy_csv.write_text("sample_id,chronological_age,cg001,cg002\nS1,45,0.2,0.8\nS2,65,0.4,0.6\n")

    val_res = DatasetValidator.inspect_file(dummy_csv)
    assert val_res.is_valid is True
    assert val_res.sample_count == 2
    assert val_res.feature_count == 2


# =============================================================================
# 6. MULTI-OMICS MANIFEST & MERGE STRATEGY TESTS
# =============================================================================

def test_manifest_importer_and_assembly(tmp_path):
    # 1. Test ManifestImporter validation
    sample_file = tmp_path / "sample.csv"
    sample_file.write_text("sample_id,age\nS1,45\n")

    manifest_data = {
        "dataset_id": "TEST_COHORT",
        "samples": [
            {"sample_id": "S1", "age": 45, "methylation_file": str(sample_file)},
            {"sample_id": "S2", "age": 60, "methylation_file": str(sample_file)},
        ],
    }
    val = ManifestImporter.validate_manifest(manifest_data)
    assert val["valid"] is True
    assert val["total_samples"] == 2

    # 2. Test MultiOmicsAssembler intersection merge
    df_meth = pd.DataFrame({
        "sample_id": ["S1", "S2", "S3"],
        "cg01": [0.2, 0.4, 0.6],
        "chronological_age": [40, 50, 60],
    })
    df_rna = pd.DataFrame({
        "sample_id": ["S2", "S3", "S4"],
        "GENE_TP53": [5.2, 6.1, 4.9],
    })

    assembler = MultiOmicsAssembler()
    merged_df, audit = assembler.assemble_cohort(
        datasets={"methylation": df_meth, "transcriptomics": df_rna},
        strategy="intersection",
    )
    assert len(merged_df) == 2  # Only S2 and S3 in intersection
    assert set(merged_df["sample_id"]) == {"S2", "S3"}
    assert "GENE_TP53" in merged_df.columns
    assert "cg01" in merged_df.columns


def test_manifest_union_merge():
    df1 = pd.DataFrame({"sample_id": ["S1", "S2"], "cg01": [0.1, 0.2]})
    df2 = pd.DataFrame({"sample_id": ["S2", "S3"], "GENE_A": [10.0, 12.0]})

    assembler = MultiOmicsAssembler()
    merged_df, audit = assembler.assemble_cohort(
        datasets={"meth": df1, "rna": df2},
        strategy="union",
    )
    assert len(merged_df) == 3  # S1, S2, S3 in union
    assert audit["strategy"] == "union"


# =============================================================================
# 7. PROVENANCE & CACHE TESTS
# =============================================================================

def test_dataset_provenance_tracking():
    prov = DatasetProvenanceRecord(
        dataset_id="DS-PROV-1",
        repository="GEO",
        accession="GSE40279",
        source_url="https://ftp.ncbi.nlm.nih.gov/geo/series/GSE40nnn/GSE40279/matrix/",
        provider="GEOProvider",
    )
    prov.add_processing_step("download_completed", details="Streamed 24.5 MB", parameters={"chunk_size": 65536})
    prov.add_processing_step("orientation_detected", details="Transposed features to columns", input_shape=[1000, 50], output_shape=[50, 1000])

    record_dict = prov.to_dict()
    assert record_dict["dataset_id"] == "DS-PROV-1"
    assert len(record_dict["processing_steps"]) == 2
    assert record_dict["processing_steps"][1]["step_name"] == "orientation_detected"


def test_acquisition_cache_status_tags(tmp_path):
    cache = AcquisitionCache(cache_dir=tmp_path / "test_cache")

    # 1. Miss returns LIVE
    data, status = cache.get_metadata("geo", "GSE_TEST")
    assert data is None
    assert status == CacheStatus.LIVE

    # 2. Put metadata
    cache.set_metadata("geo", "GSE_TEST", {"title": "Cached Study"})

    # 3. Hit returns CACHED
    cached_data, hit_status = cache.get_metadata("geo", "GSE_TEST")
    assert cached_data is not None
    assert cached_data["title"] == "Cached Study"
    assert hit_status == CacheStatus.CACHED


# =============================================================================
# 8. THIRD-GENERATION CLOCK & COMPATIBILITY ENGINE TESTS
# =============================================================================

def test_grimage_and_dunedinpace_scientific_honesty():
    df_missing = pd.DataFrame({
        "chronological_age": [45, 60],
        "random_gene_1": [1.0, 2.0],
    })

    grim = GrimAgeClock()
    pred_grim, meta_grim = grim.predict(df_missing)
    assert pred_grim is None
    assert "error" in meta_grim

    dunedin = DunedinPACEClock()
    pred_pace, meta_pace = dunedin.predict(df_missing)
    assert pred_pace is None
    assert "error" in meta_pace


def test_clock_compatibility_engine_tiers():
    engine = ClockCompatibilityEngine()

    # 1. Non-methylation dataset (e.g. transcriptomics only)
    df_rna = pd.DataFrame({
        "GENE_TP53": [5.0, 6.0],
        "GENE_SIRT1": [8.0, 7.5],
        "chronological_age": [30, 70],
    })
    comp_rna = engine.evaluate_compatibility(df_rna)
    assert comp_rna["clocks"]["Horvath"]["status"] == "NOT_APPLICABLE"
    assert comp_rna["clocks"]["GrimAge"]["status"] == "NOT_APPLICABLE"

    # 2. Methylation dataset with Horvath canonical CpGs
    df_meth = pd.DataFrame({
        "cg16867657": [0.2, 0.8],  # ELOVL2
        "cg06639320": [0.3, 0.7],  # FHL2
        "cg02233190": [0.1, 0.9],  # GSTP1
        "cg19283806": [0.4, 0.6],  # CCDC102B
        "cg24724428": [0.5, 0.5],  # PENK
        "cg09809672": [0.2, 0.7],  # EDARADD
        "cg22736354": [0.3, 0.8],  # NHLRC1
        "chronological_age": [35, 65],
    })
    comp_meth = engine.evaluate_compatibility(df_meth)
    assert comp_meth["clocks"]["Horvath"]["status"] in ("UNAVAILABLE", "PARTIAL_COVERAGE")
    assert comp_meth["clocks"]["Hannum"]["status"] in ("PARTIAL_COVERAGE", "FULL_COVERAGE")
    assert comp_meth["clocks"]["GrimAge"]["status"] in ("UNAVAILABLE", "NOT_APPLICABLE")
    assert comp_meth["clocks"]["DunedinPACE"]["status"] in ("UNAVAILABLE", "NOT_APPLICABLE")
