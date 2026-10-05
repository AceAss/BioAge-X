"""
STRING Database API Client & Molecular Interaction Adapter for BioAge-X.
Retrieves protein-protein interaction networks, confidence scores, and evidence channels
(experiments, database, coexpression, textmining) with caching and local fallback.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import time
import httpx
import pandas as pd
from datetime import datetime, timezone

from bioage.integrations.base import (
    BiologicalKnowledgeProvider,
    InteractionProvider,
    KnowledgeStatus,
    ProviderHealth,
    InteractionEdge,
)
from bioage.integrations.cache import get_integration_cache, PersistentBiologicalCache
from bioage.integrations.rate_limit import RateLimiter, retry_with_backoff
from bioage.utils.logger import get_logger

logger = get_logger("bioage.integrations.string")

DEFAULT_EDGE_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "example" / "aging_network_edges.csv"


class STRINGClient(BiologicalKnowledgeProvider, InteractionProvider):
    """Client for STRING DB PPI retrieval with hybrid and fallback support."""

    BASE_URL = "https://string-db.org/api/json"

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 8.0,
        cache: Optional[PersistentBiologicalCache] = None,
        enable_live: bool = True,
        edge_file_path: Optional[Path] = None,
    ):
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.timeout = timeout
        self.cache = cache or get_integration_cache()
        self.enable_live = enable_live
        self.edge_file_path = edge_file_path or DEFAULT_EDGE_FILE
        self.rate_limiter = RateLimiter(requests_per_second=2.5, provider_name="STRING")
        self.last_health: Optional[ProviderHealth] = None

    @property
    def provider_name(self) -> str:
        return "STRING"

    def check_health(self) -> ProviderHealth:
        """Checks STRING API status and database version."""
        start = time.time()
        try:
            with httpx.Client(timeout=4.0) as client:
                res = client.get(f"{self.base_url}/version")
                latency = round((time.time() - start) * 1000, 2)
                if res.status_code == 200:
                    data = res.json()
                    version = "v12.0"
                    if isinstance(data, list) and data:
                        version = data[0].get("string_version", "v12.0")

                    health = ProviderHealth(
                        provider="STRING",
                        status="available",
                        version=f"STRING DB {version}",
                        latency_ms=latency,
                        last_successful_request=datetime.now(timezone.utc).isoformat(),
                        cached_records=self.cache.get_stats().get("by_provider", {}).get("string", 0),
                        message="STRING API operational",
                    )
                    self.last_health = health
                    return health

            health = ProviderHealth(
                provider="STRING",
                status="degraded",
                latency_ms=round((time.time() - start) * 1000, 2),
                cached_records=self.cache.get_stats().get("by_provider", {}).get("string", 0),
                message=f"STRING responded with status {res.status_code}",
            )
            self.last_health = health
            return health
        except Exception as e:
            health = ProviderHealth(
                provider="STRING",
                status="unavailable",
                latency_ms=round((time.time() - start) * 1000, 2),
                cached_records=self.cache.get_stats().get("by_provider", {}).get("string", 0),
                message=f"STRING ping failed ({e}). Local interactome fallback active.",
            )
            self.last_health = health
            return health

    def get_interactions(
        self,
        genes: List[str],
        min_score: float = 0.400,
        species: int = 9606,
        network_source: str = "hybrid",  # "string", "local", "hybrid"
    ) -> Tuple[List[InteractionEdge], KnowledgeStatus]:
        """
        Retrieves PPI network for seed genes.
        Supports:
          - "local": Only local aging interactome CSV.
          - "string": Only live or cached STRING DB.
          - "hybrid": Merged STRING + Local interactome.
        """
        clean_genes = sorted(list(set(
            str(g).replace("GENE_", "").split("_")[-1].upper()
            for g in genes if str(g).strip()
        )))

        if not clean_genes:
            return [], KnowledgeStatus.NOT_FOUND

        if network_source == "local":
            local_edges = self._load_local_fallback(clean_genes)
            return local_edges, KnowledgeStatus.LOCAL_FALLBACK

        # Check Cache
        cache_params = {
            "genes": clean_genes,
            "min_score": min_score,
            "species": species,
        }
        cached = self.cache.get("string", cache_params)

        string_edges: List[InteractionEdge] = []
        overall_status = KnowledgeStatus.LIVE

        if cached:
            payload, meta = cached
            string_edges = [
                InteractionEdge(**item) for item in payload
            ]
            overall_status = KnowledgeStatus.CACHED
            logger.info(f"Loaded {len(string_edges)} STRING edges from cache")
        elif self.enable_live:
            try:
                string_edges = self._fetch_live_interactions(clean_genes, min_score, species)
                # Save to cache
                self.cache.set(
                    "string",
                    cache_params,
                    [e.to_dict() for e in string_edges],
                    provider_version="v12.0",
                )
                overall_status = KnowledgeStatus.LIVE
                logger.info(f"Retrieved {len(string_edges)} live STRING edges")
            except Exception as e:
                logger.warning(f"STRING live retrieval failed: {e}. Falling back to local interactome.")
                overall_status = KnowledgeStatus.LOCAL_FALLBACK
        else:
            overall_status = KnowledgeStatus.LOCAL_FALLBACK

        # Handle local fallback when string_edges is empty or failed
        if not string_edges or overall_status == KnowledgeStatus.LOCAL_FALLBACK:
            local_edges = self._load_local_fallback(clean_genes)
            if network_source == "string" and overall_status == KnowledgeStatus.LOCAL_FALLBACK:
                # User wanted STRING only but it failed -> return local fallback with clear status
                return local_edges, KnowledgeStatus.LOCAL_FALLBACK
            return local_edges, KnowledgeStatus.LOCAL_FALLBACK

        # If hybrid, merge with local aging interactome
        if network_source == "hybrid":
            local_edges = self._load_local_fallback(clean_genes)
            merged = self._merge_edges(string_edges, local_edges)
            return merged, overall_status

        return string_edges, overall_status

    def _fetch_live_interactions(
        self,
        genes: List[str],
        min_score: float,
        species: int,
    ) -> List[InteractionEdge]:
        """Queries STRING /network endpoint."""
        self.rate_limiter.wait()
        score_int = int(min_score * 1000)  # STRING expects 0..1000

        @retry_with_backoff("STRING", max_retries=2, base_delay=0.5)
        def _get():
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.base_url}/network",
                    data={
                        "identifiers": "%0d".join(genes),
                        "species": str(species),
                        "required_score": str(score_int),
                        "caller_identity": "bioage_x_research",
                    },
                )
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code in (400, 404):
                    logger.debug(f"STRING query returned status {resp.status_code}")
                    return []
                resp.raise_for_status()

        raw_data = _get()
        if not isinstance(raw_data, list):
            return []

        edges: List[InteractionEdge] = []
        now_utc = datetime.now(timezone.utc).isoformat()

        for row in raw_data:
            p_a = row.get("preferredName_A", "").upper()
            p_b = row.get("preferredName_B", "").upper()
            if not p_a or not p_b or p_a == p_b:
                continue

            score = float(row.get("score", 0.0))
            if score > 1.0:
                score = round(score / 1000.0, 3)

            evidence = {
                "experiments": float(row.get("escore", 0.0)),
                "database": float(row.get("dscore", 0.0)),
                "textmining": float(row.get("tscore", 0.0)),
                "coexpression": float(row.get("ascore", 0.0)),
            }

            edge = InteractionEdge(
                source=p_a,
                target=p_b,
                source_type="Protein",
                target_type="Protein",
                interaction_type="functional",
                confidence_score=score,
                evidence_scores=evidence,
                provider="STRING",
                provider_version="v12.0",
                status=KnowledgeStatus.LIVE,
                retrieved_at=now_utc,
            )
            edges.append(edge)

        return edges

    def _load_local_fallback(self, query_genes: List[str]) -> List[InteractionEdge]:
        """Loads canonical aging interactome edges connected to query genes."""
        query_set = set(query_genes)
        now_utc = datetime.now(timezone.utc).isoformat()
        edges: List[InteractionEdge] = []

        if self.edge_file_path.exists():
            try:
                df = pd.read_csv(self.edge_file_path)
                for _, row in df.iterrows():
                    src = str(row["source"]).upper()
                    tgt = str(row["target"]).upper()
                    if src in query_set or tgt in query_set or not query_set:
                        edges.append(InteractionEdge(
                            source=src,
                            target=tgt,
                            source_type=str(row.get("source_type", "Gene")),
                            target_type=str(row.get("target_type", "Gene")),
                            interaction_type=str(row.get("edge_type", "regulation")),
                            confidence_score=float(row.get("weight", 0.85)),
                            evidence_scores={"curated_literature": float(row.get("weight", 0.85))},
                            provider="Local Aging Interactome",
                            provider_version="curated_v1",
                            status=KnowledgeStatus.LOCAL_FALLBACK,
                            retrieved_at=now_utc,
                        ))
                if edges:
                    return edges
            except Exception as e:
                logger.warning(f"Failed to read local edge file: {e}")

        # Built-in minimal fallback if CSV missing
        builtin_defaults = [
            ("TP53", "CDKN1A", 0.95, "regulation"),
            ("CDKN2A", "RB1", 0.90, "regulation"),
            ("SIRT1", "TP53", 0.85, "regulation"),
            ("SIRT1", "FOXO3", 0.88, "interaction"),
            ("MTOR", "RPS6KB1", 0.92, "regulation"),
            ("AKT1", "MTOR", 0.94, "regulation"),
            ("IL6", "STAT3", 0.91, "regulation"),
            ("TNF", "NFKB1", 0.93, "regulation"),
            ("TERT", "POT1", 0.86, "interaction"),
            ("ELOVL2", "FHL2", 0.72, "association"),
            ("FHL2", "TP53", 0.78, "interaction"),
            ("SOD2", "FOXO3", 0.80, "regulation"),
            ("GDF15", "TP53", 0.81, "regulation"),
            ("KLOTHO", "IGF1", 0.84, "regulation"),
            ("DNMT1", "ELOVL2", 0.79, "regulation"),
        ]
        for src, tgt, score, etype in builtin_defaults:
            if src in query_set or tgt in query_set or not query_set:
                edges.append(InteractionEdge(
                    source=src,
                    target=tgt,
                    source_type="Protein",
                    target_type="Protein",
                    interaction_type=etype,
                    confidence_score=score,
                    evidence_scores={"curated_literature": score},
                    provider="Local Aging Interactome",
                    provider_version="curated_v1",
                    status=KnowledgeStatus.LOCAL_FALLBACK,
                    retrieved_at=now_utc,
                ))

        return edges

    def _merge_edges(
        self,
        string_edges: List[InteractionEdge],
        local_edges: List[InteractionEdge],
    ) -> List[InteractionEdge]:
        """Merges STRING edges and Local edges, preventing duplicate undirected pairs."""
        seen_pairs = set()
        merged = []

        # Keep STRING edges
        for e in string_edges:
            pair = tuple(sorted([e.source, e.target]))
            seen_pairs.add(pair)
            merged.append(e)

        # Append unique local edges
        for e in local_edges:
            pair = tuple(sorted([e.source, e.target]))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                merged.append(e)

        return merged
