"""
Base interfaces, data transfer objects, and status enumerations for
the Universal Biological Data Acquisition Layer in BioAge-X.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime, timezone


class AccessType(str, Enum):
    """Access tier of an external biological data repository."""
    PUBLIC = "PUBLIC"
    CONDITIONAL = "CONDITIONAL"  # Requires specialized preprocessing, file selection, or terms
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"  # Requires login token / API key
    RESTRICTED = "RESTRICTED"  # Controlled access (e.g. dbGaP, EGA, DAC approval)


class CompatibilityLevel(str, Enum):
    """Compatibility classification for BioAge-X multi-omics workflows."""
    COMPATIBLE = "COMPATIBLE"
    PARTIALLY_COMPATIBLE = "PARTIALLY_COMPATIBLE"
    REQUIRES_PREPROCESSING = "REQUIRES_PREPROCESSING"
    UNSUPPORTED = "UNSUPPORTED"


class DownloadOptionType(str, Enum):
    """Granularity of download offerings."""
    METADATA_ONLY = "METADATA_ONLY"
    EXPRESSION_MATRIX = "EXPRESSION_MATRIX"
    SELECT_FILES = "SELECT_FILES"
    FULL_DATASET = "FULL_DATASET"


@dataclass
class DatasetSearchResult:
    """Summary record returned by a provider search operation."""
    accession: str
    title: str
    repository: str
    organism: str
    tissue: str
    omics_type: str
    study_type: str
    sample_count: int
    age_metadata_available: bool
    file_count: int
    approximate_size: str
    availability: str  # "Open Access", "Restricted Access", "Requires Login"
    provider: str
    source_url: str

    @property
    def modality(self) -> str:
        return self.omics_type.lower()

    @property
    def requires_preprocessing(self) -> bool:
        st = self.study_type.lower()
        return "raw" in st or "sequencing" in st or self.repository in ("SRA", "ENA")

    @property
    def access_restricted(self) -> bool:
        av = self.availability.lower()
        return "restricted" in av or "dbgap" in av or "controlled" in av

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["modality"] = self.modality
        d["requires_preprocessing"] = self.requires_preprocessing
        d["access_restricted"] = self.access_restricted
        return d


@dataclass
class DownloadOption:
    """Download package offered to user."""
    option_id: str
    title: str
    description: str
    size_bytes: int
    file_count: int
    option_type: DownloadOptionType
    requires_auth: bool = False
    access_restricted: bool = False
    requires_preprocessing: bool = False

    @property
    def label(self) -> str:
        return self.title

    @property
    def format(self) -> str:
        return self.option_type.value

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["option_type"] = self.option_type.value
        d["label"] = self.label
        d["format"] = self.format
        return d


@dataclass
class DatasetMetadata:
    """Detailed metadata inspection record displayed prior to download."""
    accession: str
    title: str
    description: str
    repository: str
    organism: str
    tissue: str
    omics_type: str
    study_type: str
    sample_count: int
    available_files: List[str]
    file_types: List[str]
    approximate_size_bytes: int
    approximate_size_display: str
    age_metadata_status: str  # "AVAILABLE", "PARTIAL", "UNAVAILABLE"
    compatibility_status: CompatibilityLevel
    required_preprocessing: str
    potential_limitations: str
    license_info: str
    citation: str
    source_url: str
    restricted_access_details: Optional[str] = None
    access_type: AccessType = AccessType.PUBLIC

    @property
    def modality(self) -> str:
        return self.omics_type.lower()

    @property
    def download_options(self) -> List[DownloadOption]:
        opts = []
        is_restricted = bool(self.access_type == AccessType.RESTRICTED or "restricted" in self.compatibility_status.value.lower())
        is_raw = bool(self.compatibility_status == CompatibilityLevel.REQUIRES_PREPROCESSING)
        for idx, f in enumerate(self.available_files):
            opts.append(
                DownloadOption(
                    option_id=f"opt_{idx + 1}",
                    title=f"File: {f}",
                    description=f"Resource {f} ({self.approximate_size_display})",
                    size_bytes=self.approximate_size_bytes // max(1, len(self.available_files)),
                    file_count=1,
                    option_type=DownloadOptionType.EXPRESSION_MATRIX if ("matrix" in f.lower() or "csv" in f.lower()) else DownloadOptionType.SELECT_FILES,
                    requires_auth=is_restricted,
                    access_restricted=is_restricted or ("bam" in f.lower() or "raw" in f.lower() and self.repository == "GDC"),
                    requires_preprocessing=is_raw or ("fastq" in f.lower() or "sra" in f.lower()),
                )
            )
        if not opts:
            opts.append(
                DownloadOption(
                    option_id="opt_default",
                    title=f"Complete Dataset Archive ({self.accession})",
                    description=f"Full files package ({self.approximate_size_display})",
                    size_bytes=self.approximate_size_bytes,
                    file_count=len(self.available_files) or 1,
                    option_type=DownloadOptionType.FULL_DATASET,
                    requires_auth=is_restricted,
                    access_restricted=is_restricted,
                    requires_preprocessing=is_raw,
                )
            )
        return opts

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["compatibility_status"] = self.compatibility_status.value
        d["access_type"] = self.access_type.value
        d["modality"] = self.modality
        d["download_options"] = [opt.to_dict() for opt in self.download_options]
        return d


@dataclass
class DownloadResult:
    """Result of an executed download operation."""
    accession: str
    provider: str
    downloaded_files: List[Path]
    total_bytes: int
    elapsed_seconds: float
    checksums: Dict[str, str] = field(default_factory=dict)
    status: str = "COMPLETED"  # "COMPLETED", "FAILED", "CANCELLED"
    error_message: Optional[str] = None
    provenance_record: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["downloaded_files"] = [str(p) for p in self.downloaded_files]
        return d


@dataclass
class ValidationResult:
    """Outcome of safety, disk-space, and checksum validation checks."""
    is_valid: bool
    checksum_ok: bool
    disk_space_ok: bool
    format_detected: str
    omics_detected: str
    sample_count: int
    feature_count: int
    compatibility_level: CompatibilityLevel
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["compatibility_level"] = self.compatibility_level.value
        return d


@dataclass
class IngestionResult:
    """Outcome of dataset normalization and BioAge-X registry import."""
    dataset_id: str
    name: str
    file_path: str
    format: str
    n_samples: int
    n_features: int
    detected_modality: str
    compatibility_status: CompatibilityLevel
    profile: Dict[str, Any]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["compatibility_status"] = self.compatibility_status.value
        return d


class DatasetProvider(ABC):
    """
    Extensible connector interface for public biological data repositories.
    Every repository connector implements this contract.
    """

    name: str = "Generic"
    category: str = "General"
    description: str = "Base Biological Data Provider"
    access_type: AccessType = AccessType.PUBLIC
    supported_accession_patterns: List[str] = []

    @abstractmethod
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[DatasetSearchResult]:
        """Searches repository for datasets matching biological query."""
        pass

    @abstractmethod
    def get_metadata(self, accession: str) -> DatasetMetadata:
        """Retrieves and normalizes dataset metadata for preview."""
        pass

    @abstractmethod
    def get_download_options(self, accession: str) -> List[DownloadOption]:
        """Provides available download granularities (Metadata, Matrix, Full)."""
        pass

    @abstractmethod
    def download(
        self,
        accession: str,
        option_id: Optional[str] = None,
        target_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[int, int, float, str], None]] = None,
    ) -> DownloadResult:
        """
        Executes streaming, validated download of selected dataset files.
        progress_callback signature: (downloaded_bytes, total_bytes, speed_bytes_per_sec, status_text)
        """
        pass

    @abstractmethod
    def validate(self, download_result: DownloadResult) -> ValidationResult:
        """Inspects downloaded files for integrity, format, and omics modality."""
        pass

    @abstractmethod
    def import_dataset(
        self,
        download_result: DownloadResult,
        options: Optional[Dict[str, Any]] = None,
    ) -> IngestionResult:
        """Normalizes and ingests dataset into BioAge-X platform storage and database."""
        pass
