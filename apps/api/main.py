"""
BioAge-X Backend API Server.
Main entry point orchestrating datasets, preprocessing, machine learning,
explainability, network biology, GNNs, and research reporting.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.core.config import settings
from apps.api.core.database import Base, engine, SessionLocal
from apps.api.models.db_models import DatasetRecord
from apps.api.routers import (
    datasets_router,
    analyses_router,
    models_router,
    benchmarks_router,
    explainability_router,
    network_router,
    gnn_router,
    pathways_router,
    reports_router,
    experiments_router,
    health_router,
    integrations_router,
)
from bioage.utils.logger import get_logger

logger = get_logger("apps.api.main")

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Explainable Multi-Omics Biological Age Estimation & Network Biology Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /api/v1
api_prefix = settings.API_V1_STR
app.include_router(health_router, prefix=api_prefix)
app.include_router(integrations_router, prefix=api_prefix)
app.include_router(datasets_router, prefix=api_prefix)
app.include_router(analyses_router, prefix=api_prefix)
app.include_router(models_router, prefix=api_prefix)
app.include_router(benchmarks_router, prefix=api_prefix)
app.include_router(explainability_router, prefix=api_prefix)
app.include_router(network_router, prefix=api_prefix)
app.include_router(gnn_router, prefix=api_prefix)
app.include_router(pathways_router, prefix=api_prefix)
app.include_router(reports_router, prefix=api_prefix)
app.include_router(experiments_router, prefix=api_prefix)

# Also expose health check at root /health for docker/load-balancers
app.include_router(health_router)


@app.on_event("startup")
def on_startup():
    logger.info("=== BioAge-X Backend API Server Initialized ===")
    logger.info(f"Connected to database: {settings.DATABASE_URL}")

    # Auto-seed demo dataset if not already present
    db = SessionLocal()
    try:
        existing = db.query(DatasetRecord).filter(DatasetRecord.name == "demo_multiomics.csv").first()
        if not existing:
            demo_path = settings.EXAMPLE_DIR / "demo_multiomics.csv"
            if not demo_path.exists():
                from scripts.generate_demo_data import main as gen_demo
                gen_demo()
            from apps.api.routers.datasets import load_demo_dataset
            load_demo_dataset(db)
            logger.info("Auto-seeded synthetic demo multi-omics dataset into platform database.")
    except Exception as e:
        logger.warning(f"Startup demo seed check warning: {e}")
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "message": "Welcome to BioAge-X: Explainable Multi-Omics Biological Age Estimation Platform",
        "version": "0.1.0",
        "docs": "/docs",
        "api_v1": "/api/v1",
        "tagline": "From molecular signals to biological age.",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.main:app", host="0.0.0.0", port=8000, reload=True)
