"""
Script to generate demo multi-omics cohorts and network edges for BioAge-X.
Outputs sample files to data/example/
"""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from bioage.utils.synthetic_data import SyntheticMultiOmicsGenerator
from bioage.network.interaction_graph import BiologicalInteractionGraph
from bioage.utils.logger import get_logger

logger = get_logger("scripts.generate_demo_data")


def main():
    example_dir = root_dir / "data" / "example"
    example_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate synthetic cohort
    generator = SyntheticMultiOmicsGenerator(n_samples=150, n_cpg_probes=120, n_genes=150, random_seed=42)
    df_combined, df_meth, df_trans = generator.generate_cohort()

    combined_path = example_dir / "demo_multiomics.csv"
    meth_path = example_dir / "demo_methylation.csv"
    trans_path = example_dir / "demo_transcriptomics.csv"
    clinical_path = example_dir / "demo_clinical.csv"

    df_combined.to_csv(combined_path, index=True)
    df_meth.to_csv(meth_path, index=True)
    df_trans.to_csv(trans_path, index=True)

    clinical_cols = ["sample_id", "chronological_age", "sex", "smoking_status", "bmi", "true_age_acceleration", "data_provenance"]
    df_combined[clinical_cols].to_csv(clinical_path, index=False)

    logger.info(f"Saved demo datasets to {example_dir}")

    # 2. Save canonical interaction edges
    graph_builder = BiologicalInteractionGraph()
    df_edges = graph_builder._load_edge_list(None)
    edges_path = example_dir / "aging_network_edges.csv"
    df_edges.to_csv(edges_path, index=False)
    logger.info(f"Saved canonical network edges to {edges_path}")

    print("Demo data generation complete!")


if __name__ == "__main__":
    main()
