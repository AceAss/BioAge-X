"""
External Biological Knowledge Integrations Router for BioAge-X REST API.
Exposes endpoints for provider health checks, identifier resolution (Ensembl),
PPI networks (STRING), pathway enrichment (Reactome), public dataset discovery (NCBI/GEO),
and biological provenance tracking.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import json
import uuid
from datetime import datetime, timezone

from apps.api.core.config import settings
from apps.api.core.database import get_db
from apps.api.models.db_models import DatasetRecord
from apps.api.schemas.api_schemas import (
    ResolveGenesRequest,
    ResolveGenesResponse,
    StringNetworkRequest,
    ReactomePathwaysRequest,
    EnsemblAnnotateRequest,
    GeoImportRequest,
    IntegrationsHealthResponse,
)
from bioage.integrations.ensembl_client import EnsemblClient
from bioage.integrations.string_client import STRINGClient
from bioage.integrations.reactome_client import ReactomeClient
from bioage.integrations.ncbi_client import NCBIClient
from bioage.integrations.geo_client import GEOClient
from bioage.integrations.resolver import UnifiedIdentifierResolver
from bioage.integrations.cache import get_integration_cache
from bioage.integrations.provenance import get_provenance_tracker
from bioage.ai.gemini_client import GeminiAssistantClient
from bioage.utils.logger import get_logger

logger = get_logger("apps.api.routers.integrations")
router = APIRouter(prefix="/integrations", tags=["External Biological Knowledge"])


@router.get("/health", response_model=IntegrationsHealthResponse)
def get_integrations_health():
    """
    Checks operational connectivity and versions for STRING, Reactome, Ensembl, NCBI/GEO, and Gemini.
    Distinguishes: AVAILABLE_NO_KEY, AVAILABLE_WITH_KEY, DEGRADED, UNAVAILABLE, AUTH_REQUIRED, DISABLED.
    Returns status without crashing or blocking startup if any provider is unavailable.
    """
    ensembl = EnsemblClient().check_health()
    string = STRINGClient().check_health()
    reactome = ReactomeClient().check_health()
    ncbi = NCBIClient().check_health()
    gemini = GeminiAssistantClient(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_MODEL,
        enabled=settings.GEMINI_ENABLED,
    ).check_health()
    cache_stats = get_integration_cache().get_stats()

    string_status = "AVAILABLE_NO_KEY" if string.status in ("available", "AVAILABLE_NO_KEY") else string.status.upper()
    reactome_status = "AVAILABLE_NO_KEY" if reactome.status in ("available", "AVAILABLE_NO_KEY") else reactome.status.upper()
    ensembl_status = "AVAILABLE_NO_KEY" if ensembl.status in ("available", "AVAILABLE_NO_KEY") else ensembl.status.upper()
    ncbi_status = (
        ("AVAILABLE_WITH_KEY" if settings.NCBI_API_KEY else "AVAILABLE_NO_KEY")
        if ncbi.status in ("available", "AVAILABLE_NO_KEY", "AVAILABLE_WITH_KEY")
        else ncbi.status.upper()
    )
    gemini_status = gemini.status.upper()

    return IntegrationsHealthResponse(
        string=string_status,
        reactome=reactome_status,
        ensembl=ensembl_status,
        ncbi=ncbi_status,
        gemini=gemini_status,
        details={
            "ensembl": ensembl.to_dict(),
            "string": string.to_dict(),
            "reactome": reactome.to_dict(),
            "ncbi": ncbi.to_dict(),
            "gemini": gemini.to_dict(),
        },
        cache=cache_stats,
    )


@router.post("/genes/resolve", response_model=ResolveGenesResponse)
def resolve_identifiers(request: ResolveGenesRequest):
    """
    Resolves a batch of heterogeneous feature identifiers (CpGs, Ensembl IDs, Gene Symbols, Covariates).
    Identifies ambiguities without fabrication, preserves provenance, and provides canonical mappings.
    """
    resolver = UnifiedIdentifierResolver()
    resolved = resolver.resolve_batch(request.identifiers, species=request.species)

    ambiguous_cnt = sum(1 for r in resolved if r.status.value == "AMBIGUOUS" or str(r.status) == "AMBIGUOUS")
    status_counts = {}
    for r in resolved:
        st = r.status.value if hasattr(r.status, "value") else str(r.status)
        status_counts[st] = status_counts.get(st, 0) + 1

    return ResolveGenesResponse(
        resolved=[r.to_dict() for r in resolved],
        total_count=len(resolved),
        ambiguous_count=ambiguous_cnt,
        provenance_summary={
            "status_distribution": status_counts,
            "provider": "Ensembl + Local Feature Annotation",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        },
    )


@router.post("/string/network")
def get_string_network(request: StringNetworkRequest):
    """
    Retrieves protein-protein interaction network from STRING DB or local interactome.
    Supports network_source: 'hybrid', 'string', 'local'.
    """
    client = STRINGClient()
    edges, status = client.get_interactions(
        genes=request.genes,
        min_score=request.min_score,
        species=request.species,
        network_source=request.network_source,
    )

    edge_dicts = [e.to_dict() for e in edges]
    source_counts = {}
    for e in edge_dicts:
        p = e.get("provider", "Unknown")
        source_counts[p] = source_counts.get(p, 0) + 1

    return {
        "status": status.value if hasattr(status, "value") else str(status),
        "network_source": request.network_source,
        "total_edges": len(edge_dicts),
        "source_breakdown": source_counts,
        "edges": edge_dicts,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/reactome/pathways")
def enrich_reactome_pathways(request: ReactomePathwaysRequest):
    """
    Runs pathway over-representation analysis via Reactome Analysis Service or Hallmark database.
    Supports pathway_source: 'reactome', 'hallmarks', 'combined'.
    """
    client = ReactomeClient()
    enriched, status = client.enrich_pathways(
        genes=request.genes,
        species=request.species,
        fdr_threshold=request.fdr_threshold,
        pathway_source=request.pathway_source,
    )

    return {
        "status": status.value if hasattr(status, "value") else str(status),
        "pathway_source": request.pathway_source,
        "pathway_count": len(enriched),
        "pathways": [p.to_dict() for p in enriched],
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/ensembl/annotate")
def annotate_ensembl_symbols(request: EnsemblAnnotateRequest):
    """
    Retrieves canonical Ensembl gene models, chromosomes, and coordinates for symbols.
    """
    client = EnsemblClient()
    results = client.resolve_batch(request.symbols, species=request.species)
    return {
        "total": len(results),
        "annotations": [r.to_dict() for r in results],
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/geo/search")
def search_geo_datasets(
    query: str = Query(default="human aging blood methylation"),
    max_results: int = Query(default=10, ge=1, le=25),
):
    """
    Searches NCBI GEO for relevant public functional genomics datasets (aging, methylation, RNA-seq).
    Pre-filters and returns metadata without performing arbitrary massive file downloads.
    """
    client = GEOClient()
    results = client.search_datasets(query=query, max_results=max_results)
    return {
        "query": query,
        "count": len(results),
        "datasets": [r.to_dict() for r in results],
    }


@router.get("/geo/{accession}")
def get_geo_dataset_metadata(accession: str):
    """
    Retrieves study metadata, sample count, platform, and compatibility rating for a GEO accession.
    """
    client = GEOClient()
    meta = client.get_dataset_metadata(accession=accession)
    if not meta:
        raise HTTPException(status_code=404, detail=f"GEO accession '{accession}' not found in catalog or NCBI index")
    return meta.to_dict()


@router.post("/geo/import")
def import_geo_dataset(request: GeoImportRequest, db: Session = Depends(get_db)):
    """
    Safely imports a verified public dataset into BioAge-X without risky unverified script executions.
    For landmark benchmarks (e.g. GSE40279 Hannum blood), activates the local verified benchmark cohort.
    """
    accession = request.accession.strip().upper()
    client = GEOClient()
    meta = client.get_dataset_metadata(accession)

    if not meta:
        raise HTTPException(status_code=404, detail=f"Dataset {accession} not found")

    if "Not Compatible" in meta.compatibility_status:
        raise HTTPException(
            status_code=400,
            detail=f"Dataset {accession} is not compatible with the BioAge-X workflow: {meta.compatibility_status}"
        )

    # Check if curated benchmark cohort exists locally
    benchmark_file = settings.PROJECT_ROOT / "data" / "public" / "GSE40279_Hannum_Blood_Benchmark.csv"
    if accession == "GSE40279" and benchmark_file.exists():
        dataset_id = f"ds_geo_{accession.lower()}"
        existing = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
        if existing:
            return {
                "message": f"Dataset {accession} is already imported and available for analysis.",
                "dataset_id": existing.id,
                "name": existing.name,
                "n_samples": existing.n_samples,
                "n_features": existing.n_features,
            }

        import pandas as pd
        df = pd.read_csv(benchmark_file, index_col=0)
        record = DatasetRecord(
            id=dataset_id,
            name=f"GSE40279 Hannum Blood Epigenetic Benchmark ({meta.sample_count} samples)",
            file_path=str(benchmark_file),
            format="csv",
            n_samples=len(df),
            n_features=len(df.columns) - 1,
            orientation="samples_by_features",
            missing_fraction=0.0,
            age_column="age",
            detected_modality="methylation",
            profile_json=json.dumps({
                "source": "NCBI GEO GSE40279",
                "organism": "Homo sapiens",
                "tissue": "Whole Blood",
                "platform": "Illumina HumanMethylation450",
                "verified": True,
            }),
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return {
            "message": f"Successfully imported verified public benchmark {accession}.",
            "dataset_id": record.id,
            "name": record.name,
            "n_samples": record.n_samples,
            "n_features": record.n_features,
            "compatibility": meta.compatibility_status,
        }

    # If general public dataset
    return {
        "message": f"Dataset {accession} metadata verified. For custom large GEO matrices, place the preprocessed CSV in data/raw/ to register.",
        "accession": accession,
        "title": meta.title,
        "sample_count": meta.sample_count,
        "compatibility": meta.compatibility_status,
        "external_url": meta.external_url,
    }


@router.get("/provenance/{experiment_id}")
def get_experiment_provenance(experiment_id: str):
    """
    Retrieves full biological knowledge provenance record for an experiment,
    documenting all live, cached, and local fallback queries.
    """
    tracker = get_provenance_tracker()
    summary = tracker.get_summary(experiment_id)
    return summary


@router.get("/cache/stats")
def get_cache_stats():
    """Returns persistent cache metrics (record counts per provider, hit/miss ratios)."""
    return get_integration_cache().get_stats()


@router.post("/cache/clear")
def clear_cache(provider: Optional[str] = None):
    """Invalidates cached biological records for a specific provider or all providers."""
    cache = get_integration_cache()
    cleared = cache.invalidate(provider=provider)
    return {"message": f"Cleared {cleared} cache records", "provider": provider or "all"}
