"""
NCBI E-Utilities API Client for BioAge-X.
Interfaces with NCBI Entrez E-Utilities (esearch, esummary) for functional genomics
and GEO dataset discovery. Honors NCBI rate limits, supports optional NCBI_API_KEY,
and enforces non-blocking fault tolerance.
"""

from typing import Dict, List, Optional, Any
import os
import time
import httpx
from datetime import datetime, timezone

from bioage.integrations.base import (
    BiologicalKnowledgeProvider,
    ProviderHealth,
)
from bioage.integrations.cache import get_integration_cache, PersistentBiologicalCache
from bioage.integrations.rate_limit import RateLimiter, retry_with_backoff
from bioage.utils.logger import get_logger

logger = get_logger("bioage.integrations.ncbi")


class NCBIClient(BiologicalKnowledgeProvider):
    """Client for NCBI Entrez E-Utilities."""

    EUTILS_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 8.0,
        cache: Optional[PersistentBiologicalCache] = None,
        enable_live: bool = True,
    ):
        self.api_key = api_key or os.getenv("NCBI_API_KEY")
        self.base_url = (base_url or self.EUTILS_URL).rstrip("/")
        self.timeout = timeout
        self.cache = cache or get_integration_cache()
        self.enable_live = enable_live

        # Rate limit: 10 req/s with API key, 3 req/s without API key
        rps = 10.0 if self.api_key else 3.0
        self.rate_limiter = RateLimiter(requests_per_second=rps, provider_name="NCBI")
        self.last_health: Optional[ProviderHealth] = None

    @property
    def provider_name(self) -> str:
        return "NCBI/GEO"

    def check_health(self) -> ProviderHealth:
        """Pings NCBI E-utilities via einfo."""
        start = time.time()
        try:
            params = {"db": "gds", "retmode": "json"}
            if self.api_key:
                params["api_key"] = self.api_key

            with httpx.Client(timeout=4.0) as client:
                res = client.get(f"{self.base_url}/einfo.fcgi", params=params)
                latency = round((time.time() - start) * 1000, 2)
                if res.status_code == 200:
                    health = ProviderHealth(
                        provider="NCBI/GEO",
                        status="available",
                        version="Entrez E-Utilities v2.0",
                        latency_ms=latency,
                        last_successful_request=datetime.now(timezone.utc).isoformat(),
                        cached_records=self.cache.get_stats().get("by_provider", {}).get("ncbi", 0),
                        message="NCBI E-Utilities operational" + (" (API key active)" if self.api_key else " (Standard rate limit)"),
                    )
                    self.last_health = health
                    return health

            health = ProviderHealth(
                provider="NCBI/GEO",
                status="degraded",
                latency_ms=round((time.time() - start) * 1000, 2),
                cached_records=self.cache.get_stats().get("by_provider", {}).get("ncbi", 0),
                message=f"NCBI responded with status {res.status_code}",
            )
            self.last_health = health
            return health
        except Exception as e:
            health = ProviderHealth(
                provider="NCBI/GEO",
                status="unavailable",
                latency_ms=round((time.time() - start) * 1000, 2),
                cached_records=self.cache.get_stats().get("by_provider", {}).get("ncbi", 0),
                message=f"NCBI ping failed ({e}). Curated local aging catalog active.",
            )
            self.last_health = health
            return health

    def esearch_gds(self, term: str, retmax: int = 10) -> List[str]:
        """Searches GEO DataSets (gds) database, returning list of UID strings."""
        if not self.enable_live:
            return []

        self.rate_limiter.wait()
        params = {
            "db": "gds",
            "term": term,
            "retmax": retmax,
            "retmode": "json",
            "sort": "pub_date",
        }
        if self.api_key:
            params["api_key"] = self.api_key

        @retry_with_backoff("NCBI", max_retries=2, base_delay=0.5)
        def _get():
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/esearch.fcgi", params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("esearchresult", {}).get("idlist", [])
                resp.raise_for_status()
                return []

        try:
            return _get()
        except Exception as e:
            logger.warning(f"NCBI esearch failed for query '{term}': {e}")
            return []

    def esummary_gds(self, uids: List[str]) -> Dict[str, Any]:
        """Fetches document summaries for given GDS UIDs."""
        if not uids or not self.enable_live:
            return {}

        self.rate_limiter.wait()
        params = {
            "db": "gds",
            "id": ",".join(uids),
            "retmode": "json",
        }
        if self.api_key:
            params["api_key"] = self.api_key

        @retry_with_backoff("NCBI", max_retries=2, base_delay=0.5)
        def _get():
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/esummary.fcgi", params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("result", {})
                resp.raise_for_status()
                return {}

        try:
            return _get()
        except Exception as e:
            logger.warning(f"NCBI esummary failed for {len(uids)} UIDs: {e}")
            return {}
