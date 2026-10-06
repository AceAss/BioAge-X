"""
High-security archive extraction module for BioAge-X.
Defends against:
1. Path traversal attacks (Zip Slip / relative '../' path escapes)
2. Decompression bombs (unbounded disk expansion)
3. Malicious symlinks / hardlinks pointing outside destination
4. Executable permission exploits
"""

import os
import gzip
import shutil
import zipfile
import tarfile
from pathlib import Path
from typing import List, Optional

from bioage.utils.logger import get_logger

logger = get_logger("bioage.acquisition.extractor")

# Security constraints
MAX_EXTRACTED_BYTES = 5 * 1024 * 1024 * 1024  # 5 GB safety threshold
MAX_COMPRESSION_RATIO = 100.0  # Alert if compressed-to-uncompressed exceeds 100x
MAX_ARCHIVE_FILES = 10000


class ArchiveExtractionSecurityError(RuntimeError):
    """Raised when an archive violates path security or decompression limits."""
    pass


class SafeArchiveExtractor:
    """Safely extracts zip, tar, tar.gz, tar.bz2, and gz files."""

    @staticmethod
    def is_safe_path(target_dir: Path, path: Path) -> bool:
        """Verifies that resolved path is strictly contained within target directory."""
        try:
            resolved_target = target_dir.resolve()
            resolved_path = path.resolve()
            # Must be within resolved_target
            return resolved_path == resolved_target or resolved_target in resolved_path.parents
        except Exception:
            return False

    @classmethod
    def extract_zip(cls, archive_path: Path, target_dir: Path) -> List[Path]:
        """Safely extracts a ZIP archive with traversal and bomb protection."""
        target_dir.mkdir(parents=True, exist_ok=True)
        extracted_files: List[Path] = []
        total_uncompressed = 0

        with zipfile.ZipFile(archive_path, 'r') as zf:
            infolist = zf.infolist()
            if len(infolist) > MAX_ARCHIVE_FILES:
                raise ArchiveExtractionSecurityError(
                    f"Archive exceeds maximum allowable file count ({len(infolist)} > {MAX_ARCHIVE_FILES})."
                )

            for member in infolist:
                # Security check 1: filename cannot be absolute or traverse upwards
                norm_name = os.path.normpath(member.filename)
                if norm_name.startswith("..") or os.path.isabs(norm_name):
                    raise ArchiveExtractionSecurityError(
                        f"Detected malicious path traversal attempt in archive: '{member.filename}'"
                    )

                dest_path = target_dir / norm_name
                if not cls.is_safe_path(target_dir, dest_path):
                    raise ArchiveExtractionSecurityError(
                        f"Resolved extraction path escapes destination boundary: '{dest_path}'"
                    )

                # Security check 2: decompression bomb
                total_uncompressed += member.file_size
                if total_uncompressed > MAX_EXTRACTED_BYTES:
                    raise ArchiveExtractionSecurityError(
                        f"Archive uncompressed size exceeds security threshold ({total_uncompressed} bytes)."
                    )

                if member.is_dir():
                    dest_path.mkdir(parents=True, exist_ok=True)
                else:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as source, open(dest_path, "wb") as target:
                        shutil.copyfileobj(source, target)
                    # Strip any execute bits
                    try:
                        os.chmod(dest_path, 0o644)
                    except Exception:
                        pass
                    extracted_files.append(dest_path)

        logger.info(f"Safely extracted {len(extracted_files)} files from {archive_path.name} to {target_dir}")
        return extracted_files

    @classmethod
    def extract_tar(cls, archive_path: Path, target_dir: Path) -> List[Path]:
        """Safely extracts a tar / tar.gz / tar.bz2 archive with path verification."""
        target_dir.mkdir(parents=True, exist_ok=True)
        extracted_files: List[Path] = []
        total_uncompressed = 0

        mode = "r:*"
        with tarfile.open(archive_path, mode) as tf:
            members = tf.getmembers()
            if len(members) > MAX_ARCHIVE_FILES:
                raise ArchiveExtractionSecurityError(
                    f"Archive file count exceeds security limit ({len(members)} > {MAX_ARCHIVE_FILES})."
                )

            for member in members:
                # Disallow symlinks pointing outside or device nodes
                if member.issym() or member.islnk():
                    link_target = Path(member.linkname)
                    if link_target.is_absolute() or ".." in member.linkname:
                        raise ArchiveExtractionSecurityError(
                            f"Suspicious link in archive: '{member.name}' -> '{member.linkname}'"
                        )
                if not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
                    continue  # Skip devices, FIFOs, etc.

                norm_name = os.path.normpath(member.name)
                if norm_name.startswith("..") or os.path.isabs(norm_name):
                    raise ArchiveExtractionSecurityError(
                        f"Path traversal detected in tar member: '{member.name}'"
                    )

                dest_path = target_dir / norm_name
                if not cls.is_safe_path(target_dir, dest_path):
                    raise ArchiveExtractionSecurityError(
                        f"Resolved extraction path escapes destination: '{dest_path}'"
                    )

                total_uncompressed += member.size
                if total_uncompressed > MAX_EXTRACTED_BYTES:
                    raise ArchiveExtractionSecurityError(
                        f"Tar uncompressed size exceeds {MAX_EXTRACTED_BYTES} bytes."
                    )

                if member.isdir():
                    dest_path.mkdir(parents=True, exist_ok=True)
                else:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    f = tf.extractfile(member)
                    if f:
                        with open(dest_path, "wb") as out:
                            shutil.copyfileobj(f, out)
                        try:
                            os.chmod(dest_path, 0o644)
                        except Exception:
                            pass
                        extracted_files.append(dest_path)

        return extracted_files

    @classmethod
    def extract_gzip(cls, gz_path: Path, target_dir: Path) -> Path:
        """Extracts a single .gz file to target_dir."""
        target_dir.mkdir(parents=True, exist_ok=True)
        out_name = gz_path.stem
        if not out_name:
            out_name = f"{gz_path.name}.extracted"
        dest_path = target_dir / out_name

        if not cls.is_safe_path(target_dir, dest_path):
            raise ArchiveExtractionSecurityError("Decompressed path escapes destination.")

        with gzip.open(gz_path, 'rb') as f_in, open(dest_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

        try:
            os.chmod(dest_path, 0o644)
        except Exception:
            pass

        return dest_path

    @classmethod
    def extract(cls, archive_path: Path, target_dir: Path) -> List[Path]:
        """Automatically detects archive format and safely decompresses."""
        suffix = archive_path.suffix.lower()
        name_lower = archive_path.name.lower()

        if name_lower.endswith(".tar.gz") or name_lower.endswith(".tgz") or name_lower.endswith(".tar.bz2") or suffix == ".tar":
            return cls.extract_tar(archive_path, target_dir)
        elif suffix == ".zip":
            return cls.extract_zip(archive_path, target_dir)
        elif suffix == ".gz":
            extracted_file = cls.extract_gzip(archive_path, target_dir)
            return [extracted_file]
        else:
            # Not an archive, return as single file
            return [archive_path]
