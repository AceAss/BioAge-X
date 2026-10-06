"""
Robust Download Service for Universal Biological Data Acquisition in BioAge-X.

Features:
- Streaming chunked downloads
- Resumable transfers via HTTP Range headers
- Real-time progress and transfer speed calculation
- Disk space safety pre-checks
- Exponential backoff retry for transient network faults
- Checksum validation (SHA-256, MD5)
- Cancellation and failure cleanup
"""

import time
import shutil
import hashlib
from pathlib import Path
from typing import Optional, Callable, Dict, Any, Tuple
import requests

from bioage.utils.logger import get_logger

logger = get_logger("bioage.acquisition.downloader")

# Constants
DEFAULT_CHUNK_SIZE = 64 * 1024  # 64 KB
DEFAULT_TIMEOUT_SEC = 30
MAX_RETRIES = 3
INITIAL_BACKOFF_SEC = 1.0
DISK_SAFETY_BUFFER_RATIO = 1.30  # Require 30% headroom above estimated download size


class InsufficientDiskSpaceError(RuntimeError):
    """Raised when destination drive does not have sufficient space for dataset."""
    pass


class DownloadCancelledError(RuntimeError):
    """Raised when download operation is cancelled by the user or supervisor."""
    pass


class ChecksumMismatchError(RuntimeError):
    """Raised when downloaded file fails checksum integrity verification."""
    pass


class DownloadManager:
    """Manages secure, streaming, and resumable file downloads."""

    def __init__(self, target_root: Optional[Path] = None):
        self.target_root = target_root or Path("data/raw")
        self.target_root.mkdir(parents=True, exist_ok=True)
        self._cancellation_flags: Dict[str, bool] = {}

    def cancel_download(self, job_id: str) -> None:
        """Flags a running download for immediate cancellation."""
        self._cancellation_flags[job_id] = True
        logger.info(f"Cancellation requested for download job {job_id}")

    def is_cancelled(self, job_id: Optional[str]) -> bool:
        if not job_id:
            return False
        return self._cancellation_flags.get(job_id, False)

    @staticmethod
    def check_disk_space(target_dir: Path, required_bytes: int) -> Tuple[bool, int, int]:
        """
        Verifies that disk containing target_dir has sufficient free space.
        Returns: (is_sufficient, free_bytes, required_with_buffer_bytes)
        """
        try:
            total, used, free = shutil.disk_usage(target_dir)
            required_with_buffer = int(required_bytes * DISK_SAFETY_BUFFER_RATIO)
            is_ok = free >= required_with_buffer
            return is_ok, free, required_with_buffer
        except Exception as e:
            logger.warning(f"Disk space check error: {e}; defaulting to permissive.")
            return True, 10**12, required_bytes

    @staticmethod
    def compute_checksum(file_path: Path, algorithm: str = "sha256") -> str:
        """Computes cryptographic digest of local file."""
        hasher = hashlib.sha256() if algorithm.lower() == "sha256" else hashlib.md5()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def verify_checksum(file_path: Path, expected_checksum: str, algorithm: str = "sha256") -> bool:
        """Verifies if local file matches expected cryptographic checksum."""
        actual = DownloadManager.compute_checksum(file_path, algorithm=algorithm)
        return actual.lower() == expected_checksum.lower()

    def download_url(
        self,
        url: str,
        target_path: Path,
        expected_size: Optional[int] = None,
        expected_checksum: Optional[str] = None,
        checksum_algo: str = "sha256",
        job_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, float, str], None]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Path:
        """
        Streams file download with retries, progress reporting, and verification.
        """
        target_path.parent.mkdir(parents=True, exist_ok=True)
        req_headers = dict(headers or {})

        # 1. Disk space check
        if expected_size and expected_size > 0:
            ok, free_b, req_b = self.check_disk_space(target_path.parent, expected_size)
            if not ok:
                raise InsufficientDiskSpaceError(
                    f"Insufficient disk space on destination. Free: {free_b / 1e9:.2f} GB, "
                    f"Required: {req_b / 1e9:.2f} GB (including safety headroom)."
                )

        # 2. Check for existing partial file for resumable download
        downloaded_bytes = 0
        mode = "wb"
        if target_path.exists():
            downloaded_bytes = target_path.stat().st_size
            if downloaded_bytes > 0:
                req_headers["Range"] = f"bytes={downloaded_bytes}-"
                mode = "ab"
                logger.info(f"Attempting resumable download from byte {downloaded_bytes}")

        retry_count = 0
        backoff = INITIAL_BACKOFF_SEC

        while retry_count <= MAX_RETRIES:
            if self.is_cancelled(job_id):
                if target_path.exists():
                    target_path.unlink(missing_ok=True)
                raise DownloadCancelledError(f"Download of {url} cancelled.")

            try:
                with requests.get(
                    url,
                    headers=req_headers,
                    stream=True,
                    timeout=DEFAULT_TIMEOUT_SEC,
                ) as resp:
                    # Handle range response (206 Partial Content) vs 200 OK
                    if resp.status_code == 416:
                        # Range unsatisfiable, file already complete or server changed
                        break
                    elif resp.status_code == 200 and mode == "ab":
                        # Server does not support Range, restart from scratch
                        mode = "wb"
                        downloaded_bytes = 0

                    resp.raise_for_status()

                    total_size = downloaded_bytes + int(resp.headers.get("Content-Length", 0))
                    if not total_size or total_size == downloaded_bytes:
                        total_size = expected_size or 0

                    start_time = time.time()
                    last_progress_time = start_time

                    with open(target_path, mode) as f:
                        for chunk in resp.iter_content(chunk_size=DEFAULT_CHUNK_SIZE):
                            if self.is_cancelled(job_id):
                                target_path.unlink(missing_ok=True)
                                raise DownloadCancelledError(f"Download cancelled for {url}.")

                            if chunk:
                                f.write(chunk)
                                downloaded_bytes += len(chunk)

                                now = time.time()
                                if progress_callback and (now - last_progress_time >= 0.25):
                                    elapsed = max(now - start_time, 0.001)
                                    speed = downloaded_bytes / elapsed
                                    status_text = f"Downloading: {downloaded_bytes / 1e6:.1f} MB / {total_size / 1e6:.1f} MB"
                                    progress_callback(downloaded_bytes, total_size, speed, status_text)
                                    last_progress_time = now

                # Download loop completed successfully
                break

            except (requests.exceptions.RequestException, ConnectionError) as net_err:
                retry_count += 1
                if retry_count > MAX_RETRIES:
                    # Clean up partial file on hard failure
                    if target_path.exists():
                        target_path.unlink(missing_ok=True)
                    logger.error(f"Download failed after {MAX_RETRIES} retries: {net_err}")
                    raise

                logger.warning(
                    f"Transient download error on {url} ({net_err}). Retrying {retry_count}/{MAX_RETRIES} in {backoff}s..."
                )
                time.sleep(backoff)
                backoff *= 2.0

        # Final progress update
        if progress_callback:
            final_size = target_path.stat().st_size if target_path.exists() else downloaded_bytes
            progress_callback(final_size, final_size, 0.0, "Download complete. Validating integrity...")

        # 3. Checksum verification if provided
        if expected_checksum:
            actual_checksum = self.compute_checksum(target_path, algorithm=checksum_algo)
            if actual_checksum.lower() != expected_checksum.lower():
                target_path.unlink(missing_ok=True)
                raise ChecksumMismatchError(
                    f"Checksum validation failed for {target_path.name}. "
                    f"Expected {expected_checksum}, calculated {actual_checksum}."
                )
            logger.info(f"Checksum verified for {target_path.name} ({checksum_algo}: {actual_checksum})")

        return target_path
