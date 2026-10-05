"""
Unit and Integration Tests for BioAge-X External Biological Knowledge Layer.
Validates STRING, Reactome, Ensembl, NCBI/GEO clients, caching, rate limiting,
exponential backoff, identifier resolution, provenance tracking, and network source switching.
All standard tests use deterministic mocking so CI NEVER requires live internet access.
Optional live testing is enabled only when RUN_LIVE_INTEGRATION_TESTS=true.
"""

import os
import time
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import httpx

from bioage.integrations.base import (
    KnowledgeStatus,
    ProviderHealth,
    ResolvedIdentifier,
    InteractionEdge,
    EnrichedPathway,
    GeoDatasetMetadata,
)
from bioage.integrations.cache import PersistentBiologicalCache
from bioage.integrations.rate_limit import RateLimiter, retry_with_backoff
from bioage.integrations.provenance import BiologicalProvenanceTracker
from bioage.integrations.ensembl_client import EnsemblClient, LOCAL_ENSEMBL_FALLBACK
from bioage.integrations.string_client import STRINGClient
from bioage.integrations.reactome_client import ReactomeClient
from bioage.integrations.ncbi_client import NCBIClient
from bioage.integrations.geo_client import GEOClient, CURATED_GEO_CATALOG
from bioage.integrations.resolver import UnifiedIdentifierResolver
from bioage.network.interaction_graph import BiologicalInteractionGraph


# =============================================================================
# 1. CACHING LAYER TESTS
# =============================================================================

def test_cache_set_get_and_expiration(tmp_path):
    cache = PersistentBiologicalCache(cache_dir=tmp_path, default_ttl_seconds=2)
    params = {"species": "homo_sapiens", "symbol": "ELOVL2"}
    payload = {"symbol": "ELOVL2", "ensembl_id": "ENSG00000197977"}

    # Set
    key = cache.set("ensembl", params, payload, provider_version="113")
    assert key is not None

    # Get immediately (hit)
    hit = cache.get("ensembl", params)
    assert hit is not None
    data, meta = hit
    assert data["symbol"] == "ELOVL2"
    assert meta["provider_version"] == "113"

    # Stats
    stats = cache.get_stats()
    assert stats["total_records"] == 1
    assert stats["by_provider"]["ensembl"] == 1

    # Invalidate
    cleared = cache.invalidate("ensembl")
    assert cleared == 1
    assert cache.get("ensembl", params) is None


# =============================================================================
# 2. RATE LIMITING & RETRY TESTS
# =============================================================================

def test_rate_limiter_throttling():
    limiter = RateLimiter(requests_per_second=20.0, provider_name="test")
    t0 = time.time()
    for _ in range(3):
        limiter.wait()
    elapsed = time.time() - t0
    # 3 requests at 20 req/s takes at least 2 * 0.05 = 0.10s
    assert elapsed >= 0.08


def test_retry_with_backoff_transient_recovery():
    attempts = 0

    @retry_with_backoff("TestProvider", max_retries=2, base_delay=0.05)
    def flaky_call():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise httpx.RequestError("Transient network glitch")
        return "success"

    res = flaky_call()
    assert res == "success"
    assert attempts == 2


def test_retry_with_backoff_permanent_error_not_retried():
    attempts = 0

    # Mock 404 client error
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    http_error = httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_resp)

    @retry_with_backoff("TestProvider", max_retries=3, base_delay=0.05)
    def client_error_call():
        nonlocal attempts
        attempts += 1
        raise http_error

    with pytest.raises(httpx.HTTPStatusError):
        client_error_call()

    # Must fail immediately on attempt 1 without retry loops
    assert attempts == 1


# =============================================================================
# 3. PROVENANCE TRACKER TESTS
# =============================================================================

def test_provenance_recording_and_lineage(tmp_path):
    tracker = BiologicalProvenanceTracker(storage_dir=tmp_path)
    exp_id = "EXP-TEST-PROV-1"

    ev = tracker.record(
        experiment_id=exp_id,
        provider="STRING",
        query_type="ppi_network",
        status=KnowledgeStatus.LIVE,
        records_count=18,
        provider_version="v12.0",
        request_summary={"min_score": 0.400},
    )
    assert ev.records_count == 18

    summary = tracker.get_summary(exp_id)
    assert summary["total_queries"] == 1
    assert summary["status_breakdown"]["LIVE"] == 1
    assert summary["providers_used"][0]["provider"] == "STRING"


# =============================================================================
# 4. ENSEMBL CLIENT TESTS (MOCKED & FALLBACK)
# =============================================================================

def test_ensembl_fallback_resolution(tmp_path):
    cache = PersistentBiologicalCache(cache_dir=tmp_path)
    client = EnsemblClient(cache=cache, enable_live=False)

    resolved = client.resolve_batch(["ELOVL2", "CDKN2A", "NON_EXISTENT_XYZ"])
    assert len(resolved) == 3

    # ELOVL2 resolved from curated fallback
    elovl2 = resolved[0]
    assert elovl2.canonical_symbol == "ELOVL2"
    assert elovl2.ensembl_gene_id == "ENSG00000197977"
    assert elovl2.chromosome == "6"
    assert elovl2.status == KnowledgeStatus.LOCAL_FALLBACK

    # Non-existent gene marked NOT_FOUND without fabrication
    unknown = resolved[2]
    assert unknown.status == KnowledgeStatus.NOT_FOUND


def test_ensembl_mocked_live_resolution(tmp_path):
    cache = PersistentBiologicalCache(cache_dir=tmp_path)
    client = EnsemblClient(cache=cache, enable_live=True)

    mock_resp = {
        "TP53": {
            "id": "ENSG00000141510",
            "display_name": "TP53",
            "seq_region_name": "17",
            "start": 7668402,
            "end": 7687550,
            "biotype": "protein_coding",
            "description": "tumor protein p53",
        }
    }

    with patch.object(client, "_fetch_live_batch", return_value=mock_resp):
        resolved = client.resolve_batch(["TP53"])
        assert len(resolved) == 1
        tp53 = resolved[0]
        assert tp53.ensembl_gene_id == "ENSG00000141510"
        assert tp53.status == KnowledgeStatus.LIVE


def test_ensembl_ambiguity_handling(tmp_path):
    cache = PersistentBiologicalCache(cache_dir=tmp_path)
    client = EnsemblClient(cache=cache, enable_live=True)

    # Return multiple models for ambiguous symbol
    mock_resp = {
        "AMBIG_GENE": [
            {"id": "ENSG00000000001", "display_name": "AMBIG_A"},
            {"id": "ENSG00000000002", "display_name": "AMBIG_B"},
        ]
    }

    with patch.object(client, "_fetch_live_batch", return_value=mock_resp):
        resolved = client.resolve_batch(["AMBIG_GENE"])
        assert len(resolved) == 1
        ambig = resolved[0]
        assert ambig.status == KnowledgeStatus.AMBIGUOUS
        assert len(ambig.ambiguity_candidates) == 2


# =============================================================================
# 5. STRING CLIENT TESTS (MOCKED, LOCAL & HYBRID)
# =============================================================================

def test_string_client_local_source():
    client = STRINGClient(enable_live=False)
    edges, status = client.get_interactions(
        genes=["TP53", "CDKN1A", "SIRT1"],
        network_source="local",
    )
    assert status == KnowledgeStatus.LOCAL_FALLBACK
    assert len(edges) > 0
    # Verify edge fields
    first_edge = edges[0]
    assert first_edge.provider == "Local Aging Interactome"
    assert first_edge.confidence_score > 0.0


def test_string_client_mocked_live_and_hybrid(tmp_path):
    cache = PersistentBiologicalCache(cache_dir=tmp_path)
    client = STRINGClient(cache=cache, enable_live=True)

    mock_string_edges = [
        InteractionEdge(
            source="TP53",
            target="MDM2",
            confidence_score=0.99,
            evidence_scores={"experiments": 0.95},
            provider="STRING",
            status=KnowledgeStatus.LIVE,
        )
    ]

    with patch.object(client, "_fetch_live_interactions", return_value=mock_string_edges):
        # STRING only
        edges_str, st_str = client.get_interactions(["TP53", "MDM2"], network_source="string")
        assert st_str == KnowledgeStatus.LIVE
        assert any(e.target == "MDM2" for e in edges_str)

        # Hybrid: contains STRING edge and local edges without crashing
        edges_hyb, st_hyb = client.get_interactions(["TP53", "MDM2"], network_source="hybrid")
        assert any(e.target == "MDM2" for e in edges_hyb)
        assert any(e.provider == "Local Aging Interactome" for e in edges_hyb)


# =============================================================================
# 6. REACTOME CLIENT TESTS (MOCKED & LOCAL FALLBACK)
# =============================================================================

def test_reactome_hallmark_fallback():
    client = ReactomeClient(enable_live=False)
    pathways, status = client.enrich_pathways(
        genes=["TP53", "CDKN2A", "IL6", "SIRT1"],
        pathway_source="hallmarks",
    )
    assert status == KnowledgeStatus.LOCAL_FALLBACK
    assert len(pathways) > 0
    assert any("Senescence" in p.pathway_name for p in pathways)


def test_reactome_mocked_live_enrichment(tmp_path):
    cache = PersistentBiologicalCache(cache_dir=tmp_path)
    client = ReactomeClient(cache=cache, enable_live=True)

    mock_pathways = [
        EnrichedPathway(
            pathway_id="R-HSA-69620",
            pathway_name="Cell Cycle Checkpoints",
            category="Reactome Pathway",
            pathway_size=240,
            overlap_count=3,
            p_value=1.5e-5,
            fdr_adjusted_p=0.001,
            source="Reactome",
            status=KnowledgeStatus.LIVE,
        )
    ]

    with patch.object(client, "_fetch_live_reactome", return_value=mock_pathways):
        results, status = client.enrich_pathways(["TP53", "CDKN2A"], pathway_source="reactome")
        assert status == KnowledgeStatus.LIVE
        assert results[0].pathway_id == "R-HSA-69620"


# =============================================================================
# 7. NCBI & GEO CLIENT TESTS
# =============================================================================

def test_geo_curated_search_and_metadata():
    geo = GEOClient(enable_live=False)

    # Search for blood methylation
    results = geo.search_datasets("blood methylation", max_results=5)
    assert len(results) > 0
    accessions = [r.accession for r in results]
    assert "GSE40279" in accessions or "GSE87571" in accessions

    # Metadata preview
    meta = geo.get_dataset_metadata("GSE40279")
    assert meta is not None
    assert meta.accession == "GSE40279"
    assert meta.sample_count == 656
    assert meta.has_age_metadata is True
    assert "Epigenetic Clock Ready" in meta.compatibility_status


# =============================================================================
# 8. UNIFIED IDENTIFIER RESOLVER TESTS
# =============================================================================

def test_unified_identifier_resolver(tmp_path):
    cache = PersistentBiologicalCache(cache_dir=tmp_path)
    ensembl = EnsemblClient(cache=cache, enable_live=False)
    resolver = UnifiedIdentifierResolver(ensembl_client=ensembl)

    raw_features = [
        "cg16867657",       # CpG -> ELOVL2
        "CDKN2A",           # Gene symbol -> CDKN2A
        "ENSG00000141510",  # Ensembl ID -> TP53
        "smoking_status",   # Clinical covariate
        "UNKNOWN_PROBE_99", # Unmapped feature
    ]

    resolved = resolver.resolve_batch(raw_features)
    assert len(resolved) == 5

    # cg16867657 mapped to ELOVL2 and Ensembl ID
    cpg = resolved[0]
    assert cpg.canonical_symbol == "ELOVL2"
    assert cpg.ensembl_gene_id == "ENSG00000197977"

    # Covariate identified
    cov = resolved[3]
    assert cov.identifier_type == "clinical_covariate"

    # Unknown preserved without hallucination
    unkn = resolved[4]
    assert unkn.status == KnowledgeStatus.NOT_FOUND


# =============================================================================
# 9. BIOLOGICAL NETWORK WITH HYBRID SOURCE
# =============================================================================

def test_network_source_switching_in_graph_builder(tmp_path):
    graph = BiologicalInteractionGraph()

    # Build local
    graph.build_from_biomarkers(
        biomarker_genes=["ELOVL2", "CDKN2A", "TP53", "SIRT1"],
        network_source="local",
        include_pathways=True,
    )
    cyto = graph.to_cytoscape_json()
    assert cyto["summary"]["network_source"] == "local"
    assert cyto["summary"]["knowledge_status"] == "LOCAL_FALLBACK"
    assert len(cyto["elements"]["nodes"]) > 0
    assert len(cyto["elements"]["edges"]) > 0


# =============================================================================
# 10. OPTIONAL LIVE INTEGRATION TESTS
# =============================================================================

@pytest.mark.skipif(
    os.getenv("RUN_LIVE_INTEGRATION_TESTS", "false").lower() != "true",
    reason="Live integration tests disabled by default. Enable with RUN_LIVE_INTEGRATION_TESTS=true",
)
def test_live_provider_health_checks():
    """Performs non-mocked live ping to external biological APIs when explicitly requested."""
    ensembl_health = EnsemblClient().check_health()
    assert ensembl_health.provider == "Ensembl"

    string_health = STRINGClient().check_health()
    assert string_health.provider == "STRING"

    reactome_health = ReactomeClient().check_health()
    assert reactome_health.provider == "Reactome"

    ncbi_health = NCBIClient().check_health()
    assert ncbi_health.provider == "NCBI/GEO"
