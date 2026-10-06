"""
AI Research Assistant Router for BioAge-X REST API.
Provides evidence-constrained interpretation endpoints using Google Gemini.
Operates strictly as an optional post-processing layer.
Zero secrets are exposed to the client.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from apps.api.core.config import settings
from apps.api.schemas.api_schemas import (
    AIStatusResponse,
    AIInterpretRequest,
    AIInterpretResponse,
)
from bioage.ai.gemini_client import GeminiAssistantClient
from bioage.utils.logger import get_logger

logger = get_logger("apps.api.routers.ai")
router = APIRouter(prefix="/ai", tags=["AI Research Assistant"])


def get_gemini_client() -> GeminiAssistantClient:
    """Dependency provider for Gemini client."""
    return GeminiAssistantClient(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_MODEL,
        enabled=settings.GEMINI_ENABLED,
    )


@router.get("/status", response_model=AIStatusResponse)
def get_ai_status(client: GeminiAssistantClient = Depends(get_gemini_client)):
    """
    Returns operational status of the optional Gemini AI Research Assistant.
    Never exposes API keys or secrets to the client.
    """
    health = client.check_health()
    return AIStatusResponse(
        enabled=client.enabled,
        configured=client.is_configured,
        model=client.model,
        status=health.status,
        message=health.message,
    )


@router.post("/interpret", response_model=AIInterpretResponse)
def interpret_evidence(
    request: AIInterpretRequest,
    client: GeminiAssistantClient = Depends(get_gemini_client),
):
    """
    Interprets supplied computational evidence using Google Gemini.
    If Gemini is disabled, keyless, or times out, a deterministic rule-based
    fallback interpretation is rendered without failing the request or experiment.
    """
    valid_tasks = {
        "explain_results",
        "summarize_experiment",
        "explain_biomarkers",
        "explain_pathways",
        "research_discussion",
        "limitations",
    }
    task = request.task_type if request.task_type in valid_tasks else "explain_results"

    result = client.interpret(
        task_type=task,
        evidence=request.evidence,
        experiment_id=request.experiment_id,
    )

    return AIInterpretResponse(
        status=result.status,
        task_type=result.task_type,
        summary=result.summary,
        observations=result.observations,
        hypotheses=result.hypotheses,
        limitations=result.limitations,
        evidence_sources=result.evidence_sources,
        disclaimer=result.disclaimer,
        model_used=result.model_used,
        cached=result.cached,
        latency_ms=result.latency_ms,
    )
