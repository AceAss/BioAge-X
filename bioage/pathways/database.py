"""
Curated Biological Pathways Database for BioAge-X.
Defines canonical hallmarks of aging, senescence, and epigenetic pathways
without requiring external internet queries.
"""

from typing import Dict, List, Set, Any

PATHWAY_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    "PW_SENESCENCE": {
        "id": "PW_SENESCENCE",
        "name": "Cellular Senescence & SASP Signaling",
        "category": "Cellular Stress",
        "description": "Permanent cell cycle arrest accompanied by secretory phenotype driving tissue remodeling and inflammation.",
        "genes": [
            "CDKN2A", "CDKN1A", "TP53", "IL6", "CXCL8", "GDF15", "SERPINE1",
            "MMP1", "MMP3", "IL1A", "IL1B", "CCND1", "RB1", "NFKB1",
        ],
    },
    "PW_TELOMERE": {
        "id": "PW_TELOMERE",
        "name": "Telomere Maintenance & Replicative Lifespan",
        "category": "Genomic Integrity",
        "description": "Regulation of shelterin complex and telomeric repeat maintenance at chromosome ends.",
        "genes": [
            "TERT", "TERC", "DKC1", "POT1", "ACD", "TINF2", "TERF1", "TERF2",
            "RAP1A", "WRN", "BLM", "ATM",
        ],
    },
    "PW_EPIGENETIC": {
        "id": "PW_EPIGENETIC",
        "name": "Epigenetic Alterations & DNA Methylation",
        "category": "Epigenomics",
        "description": "Horvath epigenetic clock loci, DNA methyltransferases, and histone-modifying sirtuin deacetylases.",
        "genes": [
            "ELOVL2", "FHL2", "PENK", "EDARADD", "DNMT1", "DNMT3A", "DNMT3B",
            "TET1", "TET2", "TET3", "SIRT1", "SIRT6", "HDAC1", "KMT2A", "EZH2",
        ],
    },
    "PW_NUTRIENT_SENSING": {
        "id": "PW_NUTRIENT_SENSING",
        "name": "Deregulated Nutrient Sensing (IIS / mTOR)",
        "category": "Metabolism",
        "description": "Insulin/IGF-1 and mechanistic target of rapamycin signaling cascades governing anabolic vs maintenance states.",
        "genes": [
            "MTOR", "RPS6KB1", "AKT1", "PIK3CA", "FOXO3", "FOXO1", "IGF1",
            "IGF1R", "INS", "INSR", "PRKAA1", "PRKAB1", "TSC1", "TSC2", "KLOTHO",
        ],
    },
    "PW_MITOCHONDRIAL": {
        "id": "PW_MITOCHONDRIAL",
        "name": "Mitochondrial Dynamics & Oxidative Stress",
        "category": "Mitochondrial Biology",
        "description": "Mitochondrial ROS production, electron transport chain efficiency, and mitophagic quality control.",
        "genes": [
            "SOD2", "CAT", "GPX1", "PPARGC1A", "TFAM", "PINK1", "PRKN",
            "POLG", "NDUFA9", "SDHA", "UQCRC1", "COX4I1", "ATP5F1A",
        ],
    },
    "PW_PROTEOSTASIS": {
        "id": "PW_PROTEOSTASIS",
        "name": "Loss of Proteostasis & Autophagy",
        "category": "Proteostasis",
        "description": "Protein folding chaperones, ubiquitin-proteasome degradation, and macroautophagy clearance.",
        "genes": [
            "HSP90AA1", "HSPA1A", "HSPA8", "BECN1", "ATG5", "ATG7", "ATG12",
            "MAP1LC3B", "SQSTM1", "LAMP2", "PSMB5", "UBB", "VCP",
        ],
    },
    "PW_INFLAMMAGING": {
        "id": "PW_INFLAMMAGING",
        "name": "Chronic Systemic Inflammaging",
        "category": "Immune & Inflammatory",
        "description": "Sterile, non-resolving systemic inflammatory state mediated by innate immune cytokines.",
        "genes": [
            "IL6", "TNF", "IL1B", "CRP", "NFKB1", "RELA", "TLR4", "NLRP3",
            "CASP1", "CXCL10", "CCL2", "JAK2", "STAT3",
        ],
    },
    "PW_DNA_REPAIR": {
        "id": "PW_DNA_REPAIR",
        "name": "DNA Damage Response & Genomic Instability",
        "category": "Genomic Integrity",
        "description": "Double-strand break repair, base excision repair, and cell cycle arrest checkpoints.",
        "genes": [
            "TP53", "ATM", "ATR", "CHEK1", "CHEK2", "BRCA1", "BRCA2", "RAD51",
            "PARP1", "XRCC1", "ERCC1", "OGG1", "H2AX",
        ],
    },
}

ALL_PATHWAY_GENES: Set[str] = set()
for p in PATHWAY_KNOWLEDGE_BASE.values():
    ALL_PATHWAY_GENES.update(p["genes"])
