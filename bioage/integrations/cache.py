"""
Persistent Caching Layer for BioAge-X External Biological Knowledge.
Provides deterministic, file-backed caching for identifier mappings,
PPI networks, pathway enrichment, and public dataset discovery.
Ensures zero redundant external hits and reproducible experiment tracking.
"""

from pathlib import Path
import json
import hashlib
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone

from bioage.utils.logger import get_logger

logger = get_logger("bioage.integrations.cache")

DEFAULT_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "cache" / "integrations"


class PersistentBiologicalCache:
    """File-backed persistent cache for external biological API calls."""

    def __init__(self, cache_dir: Optional[Path] = None, default_ttl_seconds: int = 604800):
        """
        Initializes cache directory.
        default_ttl_seconds: 7 days by default for biological annotations.
        """
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl_seconds
        self._stats = {"hits": 0, "misses": 0, "writes": 0}

    def _generate_key(self, provider: str, params: Dict[str, Any]) -> str:
        """Computes a deterministic hash key from provider and normalized parameters."""
        serialized = json.dumps(params, sort_keys=True, default=str)
        raw = f"{provider.lower()}:{serialized}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _get_file_path(self, provider: str, key: str) -> Path:
        """Returns the isolated file path for a provider key."""
        provider_dir = self.cache_dir / provider.lower()
        provider_dir.mkdir(parents=True, exist_ok=True)
        return provider_dir / f"{key}.json"

    def get(self, provider: str, params: Dict[str, Any]) -> Optional[Tuple[Any, Dict[str, Any]]]:
        """
        Retrieves cached response if present and not expired.
        Returns: (response_payload, metadata) or None.
        """
        key = self._generate_key(provider, params)
        file_path = self._get_file_path(provider, key)

        if not file_path.exists():
            self._stats["misses"] += 1
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                record = json.load(f)

            # Check expiration
            now = time.time()
            created_at_ts = record.get("created_at_ts", 0)
            ttl = record.get("ttl_seconds", self.default_ttl)

            if ttl > 0 and (now - created_at_ts) > ttl:
                logger.debug(f"Cache expired for {provider} key {key[:8]}")
                self._stats["misses"] += 1
                return None

            self._stats["hits"] += 1
            metadata = {
                "provider": record.get("provider", provider),
                "retrieved_at": record.get("retrieved_at"),
                "provider_version": record.get("provider_version"),
                "checksum": record.get("checksum"),
                "key": key,
            }
            return record.get("response_payload"), metadata

        except Exception as e:
            logger.warning(f"Error reading cache file {file_path}: {e}")
            self._stats["misses"] += 1
            return None

    def set(
        self,
        provider: str,
        params: Dict[str, Any],
        payload: Any,
        provider_version: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
    ) -> str:
        """
        Persists a biological API payload to disk.
        Returns the SHA-256 cache key.
        """
        key = self._generate_key(provider, params)
        file_path = self._get_file_path(provider, key)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl

        payload_bytes = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        checksum = hashlib.sha256(payload_bytes).hexdigest()

        now_utc = datetime.now(timezone.utc).isoformat()
        record = {
            "provider": provider,
            "request_key": key,
            "request_params": params,
            "response_payload": payload,
            "retrieved_at": now_utc,
            "created_at_ts": time.time(),
            "provider_version": provider_version or "latest",
            "ttl_seconds": ttl,
            "checksum": checksum,
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2, default=str)
            self._stats["writes"] += 1
            logger.debug(f"Cached {provider} response ({len(payload_bytes)} bytes) at {key[:8]}")
        except Exception as e:
            logger.error(f"Failed to write cache for {provider}: {e}")

        return key

    def invalidate(self, provider: Optional[str] = None) -> int:
        """Removes cache entries for a provider or all providers."""
        count = 0
        target_dir = self.cache_dir / provider.lower() if provider else self.cache_dir
        if not target_dir.exists():
            return 0

        for file in target_dir.rglob("*.json"):
            try:
                file.unlink()
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {file}: {e}")

        logger.info(f"Invalidated {count} cache records for {provider or 'all providers'}")
        return count

    def get_stats(self) -> Dict[str, Any]:
        """Calculates cache inventory per provider."""
        stats = {
            "total_records": 0,
            "by_provider": {},
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "writes": self._stats["writes"],
            "cache_dir": str(self.cache_dir),
        }

        if self.cache_dir.exists():
            for prov_dir in self.cache_dir.iterdir():
                if prov_dir.is_dir():
                    files = list(prov_dir.glob("*.json"))
                    stats["by_provider"][prov_dir.name] = len(files)
                    stats["total_records"] += len(files)

        return stats


# Global Singleton instance
_GLOBAL_CACHE: Optional[PersistentBiologicalCache] = None


def get_integration_cache() -> PersistentBiologicalCache:
    """Returns singleton cache instance."""
    global _GLOBAL_CACHE
    if _GLOBAL_CACHE is None:
        _GLOBAL_CACHE = PersistentBiologicalCache()
    return _GLOBAL_CACHE


# Convenient alias
get_biological_cache = get_integration_cache
