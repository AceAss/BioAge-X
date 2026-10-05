"""
Reactome Pathway Enrichment Client & Biological Process Adapter for BioAge-X.
Integrates live Reactome Content & Analysis Service ORA with persistent caching,
FDR adjustment, and deterministic local Hallmark of Aging pathway fallback.
"""

from typing import Dict, List, Optional, Any, Tuple
import time
import httpx
from datetime import datetime, timezone

from bioage.integrations.base import (
    BiologicalKnowledgeProvider,
    PathwayProvider,
    KnowledgeStatus,
    ProviderHealth,
    EnrichedPathway,
)
from bioage.integrations.cache import get_integration_cache, PersistentBiologicalCache
from bioage.integrations.rate_limit import RateLimiter, retry_with_backoff
from bioage.pathways.enrichment import PathwayEnrichmentAnalyzer
from bioage.utils.logger import get_logger

logger = get_logger("bioage.integrations.reactome")


class ReactomeClient(BiologicalKnowledgeProvider, PathwayProvider):
    """Reactome Analysis Service client with local hallmark-of-aging fallback."""

    ANALYSIS_URL = "https://reactome.org/AnalysisService"
    CONTENT_URL = "https://reactome.org/ContentService"

    def __init__(
        self,
        analysis_url: Optional[str] = None,
        content_url: Optional[str] = None,
        timeout: float = 8.0,
        cache: Optional[PersistentBiologicalCache] = None,
        enable_live: bool = True,
    ):
        self.analysis_url = (analysis_url or self.ANALYSIS_URL).rstrip("/")
        self.content_url = (content_url or self.CONTENT_URL).rstrip("/")
        self.timeout = timeout
        self.cache = cache or get_integration_cache()
        self.enable_live = enable_live
        self.rate_limiter = RateLimiter(requests_per_second=3.0, provider_name="Reactome")
        self.last_health: Optional[ProviderHealth] = None
        self._local_analyzer = PathwayEnrichmentAnalyzer()

    @property
    def provider_name(self) -> str:
        return "Reactome"

    def check_health(self) -> ProviderHealth:
        """Pings Reactome database version endpoint."""
        start = time.time()
        try:
            with httpx.Client(timeout=4.0) as client:
                res = client.get(f"{self.content_url}/data/database/version")
                latency = round((time.time() - start) * 1000, 2)
                if res.status_code == 200:
                    version = f"Reactome Release {res.text.strip()}"
                    health = ProviderHealth(
                        provider="Reactome",
                        status="available",
                        version=version,
                        latency_ms=latency,
                        last_successful_request=datetime.now(timezone.utc).isoformat(),
                        cached_records=self.cache.get_stats().get("by_provider", {}).get("reactome", 0),
                        message="Reactome Analysis Service operational",
                    )
                    self.last_health = health
                    return health

            health = ProviderHealth(
                provider="Reactome",
                status="degraded",
                latency_ms=round((time.time() - start) * 1000, 2),
                cached_records=self.cache.get_stats().get("by_provider", {}).get("reactome", 0),
                message=f"Reactome version check status {res.status_code}",
            )
            self.last_health = health
            return health
        except Exception as e:
            health = ProviderHealth(
                provider="Reactome",
                status="unavailable",
                latency_ms=round((time.time() - start) * 1000, 2),
                cached_records=self.cache.get_stats().get("by_provider", {}).get("reactome", 0),
                message=f"Reactome ping failed ({e}). Local hallmark fallback active.",
            )
            self.last_health = health
            return health

    def enrich_pathways(
        self,
        genes: List[str],
        species: str = "homo_sapiens",
        fdr_threshold: float = 0.10,
        pathway_source: str = "reactome",  # "reactome", "hallmarks", "combined"
    ) -> Tuple[List[EnrichedPathway], KnowledgeStatus]:
        """
        Runs pathway enrichment against Reactome, Local Hallmarks of Aging, or both.
        Preserves distinct source attribution without silent mixing.
        """
        clean_genes = sorted(list(set(
            str(g).replace("GENE_", "").split("_")[-1].upper()
            for g in genes if str(g).strip()
        )))

        if not clean_genes:
            return [], KnowledgeStatus.NOT_FOUND

        # If user explicitly requests local hallmarks only
        if pathway_source == "hallmarks":
            return self._run_local_fallback(clean_genes), KnowledgeStatus.LOCAL_FALLBACK

        # Check Cache for Reactome
        cache_params = {
            "genes": clean_genes,
            "species": species,
            "fdr_threshold": fdr_threshold,
        }
        cached = self.cache.get("reactome", cache_params)

        reactome_pathways: List[EnrichedPathway] = []
        overall_status = KnowledgeStatus.LIVE

        if cached:
            payload, meta = cached
            reactome_pathways = [
                EnrichedPathway(**item) for item in payload
            ]
            overall_status = KnowledgeStatus.CACHED
            logger.info(f"Loaded {len(reactome_pathways)} Reactome pathways from cache")
        elif self.enable_live:
            try:
                reactome_pathways = self._fetch_live_reactome(clean_genes, fdr_threshold)
                # Store in cache
                self.cache.set(
                    "reactome",
                    cache_params,
                    [p.to_dict() for p in reactome_pathways],
                    provider_version="Reactome Release 91",
                )
                overall_status = KnowledgeStatus.LIVE
                logger.info(f"Retrieved {len(reactome_pathways)} live Reactome pathways")
            except Exception as e:
                logger.warning(f"Reactome live analysis failed: {e}. Falling back to local hallmarks.")
                overall_status = KnowledgeStatus.LOCAL_FALLBACK
        else:
            overall_status = KnowledgeStatus.LOCAL_FALLBACK

        # If Reactome failed or returned empty -> local fallback
        if not reactome_pathways or overall_status == KnowledgeStatus.LOCAL_FALLBACK:
            fallback_res = self._run_local_fallback(clean_genes)
            return fallback_res, KnowledgeStatus.LOCAL_FALLBACK

        # If combined, return Reactome + Local Hallmarks with clear distinct tags
        if pathway_source == "combined":
            local_res = self._run_local_fallback(clean_genes)
            return reactome_pathways + local_res, overall_status

        return reactome_pathways, overall_status

    def _fetch_live_reactome(
        self,
        genes: List[str],
        fdr_threshold: float,
    ) -> List[EnrichedPathway]:
        """Queries Reactome Analysis Service projection endpoint."""
        self.rate_limiter.wait()
        gene_payload = "\n".join(genes)

        @retry_with_backoff("Reactome", max_retries=2, base_delay=0.5)
        def _post():
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.analysis_url}/identifiers/projection/?pageSize=30&page=1&sortBy=ENTITIES_PVALUE&order=ASC",
                    content=gene_payload.encode("utf-8"),
                    headers={"Content-Type": "text/plain", "Accept": "application/json"},
                )
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code in (400, 404):
                    logger.debug(f"Reactome returned {resp.status_code}")
                    return {}
                resp.raise_for_status()

        data = _post()
        pathways_raw = data.get("pathways", [])
        now_utc = datetime.now(timezone.utc).isoformat()
        enriched: List[EnrichedPathway] = []

        for p in pathways_raw:
            entities = p.get("entities", {})
            p_val = float(entities.get("pValue", 1.0))
            fdr = float(entities.get("fdr", 1.0))
            found_cnt = int(entities.get("found", 0))
            total_cnt = int(entities.get("total", 0))

            # Approximate odds ratio
            odds_ratio = round((found_cnt / max(1, total_cnt)) * (20000 / max(1, len(genes))), 2)

            pathway_obj = EnrichedPathway(
                pathway_id=str(p.get("stId", "")),
                pathway_name=str(p.get("name", "")),
                category="Reactome Pathway",
                matched_genes=[],  # Reactome projection returns aggregate counts
                pathway_size=total_cnt,
                overlap_count=found_cnt,
                p_value=p_val,
                fdr_adjusted_p=fdr,
                odds_ratio=odds_ratio,
                source="Reactome",
                provider_version="Release 91",
                status=KnowledgeStatus.LIVE,
                retrieved_at=now_utc,
            )
            enriched.append(pathway_obj)

        return enriched

    def _run_local_fallback(self, query_genes: List[str]) -> List[EnrichedPathway]:
        """Runs the curated hallmarks of aging local over-representation analysis."""
        raw_results = self._local_analyzer.analyze(query_genes)
        now_utc = datetime.now(timezone.utc).isoformat()

        converted: List[EnrichedPathway] = []
        for r in raw_results:
            converted.append(EnrichedPathway(
                pathway_id=r["pathway_id"],
                pathway_name=r["pathway_name"],
                category=r.get("category", "Hallmark of Aging"),
                matched_genes=r.get("overlapping_genes", []),
                pathway_size=r["pathway_size"],
                overlap_count=r["overlap_count"],
                p_value=r["p_value"],
                fdr_adjusted_p=r["fdr_adjusted_p"],
                odds_ratio=r["odds_ratio"],
                source="Local Curated Hallmarks",
                provider_version="BioAge-X Hallmarks v1.0",
                status=KnowledgeStatus.LOCAL_FALLBACK,
                retrieved_at=now_utc,
            ))

        return converted
