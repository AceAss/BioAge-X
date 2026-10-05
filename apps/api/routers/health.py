"""
Health check router for BioAge-X API.
Reports runtime status, engine readiness, and dependency capabilities.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.api.core.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Validates API health and subsystem dependencies."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    import torch
    import sklearn
    import networkx
    import xgboost

    return {
        "status": "healthy" if db_ok else "degraded",
        "platform": "BioAge-X",
        "version": "0.1.0",
        "database_connected": db_ok,
        "backends": {
            "torch": torch.__version__,
            "torch_cuda": torch.cuda.is_available(),
            "scikit_learn": sklearn.__version__,
            "xgboost": xgboost.__version__,
            "networkx": networkx.__version__,
        },
    }
