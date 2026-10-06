"""
Data Sources and Repository Registry Router for BioAge-X REST API.
Exposes supported biological repositories, connector capabilities, and access requirements.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException

from apps.api.schemas.api_schemas import DataSourceSummarySchema
from bioage.acquisition.registry import DatasetProviderRegistry
from bioage.utils.logger import get_logger

logger = get_logger("apps.api.routers.data_sources")
router = APIRouter(prefix="/data-sources", tags=["Data Sources"])


@router.get("", response_model=List[DataSourceSummarySchema])
def list_data_sources():
    """Lists all registered biological repository providers and their operational capabilities."""
    registry = DatasetProviderRegistry.get_instance()
    return registry.get_capabilities_table()


@router.get("/{provider}")
def get_data_source(provider: str):
    """Retrieves detailed configuration and accession patterns for a specific repository."""
    registry = DatasetProviderRegistry.get_instance()
    p = registry.get(provider)
    if not p:
        raise HTTPException(
            status_code=404,
            detail=f"Biological data source '{provider}' not found in registry.",
        )
    return {
        "repository": p.name,
        "category": p.category,
        "description": p.description,
        "access_type": p.access_type.value,
        "supported_accessions": p.supported_accession_patterns,
    }
