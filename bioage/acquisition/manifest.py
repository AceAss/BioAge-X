"""
Manifest Import and Multi-Sample Validation System for BioAge-X.
Supports dataset_manifest.yaml / dataset_manifest.json declarations
associating multi-omics files across local and external paths by sample ID.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import yaml
import json
import pandas as pd
import numpy as np

from bioage.acquisition.base import CompatibilityLevel
from bioage.utils.logger import get_logger

logger = get_logger("bioage.acquisition.manifest")


class ManifestValidationError(RuntimeError):
    """Raised when a dataset manifest violates integrity or schema rules."""
    pass


class ManifestImporter:
    """Parses and validates multi-sample / multi-omics manifests."""

    @classmethod
    def load_manifest(cls, manifest_path: Path) -> Dict[str, Any]:
        """Loads YAML or JSON manifest."""
        if not manifest_path.exists():
            raise ManifestValidationError(f"Manifest file not found: {manifest_path}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            if manifest_path.suffix.lower() in (".yaml", ".yml"):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)

        if not isinstance(data, dict):
            raise ManifestValidationError("Manifest root must be a mapping/dictionary.")

        return data

    @classmethod
    def validate_manifest(cls, manifest: Dict[str, Any], base_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Validates:
        - sample IDs (non-empty, unique)
        - file existence
        - age metadata presence and numeric format
        - modality declarations
        """
        base_path = base_dir or Path(".")
        samples = manifest.get("samples", [])
        if not samples or not isinstance(samples, list):
            raise ManifestValidationError("Manifest must contain a non-empty 'samples' list.")

        seen_ids = set()
        duplicate_ids = []
        missing_files = []
        samples_with_age = 0
        detected_modalities = set()

        for idx, s in enumerate(samples):
            if not isinstance(s, dict):
                raise ManifestValidationError(f"Sample at index {idx} must be a dictionary.")

            s_id = str(s.get("sample_id", "")).strip()
            if not s_id:
                raise ManifestValidationError(f"Sample at index {idx} missing 'sample_id'.")

            if s_id in seen_ids:
                duplicate_ids.append(s_id)
            seen_ids.add(s_id)

            # Age validation
            if "age" in s and s["age"] is not None:
                try:
                    float(s["age"])
                    samples_with_age += 1
                except (ValueError, TypeError):
                    pass

            # File existence checks
            for key, val in s.items():
                if key.endswith("_file") or key in ("methylation_file", "transcriptome_file", "clinical_file", "file"):
                    f_path = Path(val)
                    if not f_path.is_absolute():
                        f_path = (base_path / f_path).resolve()
                    if not f_path.exists():
                        missing_files.append(f"{s_id} -> {val}")

                    if "meth" in key:
                        detected_modalities.add("DNA Methylation")
                    elif "trans" in key or "rna" in key:
                        detected_modalities.add("Transcriptomics")
                    elif "prot" in key:
                        detected_modalities.add("Proteomics")
                    elif "metab" in key:
                        detected_modalities.add("Metabolomics")
                    elif "clin" in key:
                        detected_modalities.add("Clinical")

        warnings = []
        if duplicate_ids:
            raise ManifestValidationError(f"Duplicate sample IDs detected: {duplicate_ids[:5]}")

        if missing_files:
            raise ManifestValidationError(f"Manifest references non-existent files: {missing_files[:5]}")

        if samples_with_age < len(samples):
            warnings.append(
                f"Only {samples_with_age}/{len(samples)} samples contain chronological age metadata."
            )

        return {
            "valid": True,
            "total_samples": len(samples),
            "samples_with_age": samples_with_age,
            "detected_modalities": sorted(list(detected_modalities)),
            "warnings": warnings,
        }

    @classmethod
    def assemble_dataset(
        cls,
        manifest_path: Path,
        output_csv_path: Path,
    ) -> Tuple[Path, Dict[str, Any]]:
        """
        Loads validated manifest, combines sample-level annotations or rows,
        and produces a unified multi-omics matrix for BioAge-X.
        """
        manifest = cls.load_manifest(manifest_path)
        base_dir = manifest_path.parent
        validation = cls.validate_manifest(manifest, base_dir=base_dir)

        samples = manifest["samples"]
        records = []

        # If samples directly provide tabular data or file rows
        for s in samples:
            rec = {"sample_id": s["sample_id"]}
            if "age" in s and s["age"] is not None:
                rec["chronological_age"] = float(s["age"])

            # Copy additional clinical metadata if present
            for k, v in s.items():
                if k not in ("sample_id", "age") and not k.endswith("_file"):
                    rec[k] = v

            # If sample points to dedicated single-sample feature files
            for k, v in s.items():
                if k.endswith("_file") and Path(v).exists():
                    f_path = Path(v)
                    try:
                        f_df = pd.read_csv(f_path)
                        # If single row
                        if len(f_df) == 1:
                            for col in f_df.columns:
                                if col not in ("sample_id", "chronological_age"):
                                    rec[col] = f_df[col].iloc[0]
                    except Exception:
                        pass

            records.append(rec)

        df_out = pd.DataFrame(records)
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(output_csv_path, index=False)

        return output_csv_path, {
            "n_samples": len(df_out),
            "n_features": df_out.shape[1],
            "manifest_source": manifest.get("source", {}),
            "validation": validation,
        }
