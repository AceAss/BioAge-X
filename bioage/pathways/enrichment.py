"""
Pathway Enrichment Analysis for BioAge-X.
Implements over-representation analysis (ORA) using the hypergeometric test
and Benjamini-Hochberg FDR correction against curated aging pathways.
"""

from typing import Dict, List, Any, Optional
import numpy as np
from scipy import stats

from bioage.pathways.database import PATHWAY_KNOWLEDGE_BASE, ALL_PATHWAY_GENES
from bioage.utils.logger import get_logger

logger = get_logger("bioage.pathways.enrichment")


class PathwayEnrichmentAnalyzer:
    """Over-representation analysis engine for candidate aging biomarkers."""

    def __init__(
        self,
        custom_pathways: Optional[Dict[str, Dict[str, Any]]] = None,
        background_population_size: int = 20000,  # Standard human protein-coding genome size
    ):
        self.pathways = custom_pathways or PATHWAY_KNOWLEDGE_BASE
        self.background_size = background_population_size

    def analyze(
        self,
        query_genes: List[str],
        fdr_threshold: float = 0.10,
    ) -> List[Dict[str, Any]]:
        """
        Runs hypergeometric test for each pathway in the database.
        Returns sorted list of pathway enrichment records.
        """
        # Clean gene symbols (remove probe prefixes like GENE_, cg...)
        clean_genes = set()
        for g in query_genes:
            clean = str(g).replace("GENE_", "").split("_")[-1].upper()
            clean_genes.add(clean)

        n_query = len(clean_genes)
        logger.info(f"Analyzing pathway enrichment for {n_query} unique query genes")

        results = []
        raw_p_values = []

        M = self.background_size  # Total genes in universe
        n = n_query              # Total genes drawn (query set)

        for pw_id, pw_info in self.pathways.items():
            pw_name = pw_info["name"]
            pw_category = pw_info.get("category", "General")
            pw_genes = set(g.upper() for g in pw_info["genes"])
            N = len(pw_genes)    # Total genes in pathway (success states in universe)

            overlap = clean_genes.intersection(pw_genes)
            k = len(overlap)     # Overlap count (successes drawn)

            if k == 0:
                p_val = 1.0
                odds_ratio = 0.0
            else:
                # Hypergeometric survival function (P(X >= k))
                # hypergeom.sf(k-1, M, N, n)
                p_val = float(stats.hypergeom.sf(k - 1, M, N, n))
                
                # Contingency table for odds ratio:
                # [[overlap, query_not_in_pw], [pw_not_in_query, neither]]
                table = [
                    [k, n - k],
                    [N - k, max(1, M - N - (n - k))]
                ]
                res = stats.fisher_exact(table)
                raw_stat = float(res.statistic)
                if np.isinf(raw_stat) or np.isnan(raw_stat):
                    odds_ratio = 999.0
                else:
                    odds_ratio = round(raw_stat, 2)

            raw_p_values.append(p_val)
            results.append({
                "pathway_id": pw_id,
                "pathway_name": pw_name,
                "category": pw_category,
                "description": pw_info.get("description", ""),
                "pathway_size": N,
                "overlap_count": k,
                "overlapping_genes": sorted(list(overlap)),
                "p_value": p_val,
                "odds_ratio": odds_ratio,
            })

        # Benjamini-Hochberg FDR correction
        adj_p_values = self._benjamini_hochberg(raw_p_values)

        for i, res in enumerate(results):
            adj_p = adj_p_values[i]
            res["fdr_adjusted_p"] = round(adj_p, 6)
            res["neg_log10_p"] = round(-np.log10(max(res["p_value"], 1e-15)), 2)
            # Enrichment score
            enrichment_score = res["neg_log10_p"] * (res["overlap_count"] / max(1, res["pathway_size"]))
            res["enrichment_score"] = round(enrichment_score, 3)

        # Sort by p-value ascending
        sorted_results = sorted(results, key=lambda x: x["p_value"])
        logger.info(
            f"Pathway analysis complete. Top pathway: "
            f"'{sorted_results[0]['pathway_name']}' (p={sorted_results[0]['p_value']:.2e}, "
            f"overlap={sorted_results[0]['overlap_count']})"
        )
        return sorted_results

    def _benjamini_hochberg(self, p_values: List[float]) -> List[float]:
        """Calculates Benjamini-Hochberg FDR corrected p-values."""
        p_arr = np.asarray(p_values)
        n = len(p_arr)
        order = np.argsort(p_arr)
        ranked_p = p_arr[order]
        
        q_values = np.zeros(n)
        running_min = 1.0
        for i in range(n - 1, -1, -1):
            rank = i + 1
            q = (ranked_p[i] * n) / rank
            running_min = min(running_min, q)
            q_values[i] = min(1.0, running_min)

        unranked_q = np.zeros(n)
        unranked_q[order] = q_values
        return [float(q) for q in unranked_q]
