"""
Generic Public Dataset Connector for BioAge-X.
Supports downloading, extracting, validating, and ingesting datasets from any
public HTTP/HTTPS/FTP URL, download manifest, or uploaded archive.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import urllib.parse

from bioage.acquisition.base import (
    DatasetProvider,
    DatasetSearchResult,
    DatasetMetadata,
    DownloadOption,
    DownloadOptionType,
    DownloadResult,
    ValidationResult,
    IngestionResult,
    AccessType,
    CompatibilityLevel,
)
from bioage.acquisition.downloader import DownloadManager
from bioage.acquisition.extractor import SafeArchiveExtractor
from bioage.acquisition.validator import DatasetValidator
from bioage.acquisition.normalizer import DatasetNormalizer
from bioage.acquisition.provenance import DatasetProvenanceRecord
from bioage.utils.logger import get_logger

logger = get_logger("bioage.acquisition.providers.generic")


class GenericURLProvider(DatasetProvider):
    """Universal adapter for public direct URLs and archives."""

    name = "Generic URL"
    category = "Generic Public Web"
    description = "Downloads and ingests biological datasets from direct HTTP/HTTPS/FTP URLs or archives."
    access_type = AccessType.PUBLIC
    supported_accession_patterns = [r"^https?://", r"^ftp://"]

    def __init__(self, download_manager: Optional[DownloadManager] = None):
        self.downloader = download_manager or DownloadManager()

    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[DatasetSearchResult]:
        """Generic provider does not have a global search index; returns URL match if query is a URL."""
        if query.startswith("http://") or query.startswith("https://") or query.startswith("ftp://"):
            filename = Path(urllib.parse.urlparse(query).path).name or "dataset_download"
            return [
                DatasetSearchResult(
                    accession=query,
                    title=f"Direct Public URL: {filename}",
                    repository="Generic Public Web",
                    organism="Unknown (Auto-detect)",
                    tissue="Unknown (Auto-detect)",
                    omics_type="Unknown (Auto-detect)",
                    study_type="Public Web Resource",
                    sample_count=0,
                    age_metadata_available=False,
                    file_count=1,
                    approximate_size="Unknown",
                    availability="Open Access",
                    provider=self.name,
                    source_url=query,
                )
            ]
        return []

    def get_metadata(self, accession: str) -> DatasetMetadata:
        """Inspects URL metadata and provides preliminary dataset profile."""
        url = accession
        parsed = urllib.parse.urlparse(url)
        filename = Path(parsed.path).name or "dataset_file"
        ext = "".join(Path(parsed.path).suffixes)

        return DatasetMetadata(
            accession=accession,
            title=f"Public Data Stream: {filename}",
            description=f"Direct biological resource linked from {parsed.netloc}. BioAge-X will stream, extract if compressed, and auto-profile.",
            repository="Generic Public Resource",
            organism="Auto-detect upon ingestion",
            tissue="Auto-detect upon ingestion",
            omics_type="Auto-detect upon inspection",
            study_type="Public Dataset",
            sample_count=0,
            available_files=[filename],
            file_types=[ext or "tabular/archive"],
            approximate_size_bytes=0,
            approximate_size_display="Streaming",
            age_metadata_status="UNAVAILABLE",
            compatibility_status=CompatibilityLevel.PARTIALLY_COMPATIBLE,
            required_preprocessing="Auto-normalization and feature orientation check",
            potential_limitations="Requires public read access without login session or CAPTCHA.",
            license_info="Subject to hosting domain terms of use",
            citation=f"Online resource hosted at {url}",
            source_url=url,
            access_type=AccessType.PUBLIC,
        )

    def get_download_options(self, accession: str) -> List[DownloadOption]:
        return [
            DownloadOption(
                option_id="full_url_download",
                title="Download and Ingest Public Resource",
                description="Streams the file directly, extracts if compressed, and registers in BioAge-X.",
                size_bytes=0,
                file_count=1,
                option_type=DownloadOptionType.FULL_DATASET,
            )
        ]

    def download(
        self,
        accession: str,
        option_id: Optional[str] = None,
        target_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[int, int, float, str], None]] = None,
    ) -> DownloadResult:
        url = accession
        dest_dir = target_dir or Path("data/raw/generic")
        dest_dir.mkdir(parents=True, exist_ok=True)

        parsed = urllib.parse.urlparse(url)
        filename = Path(parsed.path).name or "downloaded_resource.dat"
        target_path = dest_dir / filename

        import time
        start_t = time.time()
        file_path = self.downloader.download_url(
            url=url,
            target_path=target_path,
            progress_callback=progress_callback,
        )
        elapsed = max(0.001, time.time() - start_t)
        total_b = file_path.stat().st_size
        checksum = self.downloader.compute_checksum(file_path)

        # If archive, safely extract
        extracted = SafeArchiveExtractor.extract(file_path, dest_dir / file_path.stem)

        return DownloadResult(
            accession=accession,
            provider=self.name,
            downloaded_files=extracted,
            total_bytes=total_b,
            elapsed_seconds=elapsed,
            checksums={file_path.name: checksum},
            status="COMPLETED",
        )

    def validate(self, download_result: DownloadResult) -> ValidationResult:
        if not download_result.downloaded_files:
            return ValidationResult(
                is_valid=False,
                checksum_ok=True,
                disk_space_ok=True,
                format_detected="none",
                omics_detected="none",
                sample_count=0,
                feature_count=0,
                compatibility_level=CompatibilityLevel.UNSUPPORTED,
                errors=["No files downloaded."],
            )

        # Inspect the primary file
        primary = download_result.downloaded_files[0]
        return DatasetValidator.inspect_file(primary)

    def import_dataset(
        self,
        download_result: DownloadResult,
        options: Optional[Dict[str, Any]] = None,
    ) -> IngestionResult:
        primary = download_result.downloaded_files[0]
        norm_dir = Path("data/processed")
        norm_path = norm_dir / f"generic_{primary.stem}_normalized.csv"

        out_path, profile = DatasetNormalizer.normalize_tabular_file(
            source_path=primary,
            output_path=norm_path,
        )

        dataset_id = f"DS-GENERIC-{primary.stem.upper()[:12]}"
        provenance = DatasetProvenanceRecord(
            dataset_id=dataset_id,
            repository="Generic Public Web",
            accession=download_result.accession,
            source_url=download_result.accession,
            provider=self.name,
            original_files=[str(f) for f in download_result.downloaded_files],
            file_checksums=download_result.checksums,
        )
        provenance.add_processing_step(
            step_name="Generic URL Ingestion & Normalization",
            details=f"Streamed and standardized into {norm_path.name}",
            output_shape=(profile["n_samples"], profile["n_features"]),
        )

        return IngestionResult(
            dataset_id=dataset_id,
            name=norm_path.name,
            file_path=str(out_path),
            format="csv",
            n_samples=profile["n_samples"],
            n_features=profile["n_features"],
            detected_modality=profile.get("detected_modality", "unknown"),
            compatibility_status=CompatibilityLevel.COMPATIBLE if profile.get("age_column") else CompatibilityLevel.PARTIALLY_COMPATIBLE,
            profile=profile,
            provenance=provenance.to_dict(),
        )
