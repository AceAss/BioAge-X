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

__all__ = [
    "datasets_router",
    "analyses_router",
    "models_router",
    "explainability_router",
    "network_router",
    "gnn_router",
    "pathways_router",
    "reports_router",
    "experiments_router",
    "health_router",
]
