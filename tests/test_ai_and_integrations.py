"""
Tests for External Service Authentication, Keyless Operations,
and Google Gemini AI Assistant Integration.
Validates:
- Keyless public operation of STRING, Reactome, Ensembl, and default NCBI
- Optional NCBI_API_KEY behavior and rate limit switching
- Gemini AI disabled, keyless, mocked enabled, timeout, and malformed fallback behaviors
- Strict secret isolation ensuring API keys never leak into API responses or frontend
"""

import json
import pytest
from unittest.mock import patch, MagicMock
import httpx
from starlette.testclient import TestClient

from apps.api.main import app
from apps.api.core.config import settings
from bioage.integrations.string_client import STRINGClient
from bioage.integrations.reactome_client import ReactomeClient
from bioage.integrations.ensembl_client import EnsemblClient
from bioage.integrations.ncbi_client import NCBIClient
from bioage.ai.gemini_client import GeminiAssistantClient, GeminiInterpretation

client = TestClient(app)


# =============================================================================
# 1. KEYLESS PUBLIC SERVICE OPERATION TESTS
# =============================================================================

def test_keyless_public_service_operations():
    """Validates that public bioinformatics services operate without any API key."""
    string = STRINGClient()
    reactome = ReactomeClient()
    ensembl = EnsemblClient()
    ncbi_default = NCBIClient()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"ping": 1}
    mock_resp.text = "113"

    with patch("httpx.Client.get", return_value=mock_resp):
        # None require API keys
        assert string.check_health().status in ("AVAILABLE_NO_KEY", "available", "AVAILABLE")
        assert reactome.check_health().status in ("AVAILABLE_NO_KEY", "available", "AVAILABLE")
        assert ensembl.check_health().status in ("AVAILABLE_NO_KEY", "available", "AVAILABLE")
    
    # Default NCBI operates keyless at 3 req/s
    assert ncbi_default.api_key is None or ncbi_default.api_key == ""
    assert ncbi_default.rate_limiter.interval >= 0.30  # ~3 req/s


def test_ncbi_rate_limit_with_and_without_optional_key():
    """Validates optional NCBI_API_KEY rate-limit adaptation."""
    # Without key: 3 req/s
    client_no_key = NCBIClient(api_key=None)
    assert client_no_key.rate_limiter.interval == pytest.approx(1.0 / 3.0, rel=1e-2)

    # With optional key: 10 req/s
    client_with_key = NCBIClient(api_key="test_ncbi_key_123")
    assert client_with_key.rate_limiter.interval == pytest.approx(1.0 / 10.0, rel=1e-2)


# =============================================================================
# 2. GEMINI AI ASSISTANT BEHAVIOR TESTS
# =============================================================================

def test_gemini_disabled_by_default():
    """Validates that Gemini is completely disabled by default with zero crashes."""
    ai_client = GeminiAssistantClient(enabled=False)
    health = ai_client.check_health()
    assert health.status == "DISABLED"
    assert "disabled" in health.message.lower()

    # Interpretation produces clean deterministic fallback without errors
    res = ai_client.interpret(
        task_type="explain_results",
        evidence={"metrics": {"mae": 2.3, "r2": 0.97}, "model_name": "RandomForest"},
    )
    assert res.status == "DISABLED"
    assert "disabled" in res.summary.lower()
    assert len(res.observations) > 0
    assert len(res.limitations) > 0
    assert "AI-generated" in res.disclaimer


def test_gemini_auth_required_when_enabled_without_key():
    """Validates clear AUTH_REQUIRED status when enabled but key is missing."""
    ai_client = GeminiAssistantClient(enabled=True, api_key="")
    health = ai_client.check_health()
    assert health.status == "AUTH_REQUIRED"

    res = ai_client.interpret(
        task_type="summarize_experiment",
        evidence={"metrics": {"mae": 0.56, "r2": 0.998}},
    )
    assert res.status == "AUTH_REQUIRED"
    assert "GEMINI_API_KEY" in res.summary


def test_gemini_mocked_live_success():
    """Validates structured schema parsing on valid Gemini API response."""
    ai_client = GeminiAssistantClient(enabled=True, api_key="test_valid_key")

    mock_gemini_json = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "summary": "Model demonstrates high predictive accuracy across the cohort.",
                                "observations": [
                                    "[OBSERVED COMPUTATIONAL RESULT] MAE reached 2.3 years.",
                                    "[EXTERNAL KNOWLEDGE] ELOVL2 elongation is widely implicated in human aging."
                                ],
                                "hypotheses": [
                                    "[HYPOTHESIS] Lipid elongation dynamics may modulate cell membrane aging."
                                ],
                                "limitations": [
                                    "[LIMITATION] Cross-sectional analysis cannot confirm longitudinal trajectory."
                                ],
                                "evidence_sources": ["BioAge-X RandomForest", "SHAP Engine", "Reactome"]
                            })
                        }
                    ]
                }
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_gemini_json

    with patch("httpx.Client.post", return_value=mock_response):
        res = ai_client.interpret(
            task_type="explain_results",
            evidence={
                "metrics": {"mae": 2.3, "r2": 0.975},
                "biomarkers": [{"feature_id": "cg16867657_ELOVL2", "symbol": "ELOVL2", "shap_value": 3.4}],
            },
        )
        assert res.status == "AVAILABLE_WITH_KEY"
        assert "Model demonstrates high predictive accuracy" in res.summary
        assert len(res.observations) == 2
        assert len(res.hypotheses) == 1
        assert len(res.limitations) == 1
        assert "Reactome" in res.evidence_sources


def test_gemini_malformed_json_fallback():
    """Validates that non-JSON output from LLM degrades gracefully to rule-based fallback."""
    ai_client = GeminiAssistantClient(enabled=True, api_key="test_key")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Not a valid JSON response from the LLM."}]}}]
    }

    with patch("httpx.Client.post", return_value=mock_response):
        res = ai_client.interpret(
            task_type="explain_results",
            evidence={"metrics": {"mae": 1.2, "r2": 0.95}},
        )
        assert res.status == "DEGRADED"
        assert len(res.observations) > 0


def test_gemini_timeout_handling():
    """Validates graceful degradation on network timeout."""
    ai_client = GeminiAssistantClient(enabled=True, api_key="test_key")

    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Connection timed out")):
        res = ai_client.interpret(
            task_type="explain_results",
            evidence={"metrics": {"mae": 1.5}},
        )
        assert res.status == "UNAVAILABLE"
        assert "timed out" in res.summary.lower()


def test_gemini_rate_limit_handling():
    """Validates 429 quota handling."""
    ai_client = GeminiAssistantClient(enabled=True, api_key="test_key")

    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.text = "Quota exceeded"

    with patch("httpx.Client.post", return_value=mock_response):
        res = ai_client.interpret(
            task_type="explain_results",
            evidence={"metrics": {"mae": 1.5}},
        )
        assert res.status == "DEGRADED"
        assert "rate limit" in res.summary.lower()


def test_gemini_caching():
    """Validates that repeated requests with identical evidence hit the in-memory cache."""
    ai_client = GeminiAssistantClient(enabled=True, api_key="test_key")

    mock_gemini_json = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": json.dumps({
                        "summary": "Cached test summary",
                        "observations": ["Obs 1"],
                        "hypotheses": ["Hyp 1"],
                        "limitations": ["Lim 1"],
                        "evidence_sources": ["Src 1"]
                    })
                }]
            }
        }]
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_gemini_json

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        evidence = {"metrics": {"mae": 3.0}}
        # Call 1: misses cache, invokes API
        r1 = ai_client.interpret("explain_results", evidence)
        assert r1.cached is False
        assert mock_post.call_count == 1

        # Call 2: hits cache, does not invoke API
        r2 = ai_client.interpret("explain_results", evidence)
        assert r2.cached is True
        assert mock_post.call_count == 1
        assert r2.summary == "Cached test summary"


# =============================================================================
# 3. SECRET ISOLATION & API ENDPOINT TESTS
# =============================================================================

def test_secret_isolation_in_api_endpoints():
    """Ensures secret API keys NEVER leak into API responses or headers."""
    secret_gemini = "AIzaSy_SUPER_SECRET_GEMINI_KEY_999"
    secret_ncbi = "NCBI_SUPER_SECRET_KEY_888"

    with patch.object(settings, "GEMINI_API_KEY", secret_gemini), \
         patch.object(settings, "NCBI_API_KEY", secret_ncbi), \
         patch.object(settings, "GEMINI_ENABLED", True):

        # 1. Check AI status endpoint
        res_ai = client.get("/api/v1/ai/status")
        assert res_ai.status_code == 200
        ai_data = res_ai.json()
        assert secret_gemini not in json.dumps(ai_data)
        assert secret_ncbi not in json.dumps(ai_data)
        assert ai_data["configured"] is True

        # 2. Check Integrations health endpoint
        res_health = client.get("/api/v1/integrations/health")
        assert res_health.status_code == 200
        health_data = res_health.json()
        assert secret_gemini not in json.dumps(health_data)
        assert secret_ncbi not in json.dumps(health_data)

        # 3. Check AI interpret endpoint
        res_interpret = client.post(
            "/api/v1/ai/interpret",
            json={"task_type": "explain_results", "evidence": {"metrics": {"mae": 2.0}}},
        )
        assert res_interpret.status_code == 200
        interpret_data = res_interpret.json()
        assert secret_gemini not in json.dumps(interpret_data)
        assert secret_ncbi not in json.dumps(interpret_data)
