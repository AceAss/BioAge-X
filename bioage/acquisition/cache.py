"""
Acquisition Cache Management for BioAge-X.
Caches remote metadata queries, search hits, manifests, and downloaded datasets
to eliminate redundant network requests and bandwidth consumption.
"""

import time
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from bioage.utils.logger import get_logger

logger = get_logger("bioage.acquisition.cache")


class CacheStatus(str, Enum):
    """Origin state of a retrieved dataset record."""
    LIVE = "LIVE"
    CACHED = "CACHED"
    LOCAL = "LOCAL"


class AcquisitionCache:
    """Manages cache directory for biological repository metadata and files."""

    def __init__(self, cache_dir: Optional[Path] = None, default_ttl_hours: int = 48):
        self.cache_dir = cache_dir or Path("data/cache/acquisition")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir = self.cache_dir / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.downloads_dir = self.cache_dir / "downloads"
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl_sec = default_ttl_hours * 3600

    def _get_key_path(self, namespace: str, key: str) -> Path:
        safe_key = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in key)
        return self.metadata_dir / f"{namespace}_{safe_key}.json"

    def get_metadata(self, namespace: str, key: str) -> Tuple[Optional[Dict[str, Any]], CacheStatus]:
        """Retrieves cached metadata if present and not expired."""
        path = self._get_key_path(namespace, key)
        if not path.exists():
            return None, CacheStatus.LIVE

        try:
            with open(path, "r", encoding="utf-8") as f:
                record = json.load(f)

            saved_time = record.get("_cached_at", 0)
            if time.time() - saved_time > self.default_ttl_sec:
                path.unlink(missing_ok=True)
                return None, CacheStatus.LIVE

            return record.get("data"), CacheStatus.CACHED
        except Exception as e:
            logger.warning(f"Error reading acquisition cache for {key}: {e}")
            return None, CacheStatus.LIVE

    def set_metadata(self, namespace: str, key: str, data: Dict[str, Any]) -> None:
        """Stores metadata record with timestamp."""
        path = self._get_key_path(namespace, key)
        try:
            record = {
                "_cached_at": time.time(),
                "namespace": namespace,
                "key": key,
                "data": data,
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write acquisition cache: {e}")

    # Compatibility alias
    put_metadata = set_metadata

    def clear(self, namespace: Optional[str] = None) -> int:
        """Clears cached metadata records."""
        cleared_count = 0
        for f in self.metadata_dir.glob("*.json"):
            if namespace is None or f.name.startswith(f"{namespace}_"):
                f.unlink(missing_ok=True)
                cleared_count += 1
        logger.info(f"Cleared {cleared_count} records from acquisition cache.")
        return cleared_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """Returns statistics on disk usage and cached objects."""
        files = list(self.metadata_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files) if files else 0
        return {
            "cached_metadata_count": len(files),
            "cache_size_bytes": total_size,
            "cache_size_kb": round(total_size / 1024, 2),
            "cache_directory": str(self.cache_dir),
        }
