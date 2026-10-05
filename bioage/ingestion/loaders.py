"""
Dataset Loaders for BioAge-X.
Supports CSV, TSV, Parquet, and H5AD formats with robust schema handling and error management.
"""

from pathlib import Path
from typing import Tuple, Optional
import pandas as pd

from bioage.ingestion.profiler import DatasetProfiler, DatasetProfile
from bioage.utils.logger import get_logger

logger = get_logger("bioage.ingestion.loaders")


class DatasetLoader:
    """Loads multi-omics datasets from disk with format auto-detection."""

    SUPPORTED_EXTENSIONS = {".csv", ".tsv", ".txt", ".parquet", ".pq", ".h5ad"}

    def __init__(self, profiler: Optional[DatasetProfiler] = None):
        self.profiler = profiler or DatasetProfiler()

    def load_file(
        self,
        file_path: str | Path,
        assumed_orientation: Optional[str] = None
    ) -> Tuple[pd.DataFrame, DatasetProfile]:
        """Loads a file from path, profiles it, and returns the standardized DataFrame and Profile."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format '{ext}'. Supported formats: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        logger.info(f"Loading dataset from: {path.name} (format: {ext})")

        if ext in {".csv", ".txt"}:
            # Try comma first, fallback to tab if only 1 column parsed
            df = pd.read_csv(path)
            if df.shape[1] == 1:
                df = pd.read_csv(path, sep="\t")
        elif ext == ".tsv":
            df = pd.read_csv(path, sep="\t")
        elif ext in {".parquet", ".pq"}:
            df = pd.read_parquet(path)
        elif ext == ".h5ad":
            df = self._load_h5ad(path)
        else:
            raise ValueError(f"Unhandled file extension: {ext}")

        standardized_df, profile = self.profiler.profile_dataframe(
            df, assumed_orientation=assumed_orientation
        )
        return standardized_df, profile

    def _load_h5ad(self, path: Path) -> pd.DataFrame:
        """Loads AnnData H5AD file into a pandas DataFrame."""
        try:
            import anndata as ad
            adata = ad.read_h5ad(path)
            # Combine X and obs (sample metadata)
            if hasattr(adata.X, "toarray"):
                x_mat = adata.X.toarray()
            else:
                x_mat = adata.X
            
            var_names = list(adata.var_names)
            obs_names = list(adata.obs_names)
            df = pd.DataFrame(x_mat, index=obs_names, columns=var_names)
            
            # Append obs metadata columns (e.g. age, sex)
            for col in adata.obs.columns:
                df[f"meta_{col}"] = adata.obs[col].values
            return df
        except ImportError:
            raise ImportError(
                "anndata library is required to load .h5ad files. Install with 'pip install anndata'."
            )
