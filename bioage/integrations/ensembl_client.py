"""
Ensembl REST API Client & Identifier Annotation Adapter for BioAge-X.
Resolves gene symbols, Ensembl Gene IDs (ENSG...), chromosomal coordinates,
and biotypes with live caching, ambiguity detection, and deterministic local fallback.
"""

from typing import Dict, List, Optional, Any, Tuple
import time
import httpx
from datetime import datetime, timezone

from bioage.integrations.base import (
    BiologicalKnowledgeProvider,
    IdentifierResolver,
    KnowledgeStatus,
    ProviderHealth,
    ResolvedIdentifier,
)
from bioage.integrations.cache import get_integration_cache, PersistentBiologicalCache
from bioage.integrations.rate_limit import RateLimiter, retry_with_backoff
from bioage.utils.logger import get_logger

logger = get_logger("bioage.integrations.ensembl")

# Curated local fallback dictionary for canonical aging & epigenetic clock genes
LOCAL_ENSEMBL_FALLBACK: Dict[str, Dict[str, Any]] = {
    "ELOVL2": {
        "ensembl_gene_id": "ENSG00000197977",
        "symbol": "ELOVL2",
        "chromosome": "6",
        "start": 11043743,
        "end": 11107297,
        "biotype": "protein_coding",
        "description": "ELOVL fatty acid elongase 2 [Source:HGNC Symbol;Acc:HGNC:14415]",
    },
    "FHL2": {
        "ensembl_gene_id": "ENSG00000115641",
        "symbol": "FHL2",
        "chromosome": "2",
        "start": 105399587,
        "end": 105467000,
        "biotype": "protein_coding",
        "description": "four and a half LIM domains 2 [Source:HGNC Symbol;Acc:HGNC:3703]",
    },
    "CDKN2A": {
        "ensembl_gene_id": "ENSG00000147889",
        "symbol": "CDKN2A",
        "chromosome": "9",
        "start": 21967751,
        "end": 21995300,
        "biotype": "protein_coding",
        "description": "cyclin dependent kinase inhibitor 2A (p16INK4a) [Source:HGNC Symbol;Acc:HGNC:1787]",
    },
    "CDKN1A": {
        "ensembl_gene_id": "ENSG00000124762",
        "symbol": "CDKN1A",
        "chromosome": "6",
        "start": 36644265,
        "end": 36655117,
        "biotype": "protein_coding",
        "description": "cyclin dependent kinase inhibitor 1A (p21CIP1) [Source:HGNC Symbol;Acc:HGNC:1784]",
    },
    "TP53": {
        "ensembl_gene_id": "ENSG00000141510",
        "symbol": "TP53",
        "chromosome": "17",
        "start": 7668402,
        "end": 7687550,
        "biotype": "protein_coding",
        "description": "tumor protein p53 [Source:HGNC Symbol;Acc:HGNC:11998]",
    },
    "SIRT1": {
        "ensembl_gene_id": "ENSG00000096717",
        "symbol": "SIRT1",
        "chromosome": "10",
        "start": 67884646,
        "end": 67918390,
        "biotype": "protein_coding",
        "description": "sirtuin 1 [Source:HGNC Symbol;Acc:HGNC:14929]",
    },
    "FOXO3": {
        "ensembl_gene_id": "ENSG00000118689",
        "symbol": "FOXO3",
        "chromosome": "6",
        "start": 108559868,
        "end": 108685121,
        "biotype": "protein_coding",
        "description": "forkhead box O3 [Source:HGNC Symbol;Acc:HGNC:3821]",
    },
    "MTOR": {
        "ensembl_gene_id": "ENSG00000198695",
        "symbol": "MTOR",
        "chromosome": "1",
        "start": 11106535,
        "end": 11262557,
        "biotype": "protein_coding",
        "description": "mechanistic target of rapamycin kinase [Source:HGNC Symbol;Acc:HGNC:3942]",
    },
    "IL6": {
        "ensembl_gene_id": "ENSG00000136244",
        "symbol": "IL6",
        "chromosome": "7",
        "start": 22725889,
        "end": 22732002,
        "biotype": "protein_coding",
        "description": "interleukin 6 [Source:HGNC Symbol;Acc:HGNC:6018]",
    },
    "TNF": {
        "ensembl_gene_id": "ENSG00000232810",
        "symbol": "TNF",
        "chromosome": "6",
        "start": 31575565,
        "end": 31578336,
        "biotype": "protein_coding",
        "description": "tumor necrosis factor [Source:HGNC Symbol;Acc:HGNC:11892]",
    },
    "TERT": {
        "ensembl_gene_id": "ENSG00000164362",
        "symbol": "TERT",
        "chromosome": "5",
        "start": 1253147,
        "end": 1295068,
        "biotype": "protein_coding",
        "description": "telomerase reverse transcriptase [Source:HGNC Symbol;Acc:HGNC:11730]",
    },
    "SOD2": {
        "ensembl_gene_id": "ENSG00000112096",
        "symbol": "SOD2",
        "chromosome": "6",
        "start": 159673892,
        "end": 159702213,
        "biotype": "protein_coding",
        "description": "superoxide dismutase 2 [Source:HGNC Symbol;Acc:HGNC:11180]",
    },
    "GDF15": {
        "ensembl_gene_id": "ENSG00000130513",
        "symbol": "GDF15",
        "chromosome": "19",
        "start": 18381504,
        "end": 18384288,
        "biotype": "protein_coding",
        "description": "growth differentiation factor 15 [Source:HGNC Symbol;Acc:HGNC:30138]",
    },
    "KLOTHO": {
        "ensembl_gene_id": "ENSG00000133401",
        "symbol": "KL",
        "chromosome": "13",
        "start": 33016024,
        "end": 33065620,
        "biotype": "protein_coding",
        "description": "klotho [Source:HGNC Symbol;Acc:HGNC:6344]",
    },
    "DNMT1": {
        "ensembl_gene_id": "ENSG00000130816",
        "symbol": "DNMT1",
        "chromosome": "19",
        "start": 10132800,
        "end": 10193100,
        "biotype": "protein_coding",
        "description": "DNA methyltransferase 1 [Source:HGNC Symbol;Acc:HGNC:2976]",
    },
    "ATM": {
        "ensembl_gene_id": "ENSG00000149311",
        "symbol": "ATM",
        "chromosome": "11",
        "start": 108223067,
        "end": 108369102,
        "biotype": "protein_coding",
        "description": "ATM serine/threonine kinase [Source:HGNC Symbol;Acc:HGNC:795]",
    },
    "GSTP1": {
        "ensembl_gene_id": "ENSG00000084207",
        "symbol": "GSTP1",
        "chromosome": "11",
        "start": 67584100,
        "end": 67587100,
        "biotype": "protein_coding",
        "description": "glutathione S-transferase pi 1 [Source:HGNC Symbol;Acc:HGNC:4638]",
    },
}


class EnsemblClient(BiologicalKnowledgeProvider, IdentifierResolver):
    """Ensembl REST client with caching, retry, and local fallback."""

    BASE_URL = "https://rest.ensembl.org"

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 6.0,
        cache: Optional[PersistentBiologicalCache] = None,
        enable_live: bool = True,
    ):
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.timeout = timeout
        self.cache = cache or get_integration_cache()
        self.enable_live = enable_live
        self.rate_limiter = RateLimiter(requests_per_second=5.0, provider_name="Ensembl")
        self.last_health: Optional[ProviderHealth] = None

    @property
    def provider_name(self) -> str:
        return "Ensembl"

    def check_health(self) -> ProviderHealth:
        """Pings Ensembl REST endpoint."""
        start = time.time()
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(
                    f"{self.base_url}/info/ping",
                    headers={"Content-Type": "application/json", "Accept": "application/json"},
                )
                latency = round((time.time() - start) * 1000, 2)
                if res.status_code == 200 and res.json().get("ping") == 1:
                    health = ProviderHealth(
                        provider="Ensembl",
                        status="available",
                        version="GRCh38 / Ensembl Release 113",
                        latency_ms=latency,
                        last_successful_request=datetime.now(timezone.utc).isoformat(),
                        cached_records=self.cache.get_stats().get("by_provider", {}).get("ensembl", 0),
                        message="Ensembl REST API operational",
                    )
                    self.last_health = health
                    return health

            health = ProviderHealth(
                provider="Ensembl",
                status="degraded",
                latency_ms=round((time.time() - start) * 1000, 2),
                cached_records=self.cache.get_stats().get("by_provider", {}).get("ensembl", 0),
                message=f"Ensembl responded with status {res.status_code}",
            )
            self.last_health = health
            return health
        except Exception as e:
            health = ProviderHealth(
                provider="Ensembl",
                status="unavailable",
                latency_ms=round((time.time() - start) * 1000, 2),
                cached_records=self.cache.get_stats().get("by_provider", {}).get("ensembl", 0),
                message=f"Ensembl ping failed ({e}). Local fallback active.",
            )
            self.last_health = health
            return health

    def resolve(self, identifier: str) -> ResolvedIdentifier:
        """Resolves a single gene symbol or Ensembl ID."""
        results = self.resolve_batch([identifier])
        return results[0] if results else ResolvedIdentifier(
            input_id=identifier,
            identifier_type="symbol",
            status=KnowledgeStatus.NOT_FOUND,
            source="Ensembl",
        )

    def resolve_batch(
        self,
        identifiers: List[str],
        species: str = "homo_sapiens",
    ) -> List[ResolvedIdentifier]:
        """
        Resolves a list of gene symbols or IDs.
        Priority:
          1. Cache
          2. Live Ensembl REST API (if enable_live=True)
          3. Local deterministic fallback
        """
        clean_ids = [str(i).strip().upper() for i in identifiers if str(i).strip()]
        if not clean_ids:
            return []

        resolved_list: List[ResolvedIdentifier] = []
        pending_ids: List[str] = []

        # 1. Check cache first
        for gene_id in clean_ids:
            cache_params = {"species": species, "symbol": gene_id}
            cached_data = self.cache.get("ensembl", cache_params)
            if cached_data:
                payload, meta = cached_data
                res_obj = self._dict_to_resolved(payload, status=KnowledgeStatus.CACHED)
                resolved_list.append(res_obj)
            else:
                pending_ids.append(gene_id)

        if not pending_ids:
            return resolved_list

        # 2. Query Live Ensembl if enabled
        live_results: Dict[str, Any] = {}
        if self.enable_live:
            try:
                live_results = self._fetch_live_batch(pending_ids, species=species)
            except Exception as e:
                logger.warning(f"Ensembl live batch lookup failed: {e}. Switching to local fallback.")

        # Process each pending ID
        for gene_id in pending_ids:
            if gene_id in live_results:
                raw_info = live_results[gene_id]
                # Check ambiguity
                if isinstance(raw_info, list) and len(raw_info) > 1:
                    candidates = [item.get("id") for item in raw_info if isinstance(item, dict)]
                    res_obj = ResolvedIdentifier(
                        input_id=gene_id,
                        identifier_type="symbol",
                        canonical_symbol=gene_id,
                        status=KnowledgeStatus.AMBIGUOUS,
                        ambiguity_candidates=candidates,
                        source="Ensembl",
                        description=f"Multiple gene models found ({len(candidates)} candidates)",
                    )
                    resolved_list.append(res_obj)
                    continue

                info = raw_info[0] if isinstance(raw_info, list) else raw_info
                res_obj = ResolvedIdentifier(
                    input_id=gene_id,
                    identifier_type="symbol",
                    canonical_symbol=info.get("display_name", gene_id),
                    ensembl_gene_id=info.get("id"),
                    species=species,
                    chromosome=str(info.get("seq_region_name", "")),
                    start_position=info.get("start"),
                    end_position=info.get("end"),
                    description=info.get("description"),
                    biotype=info.get("biotype"),
                    status=KnowledgeStatus.LIVE,
                    source="Ensembl",
                )
                # Store in cache
                self.cache.set(
                    "ensembl",
                    {"species": species, "symbol": gene_id},
                    res_obj.to_dict(),
                    provider_version="Ensembl 113",
                )
                resolved_list.append(res_obj)
            else:
                # 3. Local fallback check
                fb = LOCAL_ENSEMBL_FALLBACK.get(gene_id)
                if fb:
                    res_obj = ResolvedIdentifier(
                        input_id=gene_id,
                        identifier_type="symbol",
                        canonical_symbol=fb.get("symbol", gene_id),
                        ensembl_gene_id=fb.get("ensembl_gene_id"),
                        species=species,
                        chromosome=fb.get("chromosome"),
                        start_position=fb.get("start"),
                        end_position=fb.get("end"),
                        description=fb.get("description"),
                        biotype=fb.get("biotype"),
                        status=KnowledgeStatus.LOCAL_FALLBACK,
                        source="Local Curated Fallback (Ensembl GRCh38)",
                    )
                    resolved_list.append(res_obj)
                else:
                    # Unresolvable without fabrication
                    resolved_list.append(ResolvedIdentifier(
                        input_id=gene_id,
                        identifier_type="symbol",
                        status=KnowledgeStatus.NOT_FOUND,
                        source="Ensembl",
                        description="Gene symbol unmapped in Ensembl and local fallback",
                    ))

        return resolved_list

    def _fetch_live_batch(self, symbols: List[str], species: str = "homo_sapiens") -> Dict[str, Any]:
        """Sends batch POST to Ensembl REST lookup."""
        self.rate_limiter.wait()

        @retry_with_backoff("Ensembl", max_retries=2, base_delay=0.4)
        def _post():
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.base_url}/lookup/symbol/{species}",
                    json={"symbols": symbols},
                    headers={"Content-Type": "application/json", "Accept": "application/json"},
                )
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code in (400, 404):
                    logger.debug(f"Ensembl batch returned {resp.status_code}")
                    return {}
                resp.raise_for_status()

        return _post()

    def _dict_to_resolved(self, d: Dict[str, Any], status: KnowledgeStatus) -> ResolvedIdentifier:
        return ResolvedIdentifier(
            input_id=d.get("input_id", ""),
            identifier_type=d.get("identifier_type", "symbol"),
            canonical_symbol=d.get("canonical_symbol"),
            ensembl_gene_id=d.get("ensembl_gene_id"),
            species=d.get("species", "homo_sapiens"),
            chromosome=d.get("chromosome"),
            start_position=d.get("start_position"),
            end_position=d.get("end_position"),
            description=d.get("description"),
            biotype=d.get("biotype"),
            status=status,
            ambiguity_candidates=d.get("ambiguity_candidates", []),
            source=d.get("source", "Ensembl"),
            retrieved_at=d.get("retrieved_at", datetime.now(timezone.utc).isoformat()),
        )
