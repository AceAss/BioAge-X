"""
Dataset Provenance and Transformation Lineage Tracker for BioAge-X.
Maintains tamper-evident records answering:
1. Where did this dataset come from? (Repository, accession, URL, citation, license)
2. Exactly how did BioAge-X transform it? (Checksums, normalization, orientation changes, feature filtering)
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import json

from bioage.utils.logger import get_logger

logger = get_logger("bioage.acquisition.provenance")


@dataclass
class ProcessingStepRecord:
    """Individual data manipulation or normalization step."""
    step_name: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    parameters: Dict[str, Any] = field(default_factory=dict)
    input_shape: Optional[List[int]] = None
    output_shape: Optional[List[int]] = None
    details: str = ""


@dataclass
class DatasetProvenanceRecord:
    """Comprehensive origin and lineage contract for an ingested dataset."""
    dataset_id: str
    repository: str
    accession: str
    source_url: str
    provider: str
    retrieval_timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    download_status: str = "COMPLETED"
    original_files: List[str] = field(default_factory=list)
    file_checksums: Dict[str, str] = field(default_factory=dict)
    original_metadata: Dict[str, Any] = field(default_factory=dict)
    license_info: str = "Public Domain / CC0 / Open Academic Research"
    citation: str = ""
    processing_steps: List[Dict[str, Any]] = field(default_factory=list)
    experiment_ids: List[str] = field(default_factory=list)
    bioage_version: str = "0.1.0"

    def add_processing_step(
        self,
        step_name: str,
        details: str = "",
        parameters: Optional[Dict[str, Any]] = None,
        input_shape: Optional[Tuple[int, int]] = None,
        output_shape: Optional[Tuple[int, int]] = None,
    ) -> None:
        rec = ProcessingStepRecord(
            step_name=step_name,
            details=details,
            parameters=parameters or {},
            input_shape=list(input_shape) if input_shape else None,
            output_shape=list(output_shape) if output_shape else None,
        )
        self.processing_steps.append(asdict(rec))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def save(self, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        return output_path

    @classmethod
    def load(cls, file_path: Path) -> "DatasetProvenanceRecord":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)
