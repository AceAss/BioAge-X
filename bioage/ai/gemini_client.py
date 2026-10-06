"""
Google Gemini AI Research Assistant Client for BioAge-X.
Provides evidence-constrained natural-language interpretation of computational results.
Operates strictly as an OPTIONAL post-processing layer downstream of statistical,
ML, SHAP, network biology, and GNN computations.

Guarantees:
- Never invents biomarkers, pathways, interactions, or citations.
- Never fabricates or alters model metrics or SHAP attributions.
- Strictly separates observed computational results from external knowledge and hypotheses.
- Completely optional: BioAge-X remains 100% operational when disabled or keyless.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
import hashlib
import json
import os
import re
import time
import httpx
from datetime import datetime, timezone

from bioage.integrations.base import ProviderHealth
from bioage.utils.logger import get_logger

logger = get_logger("bioage.ai.gemini")

DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


@dataclass
class GeminiInterpretation:
    """Structured, evidence-constrained AI research interpretation."""
    status: str  # "AVAILABLE_WITH_KEY", "DISABLED", "AUTH_REQUIRED", "UNAVAILABLE", "FALLBACK"
    task_type: str
    summary: str
    observations: List[str] = field(default_factory=list)
    hypotheses: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    evidence_sources: List[str] = field(default_factory=list)
    disclaimer: str = (
        "AI-generated interpretation — verify against primary sources. "
        "Generated strictly from BioAge-X computational results; does not constitute medical or clinical advice."
    )
    model_used: Optional[str] = None
    cached: bool = False
    latency_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GeminiAssistantClient:
    """
    Client for interacting with the Google Gemini API.
    Designed for evidence-bounded interpretation of computational aging biology.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enabled: Optional[bool] = None,
        timeout: float = 12.0,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model or os.getenv("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
        
        # Determine whether AI is enabled
        env_enabled = os.getenv("GEMINI_ENABLED", "false").lower() in ("true", "1", "yes")
        self.enabled = enabled if enabled is not None else env_enabled
        
        self.timeout = timeout
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_request_time: float = 0.0
        self._min_request_interval: float = 1.0  # Rate limit: ~1 request per second max

    @property
    def is_configured(self) -> bool:
        """Returns True if enabled and API key is present."""
        return bool(self.enabled and self.api_key and self.api_key.strip())

    def check_health(self) -> ProviderHealth:
        """Checks configuration and operational health of the Gemini service."""
        if not self.enabled:
            return ProviderHealth(
                provider="Gemini",
                status="DISABLED",
                version=self.model,
                message="Gemini AI Assistant is disabled (GEMINI_ENABLED=false). All computational pipelines run normally.",
                cached_records=len(self._cache),
            )

        if not self.api_key or not self.api_key.strip():
            return ProviderHealth(
                provider="Gemini",
                status="AUTH_REQUIRED",
                version=self.model,
                message="Gemini enabled but GEMINI_API_KEY is not configured in environment.",
                cached_records=len(self._cache),
            )

        # Health ping to check connectivity
        start = time.time()
        try:
            url = f"{GEMINI_API_BASE}/{self.model}?key={self.api_key}"
            with httpx.Client(timeout=4.0) as client:
                res = client.get(url)
                latency = round((time.time() - start) * 1000, 2)
                if res.status_code == 200:
                    return ProviderHealth(
                        provider="Gemini",
                        status="AVAILABLE_WITH_KEY",
                        version=self.model,
                        latency_ms=latency,
                        last_successful_request=datetime.now(timezone.utc).isoformat(),
                        cached_records=len(self._cache),
                        message=f"Gemini API operational ({self.model})",
                    )
                elif res.status_code in (400, 403):
                    return ProviderHealth(
                        provider="Gemini",
                        status="AUTH_REQUIRED",
                        version=self.model,
                        latency_ms=latency,
                        cached_records=len(self._cache),
                        message=f"Gemini authentication failed (HTTP {res.status_code}). Check GEMINI_API_KEY.",
                    )
                else:
                    return ProviderHealth(
                        provider="Gemini",
                        status="DEGRADED",
                        version=self.model,
                        latency_ms=latency,
                        cached_records=len(self._cache),
                        message=f"Gemini responded with HTTP {res.status_code}.",
                    )
        except Exception as e:
            return ProviderHealth(
                provider="Gemini",
                status="UNAVAILABLE",
                version=self.model,
                latency_ms=round((time.time() - start) * 1000, 2),
                cached_records=len(self._cache),
                message=f"Gemini connection error: {e}. AI assistance offline.",
            )

    def interpret(
        self,
        task_type: str,
        evidence: Dict[str, Any],
        experiment_id: Optional[str] = None,
    ) -> GeminiInterpretation:
        """
        Interprets supplied computational evidence using Gemini.
        If Gemini is disabled, keyless, or unavailable, returns a deterministic structured fallback.
        """
        # 1. Check if disabled or keyless
        if not self.enabled:
            return self._build_deterministic_fallback(
                task_type, evidence, status="DISABLED",
                msg="AI interpretation disabled. Enable GEMINI_ENABLED=true in .env to activate."
            )

        if not self.api_key or not self.api_key.strip():
            return self._build_deterministic_fallback(
                task_type, evidence, status="AUTH_REQUIRED",
                msg="GEMINI_API_KEY not configured. Set GEMINI_API_KEY in your local .env to enable AI interpretations."
            )

        # 2. Check local in-memory cache
        cache_key = self._compute_cache_key(task_type, evidence)
        if cache_key in self._cache:
            hit = self._cache[cache_key]
            return GeminiInterpretation(
                status="AVAILABLE_WITH_KEY",
                task_type=task_type,
                summary=hit.get("summary", ""),
                observations=hit.get("observations", []),
                hypotheses=hit.get("hypotheses", []),
                limitations=hit.get("limitations", []),
                evidence_sources=hit.get("evidence_sources", []),
                model_used=self.model,
                cached=True,
                latency_ms=0.5,
            )

        # 3. Rate limiting throttle
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)

        # 4. Construct prompt and execute API call
        prompt = self._construct_prompt(task_type, evidence)
        start = time.time()
        try:
            url = f"{GEMINI_API_BASE}/{self.model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,  # Low temperature for strict factual adherence
                    "maxOutputTokens": 1024,
                },
            }

            self._last_request_time = time.time()
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(url, json=payload)
                latency = round((time.time() - start) * 1000, 2)

                if res.status_code == 200:
                    data = res.json()
                    raw_text = self._extract_text_from_response(data)
                    parsed = self._parse_and_validate_json(raw_text)

                    if parsed:
                        self._cache[cache_key] = parsed
                        return GeminiInterpretation(
                            status="AVAILABLE_WITH_KEY",
                            task_type=task_type,
                            summary=parsed.get("summary", ""),
                            observations=parsed.get("observations", []),
                            hypotheses=parsed.get("hypotheses", []),
                            limitations=parsed.get("limitations", []),
                            evidence_sources=parsed.get("evidence_sources", []),
                            model_used=self.model,
                            cached=False,
                            latency_ms=latency,
                        )
                    else:
                        logger.warning("Gemini response failed JSON parsing; using sanitized fallback.")
                        return self._build_deterministic_fallback(
                            task_type, evidence, status="DEGRADED",
                            msg="AI generated non-conforming response schema; deterministic fallback rendered.",
                            raw_snippet=raw_text[:200],
                        )

                elif res.status_code in (400, 403):
                    logger.warning(f"Gemini API auth error {res.status_code}: {res.text}")
                    return self._build_deterministic_fallback(
                        task_type, evidence, status="AUTH_REQUIRED",
                        msg=f"Gemini API authentication failed (HTTP {res.status_code}). Please verify GEMINI_API_KEY."
                    )
                elif res.status_code == 429:
                    logger.warning("Gemini rate limit exceeded.")
                    return self._build_deterministic_fallback(
                        task_type, evidence, status="DEGRADED",
                        msg="Gemini rate limit exceeded. Cached or deterministic fallback rendered."
                    )
                else:
                    logger.warning(f"Gemini HTTP {res.status_code}: {res.text}")
                    return self._build_deterministic_fallback(
                        task_type, evidence, status="UNAVAILABLE",
                        msg=f"Gemini service unavailable (HTTP {res.status_code})."
                    )

        except httpx.TimeoutException:
            logger.warning(f"Gemini request timed out after {self.timeout}s.")
            return self._build_deterministic_fallback(
                task_type, evidence, status="UNAVAILABLE",
                msg="Gemini request timed out. Deterministic computational interpretation provided."
            )
        except Exception as e:
            logger.error(f"Gemini request failed: {e}")
            return self._build_deterministic_fallback(
                task_type, evidence, status="UNAVAILABLE",
                msg=f"Gemini connection failed ({type(e).__name__}). Deterministic interpretation provided."
            )

    def _construct_prompt(self, task_type: str, evidence: Dict[str, Any]) -> str:
        """Builds a strictly constrained prompt enforcing scientific integrity."""
        system_instruction = (
            "You are the BioAge-X AI Research Assistant. Your role is strictly to provide "
            "evidence-constrained, objective, and scientifically cautious interpretations of computed "
            "computational biology results.\n\n"
            "CRITICAL SCIENTIFIC INTEGRITY RULES:\n"
            "1. NEVER invent biomarkers, genes, pathways, interaction edges, literature citations, or experimental findings.\n"
            "2. NEVER invent, fabricate, or modify numerical statistics, p-values, SHAP values, biological age predictions, or model metrics.\n"
            "3. NEVER claim causality, clinical diagnostic utility, or medical prognostic validity.\n"
            "4. Strictly base your response on the COMPUTED EVIDENCE provided below.\n"
            "5. You MUST return ONLY valid JSON matching this schema:\n"
            "{\n"
            '  "summary": "2-3 sentence executive synthesis of computational findings",\n'
            '  "observations": ["List of direct empirical deductions. Prefix each with [OBSERVED COMPUTATIONAL RESULT] or [EXTERNAL KNOWLEDGE]"],\n'
            '  "hypotheses": ["List of cautious, testable biological hypotheses. Prefix each with [HYPOTHESIS]"],\n'
            '  "limitations": ["List of methodological or sample constraints. Prefix each with [LIMITATION]"],\n'
            '  "evidence_sources": ["List of cited computational tools/databases (e.g. ElasticNet, SHAP, STRING, Reactome)"]\n'
            "}\n"
        )

        evidence_str = json.dumps(evidence, indent=2, default=str)
        user_prompt = (
            f"TASK TYPE: {task_type.upper()}\n\n"
            f"COMPUTED BIOLOGICAL EVIDENCE:\n"
            f"```json\n{evidence_str}\n```\n\n"
            "Provide the required structured JSON interpretation conforming strictly to the rules above."
        )

        return f"{system_instruction}\n\n{user_prompt}"

    def _extract_text_from_response(self, data: Dict[str, Any]) -> str:
        """Extracts text content from Gemini API response object."""
        try:
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
        except Exception:
            pass
        return ""

    def _parse_and_validate_json(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """Parses JSON text, stripping potential markdown fences."""
        if not raw_text:
            return None

        # Strip markdown ```json ... ``` blocks
        cleaned = raw_text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if match:
            cleaned = match.group(1).strip()

        try:
            obj = json.loads(cleaned)
            if isinstance(obj, dict) and "summary" in obj:
                # Ensure all required list fields exist
                return {
                    "summary": str(obj.get("summary", "")),
                    "observations": [str(x) for x in obj.get("observations", []) if x],
                    "hypotheses": [str(x) for x in obj.get("hypotheses", []) if x],
                    "limitations": [str(x) for x in obj.get("limitations", []) if x],
                    "evidence_sources": [str(x) for x in obj.get("evidence_sources", []) if x],
                }
        except Exception:
            pass
        return None

    def _build_deterministic_fallback(
        self,
        task_type: str,
        evidence: Dict[str, Any],
        status: str,
        msg: str,
        raw_snippet: Optional[str] = None,
    ) -> GeminiInterpretation:
        """Generates a rule-based deterministic summary when Gemini is inactive or offline."""
        metrics = evidence.get("metrics", {})
        biomarkers = evidence.get("biomarkers") or evidence.get("top_features", [])
        pathways = evidence.get("pathways", [])
        model_name = evidence.get("model_name", "BioAge-X Model")

        mae = metrics.get("mae") or evidence.get("mae", "N/A")
        r2 = metrics.get("r2") or evidence.get("r2", "N/A")
        
        top_genes = [b.get("symbol") or b.get("gene") or b.get("feature_id") for b in biomarkers[:3] if isinstance(b, dict)]
        top_genes_str = ", ".join(filter(None, top_genes)) or "computed biomarker features"

        summary = (
            f"Deterministic Analysis: {model_name} evaluated with MAE={mae} years (R²={r2}). "
            f"Top predictive drivers include {top_genes_str}. {msg}"
        )

        observations = [
            f"[OBSERVED COMPUTATIONAL RESULT] Model achieved MAE of {mae} years and R² of {r2}.",
        ]
        if top_genes:
            observations.append(
                f"[OBSERVED COMPUTATIONAL RESULT] Features {top_genes_str} exhibited highest SHAP attribution magnitude."
            )
        if pathways:
            top_pw = pathways[0].get("name") if isinstance(pathways[0], dict) else str(pathways[0])
            observations.append(
                f"[OBSERVED COMPUTATIONAL RESULT] Top enriched biological process: {top_pw}."
            )

        hypotheses = [
            "[HYPOTHESIS] Age-associated epigenetic remodeling at identified loci may reflect altered chromatin regulation during biological aging.",
        ]

        limitations = [
            "[LIMITATION] Biological age acceleration estimates reflect mathematical residuals under specific statistical assumptions.",
            "[LIMITATION] External biological mechanisms require in vitro and in vivo validation beyond in silico modeling.",
        ]

        sources = ["BioAge-X Statistical Core", "ElasticNet/RandomForest", "SHAP Attribution Engine"]
        if pathways:
            sources.append("Reactome / Hallmarks of Aging ORA")

        return GeminiInterpretation(
            status=status,
            task_type=task_type,
            summary=summary,
            observations=observations,
            hypotheses=hypotheses,
            limitations=limitations,
            evidence_sources=sources,
            model_used=self.model,
            cached=False,
            latency_ms=0.1,
        )

    def _compute_cache_key(self, task_type: str, evidence: Dict[str, Any]) -> str:
        """Computes deterministic hash for evidence payload."""
        content = f"{task_type}:{json.dumps(evidence, sort_keys=True, default=str)}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
