"""
Pydantic Request and Response Schemas for BioAge-X REST API.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class DatasetProfileSchema(BaseModel):
    n_samples: int
    n_features: int
    orientation: str
    missing_fraction: float
    duplicate_features: int
    duplicate_samples: int
    sample_id_column: Optional[str] = None
    age_column: Optional[str] = None
    detected_modality: str
    numeric_feature_count: int
    metadata_columns: List[str] = []
    feature_id_sample: List[str] = []
    sample_id_sample: List[str] = []
    suspicious_columns: List[str] = []
    warnings: List[str] = []


class DatasetResponseSchema(BaseModel):
    id: str
    name: str
    format: str
    n_samples: int
    n_features: int
    orientation: str
    missing_fraction: float
    age_column: Optional[str] = None
    detected_modality: str
    profile: Optional[Dict[str, Any]] = None
    created_at: str


class PreprocessingConfigSchema(BaseModel):
    modality: str = "methylation"  # "methylation", "transcriptomics", "multimodal"
    imputation_strategy: str = "median"
    min_variance: float = 0.001
    standardize: bool = False
    max_features: int = 40
    feature_selection_method: str = "mutual_info"  # "mutual_info", "model_based", "variance_only"


class AnalysisCreateRequest(BaseModel):
    dataset_id: str
    config: PreprocessingConfigSchema = Field(default_factory=PreprocessingConfigSchema)


class AnalysisResponseSchema(BaseModel):
    id: str
    dataset_id: str
    status: str
    modality: str
    selected_features: List[str] = []
    provenance: Optional[Dict[str, Any]] = None
    created_at: str


class ModelTrainRequest(BaseModel):
    dataset_id: str
    analysis_id: Optional[str] = None
    model_type: str = "XGBoost"  # "ElasticNet", "RandomForest", "XGBoost", "EarlyFusion", "LateFusion", "WeightedEnsemble"
    hyperparameters: Optional[Dict[str, Any]] = None


class ModelResponseSchema(BaseModel):
    id: str
    name: str
    model_type: str
    dataset_id: str
    mae: Optional[float] = None
    rmse: Optional[float] = None
    r2: Optional[float] = None
    pearson_r: Optional[float] = None
    spearman_rho: Optional[float] = None
    n_features: int
    training_time_sec: float
    feature_importance: Optional[Dict[str, float]] = None
    created_at: str


class ExplainRequest(BaseModel):
    model_id: str
    dataset_id: str
    top_k: int = 15
    sample_idx: int = 0


class ExplainResponseSchema(BaseModel):
    model_id: str
    global_biomarkers: List[Dict[str, Any]]
    beeswarm_sample: List[Dict[str, Any]]
    waterfall_sample: Dict[str, Any]


class NetworkBuildRequest(BaseModel):
    biomarkers: List[str] = []
    include_pathways: bool = True
    edge_list_name: Optional[str] = None
    network_source: str = "hybrid"  # "hybrid", "string", "local"
    min_confidence: float = 0.400
    species: int = 9606


class NetworkResponseSchema(BaseModel):
    elements: Dict[str, List[Dict[str, Any]]]
    summary: Dict[str, Any]
    centrality_top_nodes: List[Dict[str, Any]] = []


class GNNTrainRequest(BaseModel):
    architecture: str = "GCN"  # "GCN", "GraphSAGE", "GAT"
    epochs: int = 40
    lr: float = 0.01
    biomarkers: List[str] = []


class GNNResponseSchema(BaseModel):
    model_architecture: str
    test_mse: float
    test_mae: float
    test_r2: float
    top_predicted_nodes: List[Dict[str, Any]]
    disclaimer: str


class PathwayEnrichmentRequest(BaseModel):
    query_genes: List[str] = []
    fdr_threshold: float = 0.10
    pathway_source: str = "reactome"  # "reactome", "hallmarks", "combined"
    species: str = "homo_sapiens"


class PathwayEnrichmentResponse(BaseModel):
    pathways: List[Dict[str, Any]]
    query_gene_count: int
    source_attribution: str = "Reactome Analysis Service & Hallmark Knowledge Base"


# =============================================================================
# INTEGRATIONS SCHEMAS
# =============================================================================

class ResolveGenesRequest(BaseModel):
    identifiers: List[str]
    species: str = "homo_sapiens"


class ResolveGenesResponse(BaseModel):
    resolved: List[Dict[str, Any]]
    total_count: int
    ambiguous_count: int
    provenance_summary: Dict[str, Any] = {}


class StringNetworkRequest(BaseModel):
    genes: List[str]
    min_score: float = 0.400
    species: int = 9606
    network_source: str = "hybrid"  # "hybrid", "string", "local"


class ReactomePathwaysRequest(BaseModel):
    genes: List[str]
    species: str = "homo_sapiens"
    fdr_threshold: float = 0.10
    pathway_source: str = "reactome"  # "reactome", "hallmarks", "combined"


class EnsemblAnnotateRequest(BaseModel):
    symbols: List[str]
    species: str = "homo_sapiens"


class GeoImportRequest(BaseModel):
    accession: str


class IntegrationsHealthResponse(BaseModel):
    string: str
    reactome: str
    ensembl: str
    ncbi: str
    details: Dict[str, Any]
    cache: Dict[str, Any]



class ReportGenerateRequest(BaseModel):
    dataset_id: str
    model_id: str
    experiment_name: Optional[str] = None


class ReportResponseSchema(BaseModel):
    experiment_id: str
    reproducibility_hash: str
    pdf_url: Optional[str] = None
    report_data: Dict[str, Any]


class ExperimentResponseSchema(BaseModel):
    id: str
    name: str
    dataset_id: str
    model_id: str
    model_type: str
    metrics: Dict[str, Any]
    acceleration_summary: Dict[str, Any]
    pdf_url: Optional[str] = None
    created_at: str
