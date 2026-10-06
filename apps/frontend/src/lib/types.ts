export interface DatasetProfile {
  n_samples: number;
  n_features: number;
  orientation: string;
  missing_fraction: number;
  duplicate_features: number;
  duplicate_samples: number;
  sample_id_column?: string | null;
  age_column?: string | null;
  detected_modality: string;
  numeric_feature_count: number;
  metadata_columns: string[];
  feature_id_sample: string[];
  sample_id_sample: string[];
  suspicious_columns: string[];
  warnings: string[];
}

export interface Dataset {
  id: string;
  name: string;
  format: string;
  n_samples: number;
  n_features: number;
  orientation: string;
  missing_fraction: number;
  age_column?: string | null;
  detected_modality: string;
  profile?: DatasetProfile | null;
  created_at: string;
}

export interface ModelMetrics {
  mae: number;
  rmse: number;
  r2: number;
  pearson_r: number;
  pearson_pvalue?: number;
  spearman_rho: number;
  spearman_pvalue?: number;
  n_features: number;
  training_time_sec: number;
  sample_count?: number;
}

export interface Model {
  id: string;
  name: string;
  model_type: string;
  dataset_id: string;
  mae?: number;
  rmse?: number;
  r2?: number;
  pearson_r?: number;
  spearman_rho?: number;
  n_features: number;
  training_time_sec: number;
  feature_importance?: Record<string, number>;
  created_at: string;
}

export interface AgeAccelerationSummary {
  mean_acceleration: number;
  median_acceleration: number;
  std_acceleration: number;
  min_acceleration: number;
  max_acceleration: number;
  accelerated_count: number;
  decelerated_count: number;
  synchronous_count: number;
  disclaimer: string;
  stratified_stats?: Record<string, Record<string, { count: number; mean_accel: number; std_accel: number }>>;
}

export interface SamplePrediction {
  sample_id: string;
  chronological_age: number;
  predicted_bio_age: number;
  age_acceleration: number;
  acceleration_status: "Accelerated" | "Decelerated" | "Synchronous";
  sex?: string;
  smoking_status?: string;
  bmi?: number;
}

export interface ShapBiomarker {
  feature: string;
  gene_symbol: string;
  mean_abs_shap: number;
  direction: "accelerates_age" | "decelerates_age";
  biological_role: string;
}

export interface BeeswarmPoint {
  feature: string;
  sample_id: string;
  raw_value: number;
  normalized_value: number;
  shap_value: number;
}

export interface WaterfallContribution {
  feature: string;
  gene_symbol: string;
  raw_value: number;
  shap_value: number;
  impact: string;
  biological_role: string;
}

export interface WaterfallExplanation {
  sample_id: string;
  base_value: number;
  predicted_biological_age: number;
  contributions: WaterfallContribution[];
}

export interface PathwayEnrichment {
  pathway_id: string;
  pathway_name: string;
  category: string;
  description?: string;
  pathway_size: number;
  overlap_count: number;
  overlapping_genes: string[];
  p_value: number;
  odds_ratio: number;
  fdr_adjusted_p: number;
  enrichment_score?: number;
  source?: string;
  status?: string;
  provider_version?: string;
}

export interface CytoscapeNode {
  data: {
    id: string;
    label: string;
    node_type: string;
    is_biomarker?: boolean;
    degree?: number;
    betweenness?: number;
    pagerank?: number;
    community_id?: number;
    category?: string;
  };
}

export interface CytoscapeEdge {
  data: {
    id: string;
    source: string;
    target: string;
    edge_type: string;
    weight: number;
    provider?: string;
    status?: string;
    evidence_scores?: Record<string, number>;
  };
}

export interface NetworkData {
  elements: {
    nodes: CytoscapeNode[];
    edges: CytoscapeEdge[];
  };
  summary: {
    n_nodes: number;
    n_edges: number;
    n_communities: number;
    connected_components: number;
    density?: number;
    network_source?: string;
    knowledge_status?: string;
    source_breakdown?: Record<string, number>;
  };
  centrality_top_nodes: Array<{
    node_id: string;
    degree: number;
    degree_centrality: number;
    betweenness_centrality: number;
    pagerank: number;
    community_id: number;
  }>;
}

export interface GNNResult {
  model_architecture: string;
  test_mse: number;
  test_mae: number;
  test_r2: number;
  top_predicted_nodes: Array<{
    node_id: string;
    predicted_score: number;
    true_score: number;
    is_biomarker: boolean;
  }>;
  disclaimer: string;
}

export interface Experiment {
  id: string;
  name: string;
  dataset_id: string;
  model_id: string;
  model_type: string;
  metrics: ModelMetrics;
  acceleration_summary: AgeAccelerationSummary;
  pdf_url?: string;
  created_at: string;
}

export interface DataSourceSummary {
  repository: string;
  category: string;
  description: string;
  search_supported: boolean;
  download_supported: boolean;
  auto_ingest: string;
  access_type: string;
  supported_accessions: string[];
}

export interface DatasetSearchResult {
  accession: string;
  title: string;
  repository: string;
  modality: string;
  organism: string;
  sample_count: number;
  platform?: string;
  citation?: string;
  has_processed_matrix: boolean;
  requires_preprocessing: boolean;
  access_restricted: boolean;
  download_url?: string;
  compatibility_tier?: string;
}

export interface DownloadOption {
  id: string;
  label: string;
  url: string;
  format: string;
  size_bytes?: number;
  requires_preprocessing?: boolean;
  access_restricted?: boolean;
}

export interface DatasetMetadata {
  accession: string;
  repository: string;
  title: string;
  organism: string;
  description: string;
  sample_count: number;
  download_options: DownloadOption[];
  citation?: string;
  compatibility_status?: string;
  license?: string;
}

export interface DownloadJob {
  job_id: string;
  task_type: string;
  status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | "CANCELLED";
  progress: number;
  status_message: string;
  started_at?: string;
  completed_at?: string;
  error?: string;
  downloaded_bytes?: number;
  total_bytes?: number;
  speed_bytes_sec?: number;
  result_data?: any;
}

export interface ClockCompatibilityResult {
  dataset_id: string;
  dataset_name: string;
  dataset_summary: {
    total_features: number;
    total_samples: number;
    detected_cpg_probes: number;
    detected_genes: number;
    evaluated_modality: string;
  };
  clocks: Record<string, {
    clock_name: string;
    generation: string;
    status: "FULL_COVERAGE" | "PARTIAL_COVERAGE" | "UNAVAILABLE" | "NOT_APPLICABLE";
    coverage_pct: number;
    required_count: number;
    available_count: number;
    missing_count: number;
    reason: string;
    required_inputs?: string[];
    citation?: string;
  }>;
}

export interface AIStatus {
  enabled: boolean;
  configured: boolean;
  model: string;
  status: string;
  message: string;
}

export interface AIInterpretation {
  status: string;
  task_type: string;
  summary: string;
  observations: string[];
  hypotheses: string[];
  limitations: string[];
  evidence_sources: string[];
  disclaimer: string;
  model_used?: string;
  cached?: boolean;
  latency_ms?: number;
}

