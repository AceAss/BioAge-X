"""
Biological Provenance System for BioAge-X.
Tracks the exact origin, database release, retrieval timestamp, checksum,
and status (LIVE / CACHED / LOCAL_FALLBACK) for every biological annotation,
interaction edge, and pathway enrichment associated with an experiment.
"""

from pathlib import Path
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from bioage.integrations.base import KnowledgeStatus
from bioage.utils.logger import get_logger

logger = get_logger("bioage.integrations.provenance")

DEFAULT_PROVENANCE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "cache" / "provenance"


@dataclass
class ProvenanceEvent:
    """Individual provenance entry documenting a biological knowledge query."""
    provider: str
    query_type: str  # "identifier_resolution", "ppi_network", "pathway_enrichment", "dataset_metadata"
    status: KnowledgeStatus
    provider_version: Optional[str] = None
    records_count: int = 0
    cached_records_count: int = 0
    fallback_records_count: int = 0
    retrieved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    request_summary: Dict[str, Any] = field(default_factory=dict)
    checksum: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, KnowledgeStatus) else str(self.status)
        return d


class BiologicalProvenanceTracker:
    """Manages biological lineage and provenance records per experiment."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or DEFAULT_PROVENANCE_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._active_events: Dict[str, List[ProvenanceEvent]] = {}

    def record(
        self,
        experiment_id: str,
        provider: str,
        query_type: str,
        status: KnowledgeStatus,
        records_count: int = 0,
        cached_count: int = 0,
        fallback_count: int = 0,
        provider_version: Optional[str] = None,
        request_summary: Optional[Dict[str, Any]] = None,
        checksum: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ProvenanceEvent:
        """Appends a provenance event to the experiment lineage."""
        event = ProvenanceEvent(
            provider=provider,
            query_type=query_type,
            status=status,
            provider_version=provider_version,
            records_count=records_count,
            cached_records_count=cached_count,
            fallback_records_count=fallback_count,
            request_summary=request_summary or {},
            checksum=checksum,
            notes=notes,
        )

        if experiment_id not in self._active_events:
            self._active_events[experiment_id] = []
        self._active_events[experiment_id].append(event)

        # Persist to disk
        self._save_to_disk(experiment_id)
        return event

    def get_lineage(self, experiment_id: str) -> List[Dict[str, Any]]:
        """Returns all provenance events recorded for an experiment."""
        # Load from disk if not in memory
        if experiment_id not in self._active_events:
            self._load_from_disk(experiment_id)

        events = self._active_events.get(experiment_id, [])
        return [e.to_dict() for e in events]

    def get_summary(self, experiment_id: str) -> Dict[str, Any]:
        """
        Synthesizes a structured provenance breakdown for research reports and UI:
        counts by status (LIVE, CACHED, LOCAL_FALLBACK), provider versions, and timestamps.
        """
        events = self.get_lineage(experiment_id)
        if not events:
            return {
                "experiment_id": experiment_id,
                "total_queries": 0,
                "status_breakdown": {"LIVE": 0, "CACHED": 0, "LOCAL_FALLBACK": 0},
                "providers_used": [],
                "events": [],
            }

        status_counts = {"LIVE": 0, "CACHED": 0, "LOCAL_FALLBACK": 0, "OTHER": 0}
        providers_meta = {}

        for ev in events:
            st = ev["status"]
            if st in status_counts:
                status_counts[st] += 1
            else:
                status_counts["OTHER"] += 1

            prov = ev["provider"]
            if prov not in providers_meta:
                providers_meta[prov] = {
                    "provider": prov,
                    "version": ev.get("provider_version", "unknown"),
                    "latest_retrieval": ev.get("retrieved_at"),
                    "total_records": 0,
                    "statuses": set(),
                }
            providers_meta[prov]["total_records"] += ev.get("records_count", 0)
            providers_meta[prov]["statuses"].add(st)

        # Convert sets for JSON serialization
        for p in providers_meta.values():
            p["statuses"] = sorted(list(p["statuses"]))

        return {
            "experiment_id": experiment_id,
            "total_queries": len(events),
            "status_breakdown": status_counts,
            "providers_used": list(providers_meta.values()),
            "events": events,
        }

    def _get_file_path(self, experiment_id: str) -> Path:
        safe_id = "".join(c for c in experiment_id if c.isalnum() or c in ("-", "_"))
        return self.storage_dir / f"{safe_id}.json"

    def _save_to_disk(self, experiment_id: str) -> None:
        file_path = self._get_file_path(experiment_id)
        events = self._active_events.get(experiment_id, [])
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump([e.to_dict() for e in events], f, indent=2)
        except Exception as e:
            logger.warning(f"Could not persist provenance for {experiment_id}: {e}")

    def _load_from_disk(self, experiment_id: str) -> None:
        file_path = self._get_file_path(experiment_id)
        if not file_path.exists():
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_list = json.load(f)
            events = []
            for item in raw_list:
                ev = ProvenanceEvent(
                    provider=item["provider"],
                    query_type=item["query_type"],
                    status=KnowledgeStatus(item["status"]),
                    provider_version=item.get("provider_version"),
                    records_count=item.get("records_count", 0),
                    cached_records_count=item.get("cached_records_count", 0),
                    fallback_records_count=item.get("fallback_records_count", 0),
                    retrieved_at=item.get("retrieved_at", datetime.now(timezone.utc).isoformat()),
                    request_summary=item.get("request_summary", {}),
                    checksum=item.get("checksum"),
                    notes=item.get("notes"),
                )
                events.append(ev)
            self._active_events[experiment_id] = events
        except Exception as e:
            logger.warning(f"Could not load provenance for {experiment_id}: {e}")


# Singleton tracker instance
_GLOBAL_TRACKER: Optional[BiologicalProvenanceTracker] = None


def get_provenance_tracker() -> BiologicalProvenanceTracker:
    """Returns singleton provenance tracker instance."""
    global _GLOBAL_TRACKER
    if _GLOBAL_TRACKER is None:
        _GLOBAL_TRACKER = BiologicalProvenanceTracker()
    return _GLOBAL_TRACKER
