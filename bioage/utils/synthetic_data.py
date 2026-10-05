"""
Synthetic Multi-Omics Dataset Generator for BioAge-X.
Generates realistic biological aging datasets combining DNA methylation, transcriptomics,
and clinical phenotypic covariates with latent biological aging acceleration signals.

DISCLAIMER:
THIS DATASET IS CLEARLY LABELED AS DEMO / SYNTHETIC DATA FOR EDUCATIONAL
AND SOFTWARE BENCHMARKING PURPOSES ONLY. DO NOT DRAW CLINICAL INFERENCES.
"""

from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd

from bioage.utils.logger import get_logger

logger = get_logger("bioage.utils.synthetic_data")

# Canonical aging biomarkers from literature (Horvath / Hannum / Senescence / Inflammaging)
CANONICAL_CPGS = [
    ("cg16867657", "ELOVL2", 0.75),   # Strong positive correlation with age
    ("cg06639320", "FHL2", 0.68),     # Positive correlation
    ("cg19283806", "CCDC102B", 0.62), # Positive
    ("cg24724428", "PENK", 0.58),     # Positive
    ("cg09809672", "EDARADD", 0.54),  # Positive
    ("cg22736354", "NHLRC1", 0.49),   # Positive
    ("cg02233190", "GSTP1", -0.55),   # Negative correlation (hypomethylation)
    ("cg10501210", "TRIM59", 0.60),
    ("cg04474832", "MYOD1", -0.48),
    ("cg19722847", "KLF14", 0.52),
    ("cg01820374", "OTUD7A", -0.42),
    ("cg21572722", "KIAA0415", 0.46),
    ("cg07553761", "TRIM58", 0.51),
    ("cg18478117", "SST", 0.44),
    ("cg14424579", "ASPA", -0.50),
]

CANONICAL_GENES = [
    ("CDKN2A", 0.65),   # p16(INK4a), cellular senescence biomarker
    ("IL6", 0.58),      # Inflammaging cytokine
    ("TNF", 0.52),      # Pro-inflammatory cytokine
    ("SIRT1", -0.62),   # Longevity sirtuin (expression declines with age)
    ("FOXO3", -0.48),   # Longevity transcription factor (declines)
    ("MTOR", 0.45),     # Nutrient-sensing mTOR signaling
    ("TP53", 0.42),     # DNA damage checkpoint
    ("CDKN1A", 0.55),   # p21(CIP1) senescence marker
    ("TERT", -0.54),    # Telomerase reverse transcriptase (declines)
    ("SOD2", -0.40),    # Mitochondrial antioxidant (declines)
    ("CXCL8", 0.49),    # SASP chemokine
    ("GDF15", 0.61),    # Systemic aging biomarker
    ("APOE", 0.38),     # Lipid/neuro-aging marker
    ("IGF1", -0.46),    # Somatotrophic axis decline
    ("KLOTHO", -0.59),  # Anti-aging hormone
]


class SyntheticMultiOmicsGenerator:
    """Generates synthetic multi-omics cohorts with controllable age dynamics."""

    def __init__(
        self,
        n_samples: int = 150,
        n_cpg_probes: int = 120,
        n_genes: int = 150,
        random_seed: int = 42,
    ):
        self.n_samples = n_samples
        self.n_cpg_probes = n_cpg_probes
        self.n_genes = n_genes
        self.random_seed = random_seed
        self.rng = np.random.default_rng(random_seed)

    def generate_cohort(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Generates:
        1. Combined multi-omics dataset (ready for pipeline upload)
        2. Clean methylation beta matrix
        3. Clean transcriptomic count/log expression matrix
        """
        logger.info(f"Generating synthetic cohort: {self.n_samples} samples, {self.n_cpg_probes} CpGs, {self.n_genes} genes")

        # 1. Sample IDs & Chronological Age (20 to 85 years)
        sample_ids = [f"BIOAGE_SYNTH_{i+1:03d}" for i in range(self.n_samples)]
        chronological_age = self.rng.uniform(20.0, 85.0, size=self.n_samples)
        # Normalize age to [0, 1] for signal generation
        age_norm = (chronological_age - 20.0) / 65.0

        # Phenotypic covariates
        sex = self.rng.choice(["Female", "Male"], size=self.n_samples, p=[0.52, 0.48])
        smoking = self.rng.choice(["Never", "Former", "Current"], size=self.n_samples, p=[0.55, 0.28, 0.17])
        bmi = self.rng.normal(26.5, 4.2, size=self.n_samples).clip(18.5, 38.0)

        # True latent biological age acceleration
        # Smoking adds ~2.5 years, high BMI adds ~1.5 years, plus random biologic variance
        smoking_effect = np.where(smoking == "Current", 2.8, np.where(smoking == "Former", 0.9, 0.0))
        bmi_effect = ((bmi - 25.0).clip(0, None) / 10.0) * 1.8
        biologic_noise = self.rng.normal(0.0, 2.5, size=self.n_samples)
        latent_age_acceleration = smoking_effect + bmi_effect + biologic_noise
        latent_bio_age = chronological_age + latent_age_acceleration
        bio_age_norm = (latent_bio_age - 20.0) / 65.0

        # 2. DNA Methylation Matrix (Beta values in [0.0, 1.0])
        meth_data: Dict[str, np.ndarray] = {}

        # Add canonical aging CpGs
        for cpg_id, gene_name, correlation in CANONICAL_CPGS:
            base_beta = self.rng.uniform(0.2, 0.7)
            # Modulate by biological age signal
            signal = correlation * (bio_age_norm - 0.5) * 0.4
            noise = self.rng.normal(0, 0.06, size=self.n_samples)
            beta_values = np.clip(base_beta + signal + noise, 0.01, 0.99)
            meth_data[f"{cpg_id}_{gene_name}"] = np.round(beta_values, 4)

        # Fill remaining CpGs with background biological noise / low correlation
        remaining_cpgs = self.n_cpg_probes - len(CANONICAL_CPGS)
        for i in range(remaining_cpgs):
            probe_id = f"cg{90000000 + i:08d}"
            base_beta = self.rng.uniform(0.1, 0.85)
            weak_corr = self.rng.normal(0.0, 0.12)
            signal = weak_corr * (age_norm - 0.5) * 0.2
            noise = self.rng.normal(0, 0.05, size=self.n_samples)
            meth_data[probe_id] = np.round(np.clip(base_beta + signal + noise, 0.01, 0.99), 4)

        df_meth = pd.DataFrame(meth_data, index=sample_ids)

        # 3. Transcriptomics Matrix (log2 normalized expression)
        trans_data: Dict[str, np.ndarray] = {}

        # Add canonical aging genes
        for gene_symbol, correlation in CANONICAL_GENES:
            base_expr = self.rng.uniform(4.0, 10.0)
            signal = correlation * (bio_age_norm - 0.5) * 3.0
            noise = self.rng.normal(0, 0.6, size=self.n_samples)
            expr_values = np.clip(base_expr + signal + noise, 0.0, 16.0)
            trans_data[f"GENE_{gene_symbol}"] = np.round(expr_values, 3)

        # Fill remaining genes
        remaining_genes = self.n_genes - len(CANONICAL_GENES)
        for i in range(remaining_genes):
            gene_name = f"GENE_TRANS_{i+1:03d}"
            base_expr = self.rng.uniform(1.0, 11.0)
            weak_corr = self.rng.normal(0.0, 0.15)
            signal = weak_corr * (age_norm - 0.5) * 1.5
            noise = self.rng.normal(0, 0.8, size=self.n_samples)
            trans_data[gene_name] = np.round(np.clip(base_expr + signal + noise, 0.0, 16.0), 3)

        df_trans = pd.DataFrame(trans_data, index=sample_ids)

        # 4. Clinical Metadata DataFrame
        df_clinical = pd.DataFrame({
            "sample_id": sample_ids,
            "chronological_age": np.round(chronological_age, 1),
            "sex": sex,
            "smoking_status": smoking,
            "bmi": np.round(bmi, 1),
            "true_age_acceleration": np.round(latent_age_acceleration, 2),
            "data_provenance": "DEMO_SYNTHETIC_DATA",
        }, index=sample_ids)

        # 5. Combined Multi-Omics Dataset
        df_combined = pd.concat([df_clinical, df_meth, df_trans], axis=1)

        logger.info(
            f"Synthesized cohort complete. Samples: {self.n_samples}, "
            f"Mean Chronological Age: {chronological_age.mean():.1f} yrs"
        )
        return df_combined, df_meth, df_trans
