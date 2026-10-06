"""Routers package."""
from apps.api.routers.datasets import router as datasets_router
from apps.api.routers.analyses import router as analyses_router
from apps.api.routers.models import router as models_router
from apps.api.routers.explainability import router as explainability_router
from apps.api.routers.network import router as network_router
from apps.api.routers.gnn import router as gnn_router
from apps.api.routers.pathways import router as pathways_router
from apps.api.routers.reports import router as reports_router
from apps.api.routers.experiments import router as experiments_router
from apps.api.routers.health import router as health_router
from apps.api.routers.benchmarks import router as benchmarks_router
from apps.api.routers.integrations import router as integrations_router
from apps.api.routers.data_sources import router as data_sources_router
from apps.api.routers.downloads import router as downloads_router
from apps.api.routers.ai import router as ai_router
from apps.api.routers.evaluation import router as evaluation_router

__all__ = [
    "datasets_router",
    "analyses_router",
    "models_router",
    "benchmarks_router",
    "explainability_router",
    "network_router",
    "gnn_router",
    "pathways_router",
    "reports_router",
    "experiments_router",
    "health_router",
    "integrations_router",
    "data_sources_router",
    "downloads_router",
    "ai_router",
    "evaluation_router",
]
