"""
Biomarker Discovery & Biomarker-to-Biology Bridge for BioAge-X.

Transitions Phase 1 molecular features discovered through SHAP and model importance
into annotated biological entities ready for Phase 2 GraphOmics-AI network construction.

SCIENTIFIC TERMINOLOGY & DISCLAIMER:
Features identified by computational models are classified as 'Candidate Aging-Associated Features'
or 'Model-Associated Biomarkers'. They represent statistical and machine-learning associations,
NOT experimentally validated causal drivers or diagnostic criteria without independent clinical proof.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
import re

from bioage.pathways.database import PATHWAY_KNOWLEDGE_BASE
from bioage.utils.logger import get_logger

logger = get_logger("bioage.explainability.biomarker_bridge")

# Knowledge base mapping canonical CpGs to genes and functional annotations
CPG_GENE_ANNOTATIONS: Dict[str, Dict[str, str]] = {
    "cg16867657": {
        "gene": "ELOVL2",
        "protein": "Elongation of very long chain fatty acids protein 2",
        "chromosome": "Chr 6",
        "feature_type": "CpG Island / Promoter",
        "biological_role": "Lipid metabolism and polyunsaturated fatty acid elongation; landmark epigenetic aging marker.",
        "pathway_id": "PW_EPIGENETIC",
    },
    "cg06639320": {
        "gene": "FHL2",
        "protein": "Four and a half LIM domains protein 2",
        "chromosome": "Chr 2",
        "feature_type": "5' UTR / CpG Island",
        "biological_role": "Scaffolding transcriptional cofactor implicated in focal adhesion and senescence signaling.",
        "pathway_id": "PW_EPIGENETIC",
    },
    "cg19283806": {
        "gene": "CCDC102B",
        "protein": "Coiled-coil domain-containing protein 102B",
        "chromosome": "Chr 18",
        "feature_type": "Gene Body",
        "biological_role": "Centrosomal and cytoskeletal architecture regulator associated with chronological age.",
        "pathway_id": "PW_EPIGENETIC",
    },
    "cg24724428": {
        "gene": "PENK",
        "protein": "Proenkephalin",
        "chromosome": "Chr 8",
        "feature_type": "Exon 1",
        "biological_role": "Neuropeptide precursor; differential methylation tracked in brain and blood aging.",
        "pathway_id": "PW_EPIGENETIC",
    },
    "cg09809672": {
        "gene": "EDARADD",
        "protein": "EDAR-associated death domain protein",
        "chromosome": "Chr 1",
        "feature_type": "Promoter",
        "biological_role": "Ectodysplasin receptor adapter modulating NF-kB and apoptotic signaling.",
        "pathway_id": "PW_EPIGENETIC",
    },
    "cg22736354": {
        "gene": "NHLRC1",
        "protein": "NHL repeat-containing protein 1",
        "chromosome": "Chr 6",
        "feature_type": "CpG Island",
        "biological_role": "E3 ubiquitin-protein ligase mediating proteasomal degradation and glycogen metabolism.",
        "pathway_id": "PW_PROTEOSTASIS",
    },
    "cg02233190": {
        "gene": "GSTP1",
        "protein": "Glutathione S-transferase P",
        "chromosome": "Chr 11",
        "feature_type": "Promoter",
        "biological_role": "Phase II xenobiotic detoxification and oxidative stress defense; hypomethylated in aging.",
        "pathway_id": "PW_MITOCHONDRIAL",
    },
    "cg10501210": {
        "gene": "TRIM59",
        "protein": "Tripartite motif-containing protein 59",
        "chromosome": "Chr 3",
        "feature_type": "CpG Island / Exon",
        "biological_role": "Innate immunity and ubiquitin transfer modulating cellular proliferation and senescence.",
        "pathway_id": "PW_SENESCENCE",
    },
    "cg04474832": {
        "gene": "MYOD1",
        "protein": "Myoblast determination protein 1",
        "chromosome": "Chr 11",
        "feature_type": "Promoter / Enhancer",
        "biological_role": "Myogenic regulatory transcription factor implicated in age-associated sarcopenia.",
        "pathway_id": "PW_EPIGENETIC",
    },
    "cg19722847": {
        "gene": "KLF14",
        "protein": "Krueppel-like factor 14",
        "chromosome": "Chr 7",
        "feature_type": "CpG Island",
        "biological_role": "Master transcriptional regulator of adipose gene expression and metabolic aging.",
        "pathway_id": "PW_NUTRIENT_SENSING",
    },
    "cg01820374": {
        "gene": "OTUD7A",
        "protein": "OTU domain-containing protein 7A",
        "chromosome": "Chr 15",
        "feature_type": "Promoter",
        "biological_role": "Deubiquitinating enzyme regulating synaptic protein stability and neuro-aging.",
        "pathway_id": "PW_PROTEOSTASIS",
    },
    "cg21572722": {
        "gene": "KIAA0415",
        "protein": "AP-5 complex subunit zeta-1",
        "chromosome": "Chr 14",
        "feature_type": "Exon",
        "biological_role": "Endosomal and autophagic trafficking component implicated in hereditary spastic paraplegia.",
        "pathway_id": "PW_PROTEOSTASIS",
    },
    "cg07553761": {
        "gene": "TRIM58",
        "protein": "Tripartite motif-containing protein 58",
        "chromosome": "Chr 1",
        "feature_type": "CpG Island",
        "biological_role": "E3 ubiquitin ligase required for terminal erythroid maturation and cell cycle progression.",
        "pathway_id": "PW_PROTEOSTASIS",
    },
    "cg18478117": {
        "gene": "SST",
        "protein": "Somatostatin",
        "chromosome": "Chr 3",
        "feature_type": "Promoter",
        "biological_role": "Endocrine somatotrophic axis inhibitor; hypermethylated in chronological aging cohorts.",
        "pathway_id": "PW_NUTRIENT_SENSING",
    },
    "cg14424579": {
        "gene": "ASPA",
        "protein": "Aspartoacylase",
        "chromosome": "Chr 17",
        "feature_type": "Promoter",
        "biological_role": "Hydrolyzes N-acetylaspartate for lipid synthesis and myelin integrity.",
        "pathway_id": "PW_NUTRIENT_SENSING",
    },
}

# Transcriptomic and protein annotation dictionary
GENE_ANNOTATIONS: Dict[str, Dict[str, str]] = {
    "CDKN2A": {
        "gene": "CDKN2A",
        "protein": "Cyclin-dependent kinase inhibitor 2A (p16INK4a)",
        "chromosome": "Chr 9",
        "feature_type": "Transcript / Protein",
        "biological_role": "Pivotal tumor suppressor and gold-standard biomarker of cellular senescence.",
        "pathway_id": "PW_SENESCENCE",
    },
    "CDKN1A": {
        "gene": "CDKN1A",
        "protein": "Cyclin-dependent kinase inhibitor 1A (p21CIP1)",
        "chromosome": "Chr 6",
        "feature_type": "Transcript / Protein",
        "biological_role": "p53-inducible cell cycle arrest effector executing acute senescence entry.",
        "pathway_id": "PW_SENESCENCE",
    },
    "IL6": {
        "gene": "IL6",
        "protein": "Interleukin-6",
        "chromosome": "Chr 7",
        "feature_type": "Secreted Cytokine (SASP)",
        "biological_role": "Pleiotropic pro-inflammatory cytokine driving systemic inflammaging.",
        "pathway_id": "PW_INFLAMMAGING",
    },
    "TNF": {
        "gene": "TNF",
        "protein": "Tumor necrosis factor-alpha",
        "chromosome": "Chr 6",
        "feature_type": "Cytokine",
        "biological_role": "Pro-inflammatory master regulator elevated in age-related chronic diseases.",
        "pathway_id": "PW_INFLAMMAGING",
    },
    "SIRT1": {
        "gene": "SIRT1",
        "protein": "NAD-dependent protein deacetylase sirtuin-1",
        "chromosome": "Chr 10",
        "feature_type": "Enzyme / Epigenetic",
        "biological_role": "Longevity factor de-acetylating histones, p53, and PGC-1alpha; expression declines with age.",
        "pathway_id": "PW_EPIGENETIC",
    },
    "FOXO3": {
        "gene": "FOXO3",
        "protein": "Forkhead box protein O3",
        "chromosome": "Chr 6",
        "feature_type": "Transcription Factor",
        "biological_role": "Centenarian longevity gene orchestrating antioxidant and DNA repair transcription.",
        "pathway_id": "PW_NUTRIENT_SENSING",
    },
    "MTOR": {
        "gene": "MTOR",
        "protein": "Mechanistic target of rapamycin",
        "chromosome": "Chr 1",
        "feature_type": "Kinase",
        "biological_role": "Central nutrient sensor; pharmacological inhibition by rapamycin extends lifespan.",
        "pathway_id": "PW_NUTRIENT_SENSING",
    },
    "TP53": {
        "gene": "TP53",
        "protein": "Cellular tumor antigen p53",
        "chromosome": "Chr 17",
        "feature_type": "Transcription Factor",
        "biological_role": "Guardian of the genome coordinating DNA damage response and senescent checkpoints.",
        "pathway_id": "PW_DNA_REPAIR",
    },
    "TERT": {
        "gene": "TERT",
        "protein": "Telomerase reverse transcriptase",
        "chromosome": "Chr 5",
        "feature_type": "Ribonucleoprotein catalytic subunit",
        "biological_role": "Maintains telomeric repeat synthesis; transcriptional repression causes replicative exhaustion.",
        "pathway_id": "PW_TELOMERE",
    },
    "SOD2": {
        "gene": "SOD2",
        "protein": "Superoxide dismutase 2 (mitochondrial)",
        "chromosome": "Chr 6",
        "feature_type": "Antioxidant Enzyme",
        "biological_role": "Converts mitochondrial superoxide radicals to hydrogen peroxide; defends against oxidative decline.",
        "pathway_id": "PW_MITOCHONDRIAL",
    },
    "CXCL8": {
        "gene": "CXCL8",
        "protein": "Interleukin-8",
        "chromosome": "Chr 4",
        "feature_type": "Chemokine (SASP)",
        "biological_role": "Neutrophil-recruiting chemokine secreted at high levels by senescent cells.",
        "pathway_id": "PW_SENESCENCE",
    },
    "GDF15": {
        "gene": "GDF15",
        "protein": "Growth differentiation factor 15",
        "chromosome": "Chr 19",
        "feature_type": "Circulating Biomarker",
        "biological_role": "Mitochondrial stress and systemic allostatic load biomarker elevated in human aging.",
        "pathway_id": "PW_MITOCHONDRIAL",
    },
    "APOE": {
        "gene": "APOE",
        "protein": "Apolipoprotein E",
        "chromosome": "Chr 19",
        "feature_type": "Apolipoprotein",
        "biological_role": "Lipid metabolism and neurovascular integrity; epsilon 4 allele correlates with accelerated brain aging.",
        "pathway_id": "PW_NUTRIENT_SENSING",
    },
    "IGF1": {
        "gene": "IGF1",
        "protein": "Insulin-like growth factor 1",
        "chromosome": "Chr 12",
        "feature_type": "Growth Factor",
        "biological_role": "Somatotrophic axis signaling; reduced signaling correlates with extended animal longevity.",
        "pathway_id": "PW_NUTRIENT_SENSING",
    },
    "KLOTHO": {
        "gene": "KLOTHO",
        "protein": "Klotho peptide",
        "chromosome": "Chr 13",
        "feature_type": "Anti-Aging Hormone",
        "biological_role": "Circulating anti-aging factor repressing insulin/IGF-1 signaling and phosphate toxicity.",
        "pathway_id": "PW_NUTRIENT_SENSING",
    },
}


@dataclass
class CandidateBiomarker:
    """Represents a model-important molecular feature annotated for biological research."""
    feature_id: str
    modality: str
    scientific_term: str  # 'Candidate Aging-Associated Feature'
    mean_abs_shap: float
    importance_rank: int
    direction: str        # 'Accelerates Predicted Age (+)' or 'Decelerates Predicted Age (-)'
    gene_symbol: Optional[str] = None
    protein_name: Optional[str] = None
    pathway_name: Optional[str] = None
    pathway_id: Optional[str] = None
    biological_role: Optional[str] = None
    chromosome: Optional[str] = None
    feature_type: Optional[str] = None
    validation_status: str = "Computational Candidate (Requires Experimental Validation)"
    ensembl_gene_id: Optional[str] = None
    external_source: str = "Local Curated Knowledge"
    external_status: str = "LOCAL_FALLBACK"
    annotation_confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["mapped_gene"] = self.gene_symbol or "Unknown"
        d["importance"] = self.mean_abs_shap
        return d

    @property
    def mapped_gene(self) -> str:
        return self.gene_symbol or "Unknown"

    @property
    def importance(self) -> float:
        return self.mean_abs_shap


class BiomarkerToBiologyBridge:
    """
    Transforms Phase 1 SHAP/model importance rankings into annotated candidate biomarkers
    and produces the biological entities and seeds required for Phase 2 GraphOmics-AI.
    """

    def __init__(self):
        pass

    def annotate_feature(
        self,
        feature_id: str,
        importance_score: float,
        rank: int,
        shap_value: Optional[float] = None,
    ) -> CandidateBiomarker:
        """Annotates an individual feature using multi-omics knowledge base."""
        # Detect modality
        is_cpg = bool(re.match(r"^cg\d+", feature_id, re.IGNORECASE))
        is_covariate = feature_id.lower() in {"bmi", "sex", "smoking_status", "smoking", "pack_years"}

        if is_cpg:
            modality = "DNA Methylation"
            m = re.match(r"^(cg\d+)", feature_id, re.IGNORECASE)
            base_cpg = m.group(1).lower() if m else feature_id.lower()
            anno = CPG_GENE_ANNOTATIONS.get(base_cpg, None)

            # If annotated format cgXXXX_GENE
            gene = None
            if "_" in feature_id:
                parts = feature_id.split("_")
                if len(parts) > 1 and parts[1].isupper():
                    gene = parts[1]

            if anno:
                gene = gene or anno["gene"]
                protein = anno["protein"]
                bio_role = anno["biological_role"]
                pw_id = anno["pathway_id"]
                pw_name = PATHWAY_KNOWLEDGE_BASE.get(pw_id, {}).get("name", "Epigenetic Dynamics")
                chrom = anno["chromosome"]
                ftype = anno["feature_type"]
            else:
                protein = f"CpG Locus {feature_id}"
                bio_role = "Genomic DNA methylation site associated with age estimation model."
                pw_id = "PW_EPIGENETIC"
                pw_name = "Epigenetic Alterations"
                chrom = "Unannotated"
                ftype = "DNA Methylation Probe"
        elif is_covariate:
            modality = "Clinical Covariate"
            gene = None
            protein = None
            pw_id = "PW_INFLAMMAGING" if "smok" in feature_id.lower() else "PW_NUTRIENT_SENSING"
            pw_name = "Phenotypic / Lifestyle Factor"
            bio_role = f"Clinical physiological covariate: {feature_id}"
            chrom = "N/A"
            ftype = "Phenotypic Metadata"
        else:
            modality = "Transcriptomics"
            clean_gene = feature_id.split("_")[0].upper()
            anno = GENE_ANNOTATIONS.get(clean_gene, None)
            gene = clean_gene
            if anno:
                protein = anno["protein"]
                bio_role = anno["biological_role"]
                pw_id = anno["pathway_id"]
                pw_name = PATHWAY_KNOWLEDGE_BASE.get(pw_id, {}).get("name", "Aging Pathway")
                chrom = anno["chromosome"]
                ftype = anno["feature_type"]
            else:
                protein = f"{clean_gene} Gene Product"
                bio_role = "Expressed transcript with predictive weight in biological age estimation."
                pw_id = "PW_SENESCENCE"
                pw_name = "Cellular Aging Pathway"
                chrom = "Human Transcriptome"
                ftype = "mRNA Transcript"

        # Determine direction
        if shap_value is not None:
            direction = "Accelerates Predicted Age (+)" if shap_value >= 0 else "Decelerates Predicted Age (-)"
        else:
            direction = "Model Predictive Contributor"

        return CandidateBiomarker(
            feature_id=feature_id,
            modality=modality,
            scientific_term="Candidate Aging-Associated Feature",
            mean_abs_shap=round(float(importance_score), 4),
            importance_rank=rank,
            direction=direction,
            gene_symbol=gene,
            protein_name=protein,
            pathway_name=pw_name,
            pathway_id=pw_id,
            biological_role=bio_role,
            chromosome=chrom,
            feature_type=ftype,
            validation_status="Computational Candidate (Requires Experimental Validation)",
        )

    def build_candidate_biomarkers(
        self,
        feature_importance_dict: Dict[str, float],
        shap_values_dict: Optional[Dict[str, float]] = None,
        top_n: int = 25,
        enrich_external: bool = True,
    ) -> List[CandidateBiomarker]:
        """Converts raw feature importances into prioritized candidate biomarkers."""
        sorted_items = sorted(feature_importance_dict.items(), key=lambda x: abs(x[1]), reverse=True)[:top_n]
        candidates = []
        for rank, (feat, score) in enumerate(sorted_items, start=1):
            shap_val = shap_values_dict.get(feat) if shap_values_dict else score
            cand = self.annotate_feature(feat, score, rank, shap_val)
            candidates.append(cand)

        if enrich_external and candidates:
            candidates = self.enrich_with_external_knowledge(candidates)

        return candidates

    def enrich_with_external_knowledge(
        self,
        candidates: List[CandidateBiomarker],
        enable_live: bool = True,
    ) -> List[CandidateBiomarker]:
        """Enriches candidate biomarkers with Ensembl canonical IDs and provenance tracking."""
        try:
            from bioage.integrations.resolver import UnifiedIdentifierResolver
            from bioage.integrations.ensembl_client import EnsemblClient

            resolver = UnifiedIdentifierResolver(ensembl_client=EnsemblClient(enable_live=enable_live))
            feature_ids = [c.feature_id for c in candidates]
            resolved_list = resolver.resolve_batch(feature_ids)

            for cand, res in zip(candidates, resolved_list):
                if res.ensembl_gene_id:
                    cand.ensembl_gene_id = res.ensembl_gene_id
                if res.canonical_symbol and not cand.gene_symbol:
                    cand.gene_symbol = res.canonical_symbol
                if res.chromosome and (not cand.chromosome or cand.chromosome == "Unannotated"):
                    cand.chromosome = f"Chr {res.chromosome}" if not str(res.chromosome).startswith("Chr") else str(res.chromosome)
                cand.external_source = res.source
                cand.external_status = res.status.value if hasattr(res.status, "value") else str(res.status)
        except Exception as e:
            logger.warning(f"External biomarker enrichment error: {e}")

        return candidates

    def generate_phase2_bridge_payload(
        self,
        candidates: List[CandidateBiomarker],
    ) -> Dict[str, Any]:
        """
        Generates the formal transfer payload from Phase 1 to Phase 2 (GraphOmics-AI).
        Includes mapped seed genes, target pathways, and network construction parameters.
        """
        seed_genes = []
        pathway_set = set()
        for c in candidates:
            if c.gene_symbol and c.gene_symbol not in seed_genes:
                seed_genes.append(c.gene_symbol)
            if c.pathway_id:
                pathway_set.add(c.pathway_id)

        # Include canonical interactors if seed count is small
        if len(seed_genes) < 8:
            canonical_fallbacks = ["CDKN2A", "SIRT1", "IL6", "MTOR", "TP53", "ELOVL2", "FHL2", "FOXO3"]
            for g in canonical_fallbacks:
                if g not in seed_genes:
                    seed_genes.append(g)

        return {
            "source_phase": "Phase 1: BioAge Molecular Modeling",
            "target_phase": "Phase 2: GraphOmics-AI Network Analysis",
            "candidate_feature_count": len(candidates),
            "mapped_seed_genes": seed_genes,
            "associated_pathway_ids": list(pathway_set),
            "bridge_status": "READY_FOR_NETWORK_CONSTRUCTION",
            "research_question": "Do molecular features associated with biological-age prediction form coherent biological interaction networks that can be characterized using graph-based learning?",
            "candidates": [c.to_dict() for c in candidates],
        }


def enrich_with_external_knowledge(
    candidates: List[CandidateBiomarker],
    enable_live: bool = True,
) -> List[CandidateBiomarker]:
    """Module-level convenience function to enrich candidate biomarkers with Ensembl annotations."""
    bridge = BiomarkerToBiologyBridge()
    return bridge.enrich_with_external_knowledge(candidates, enable_live=enable_live)
