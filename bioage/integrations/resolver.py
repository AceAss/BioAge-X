"""
Unified Biological Identifier Resolution Pipeline for BioAge-X.
Classifies heterogeneous multi-omics features (CpG probes, Ensembl IDs, Gene Symbols, Covariates),
resolves canonical HGNC symbols and Ensembl IDs via EnsemblClient with caching,
detects ambiguities without hallucination, and preserves rigorous biological provenance.
"""

from typing import Dict, List, Optional, Any, Tuple
import re
from datetime import datetime, timezone

from bioage.integrations.base import (
    IdentifierResolver,
    KnowledgeStatus,
    ResolvedIdentifier,
)
from bioage.integrations.ensembl_client import EnsemblClient
from bioage.explainability.biomarker_bridge import CPG_GENE_ANNOTATIONS
from bioage.utils.logger import get_logger

logger = get_logger("bioage.integrations.resolver")


class UnifiedIdentifierResolver(IdentifierResolver):
    """Multi-omics feature classifier and canonical Ensembl/HGNC resolver."""

    def __init__(self, ensembl_client: Optional[EnsemblClient] = None):
        self.ensembl_client = ensembl_client or EnsemblClient()

    def detect_identifier_type(self, raw_id: str) -> str:
        """Determines the biological or technical modality of a feature ID."""
        s = str(raw_id).strip()

        # CpG methylation probe: cg followed by digits
        if re.match(r"^cg\d+", s, re.IGNORECASE):
            return "cpg"

        # Ensembl Gene ID
        if re.match(r"^ENSG\d{11}", s, re.IGNORECASE):
            return "ensembl_gene_id"

        # Ensembl Transcript ID
        if re.match(r"^ENST\d{11}", s, re.IGNORECASE):
            return "ensembl_transcript_id"

        # UniProt accession: e.g. P04637, Q9UI12
        if re.match(r"^[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2}$", s):
            return "uniprot"

        # Clinical / phenotypic covariate
        lower = s.lower()
        if lower in {
            "bmi", "age", "chronological_age", "sex", "gender", "smoking",
            "smoking_status", "pack_years", "systolic_bp", "diastolic_bp",
            "cholesterol", "fasting_glucose", "crp", "hba1c"
        }:
            return "clinical_covariate"

        # Gene prefix syntax: GENE_SYMBOL or probe_SYMBOL
        if "_" in s:
            parts = s.split("_")
            if parts[-1].isupper() and 2 <= len(parts[-1]) <= 12:
                return "prefixed_symbol"

        # Standard HGNC gene symbol (e.g. TP53, ELOVL2, CDKN2A)
        if re.match(r"^[A-Z0-9\-]{2,15}$", s):
            return "gene_symbol"

        return "unknown_feature"

    def resolve(self, identifier: str) -> ResolvedIdentifier:
        """Resolves an individual feature ID."""
        batch = self.resolve_batch([identifier])
        return batch[0] if batch else ResolvedIdentifier(
            input_id=identifier,
            identifier_type="unknown",
            status=KnowledgeStatus.NOT_FOUND,
        )

    def resolve_batch(
        self,
        identifiers: List[str],
        species: str = "homo_sapiens",
    ) -> List[ResolvedIdentifier]:
        """
        Processes a batch of candidate features through the normalization pipeline:
          Raw feature
          → detect identifier type
          → resolve identifier (CpG dictionary / Ensembl API / local fallback)
          → canonical gene & Ensembl ID
          → normalized internal representation with provenance status
        """
        results: List[ResolvedIdentifier] = []
        genes_to_lookup: Dict[str, List[int]] = {}  # gene_symbol -> list of indices in results
        now_utc = datetime.now(timezone.utc).isoformat()

        for idx, raw_id in enumerate(identifiers):
            clean_id = str(raw_id).strip()
            id_type = self.detect_identifier_type(clean_id)

            if id_type == "clinical_covariate":
                results.append(ResolvedIdentifier(
                    input_id=clean_id,
                    identifier_type="clinical_covariate",
                    canonical_symbol=None,
                    ensembl_gene_id=None,
                    species=species,
                    description=f"Phenotypic / clinical covariate: {clean_id}",
                    status=KnowledgeStatus.LOCAL_FALLBACK,
                    source="Clinical Phenotype Specification",
                    retrieved_at=now_utc,
                ))
            elif id_type == "cpg":
                # Extract CpG root
                m = re.match(r"^(cg\d+)", clean_id, re.IGNORECASE)
                cpg_root = m.group(1).lower() if m else clean_id.lower()

                # Check if suffix has gene name, e.g. cg16867657_ELOVL2
                suffix_gene = None
                if "_" in clean_id:
                    parts = clean_id.split("_")
                    if len(parts) > 1 and parts[-1].isupper():
                        suffix_gene = parts[-1]

                cpg_anno = CPG_GENE_ANNOTATIONS.get(cpg_root)
                mapped_gene = suffix_gene or (cpg_anno["gene"] if cpg_anno else None)

                if mapped_gene:
                    item = ResolvedIdentifier(
                        input_id=clean_id,
                        identifier_type="cpg",
                        canonical_symbol=mapped_gene,
                        species=species,
                        chromosome=cpg_anno.get("chromosome") if cpg_anno else None,
                        description=cpg_anno.get("biological_role") if cpg_anno else f"CpG probe targeting {mapped_gene}",
                        source="Illumina Infinium Annotation",
                        status=KnowledgeStatus.LOCAL_FALLBACK,
                        retrieved_at=now_utc,
                    )
                    results.append(item)
                    genes_to_lookup.setdefault(mapped_gene.upper(), []).append(len(results) - 1)
                else:
                    results.append(ResolvedIdentifier(
                        input_id=clean_id,
                        identifier_type="cpg",
                        canonical_symbol=None,
                        species=species,
                        description="Unannotated DNA methylation locus",
                        status=KnowledgeStatus.NOT_FOUND,
                        source="Illumina Infinium Annotation",
                        retrieved_at=now_utc,
                    ))
            elif id_type in ("prefixed_symbol", "gene_symbol"):
                # Clean prefix
                gene_symbol = clean_id.replace("GENE_", "").split("_")[-1].upper()
                item = ResolvedIdentifier(
                    input_id=clean_id,
                    identifier_type="gene_symbol",
                    canonical_symbol=gene_symbol,
                    species=species,
                    source="Ensembl",
                    status=KnowledgeStatus.LIVE,
                    retrieved_at=now_utc,
                )
                results.append(item)
                genes_to_lookup.setdefault(gene_symbol, []).append(len(results) - 1)
            elif id_type == "ensembl_gene_id":
                item = ResolvedIdentifier(
                    input_id=clean_id,
                    identifier_type="ensembl_gene_id",
                    ensembl_gene_id=clean_id,
                    species=species,
                    source="Ensembl",
                    status=KnowledgeStatus.LIVE,
                    retrieved_at=now_utc,
                )
                results.append(item)
                genes_to_lookup.setdefault(clean_id, []).append(len(results) - 1)
            else:
                results.append(ResolvedIdentifier(
                    input_id=clean_id,
                    identifier_type="unknown_feature",
                    status=KnowledgeStatus.NOT_FOUND,
                    source="IdentifierResolver",
                    description="Unrecognized molecular identifier format",
                    retrieved_at=now_utc,
                ))

        # Query Ensembl for all gene symbols needing Ensembl ID / coordinates
        if genes_to_lookup:
            unique_genes = list(genes_to_lookup.keys())
            try:
                resolved_ensembl = self.ensembl_client.resolve_batch(unique_genes, species=species)
                lookup_map = {r.input_id.upper(): r for r in resolved_ensembl}
                lookup_map.update({(r.canonical_symbol or "").upper(): r for r in resolved_ensembl if r.canonical_symbol})

                for gene_key, target_indices in genes_to_lookup.items():
                    e_match = lookup_map.get(gene_key.upper())
                    if e_match:
                        for idx in target_indices:
                            target = results[idx]
                            target.canonical_symbol = e_match.canonical_symbol or target.canonical_symbol
                            target.ensembl_gene_id = e_match.ensembl_gene_id
                            target.chromosome = target.chromosome or e_match.chromosome
                            target.start_position = e_match.start_position
                            target.end_position = e_match.end_position
                            target.biotype = e_match.biotype
                            target.status = e_match.status
                            target.source = e_match.source
                            target.ambiguity_candidates = e_match.ambiguity_candidates
                            if e_match.description and not target.description:
                                target.description = e_match.description
            except Exception as e:
                logger.warning(f"Ensembl resolution in UnifiedIdentifierResolver encountered: {e}")

        return results
