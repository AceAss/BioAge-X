"""
Logging utility for BioAge-X.
Provides structured, leveled logging for pipeline operations.
"""

import logging
import sys
from typing import Optional


def get_logger(name: str = "bioage", level: Optional[int] = None) -> logging.Logger:
    """Get or configure a logger with standard scientific formatting."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level or logging.INFO)
    return logger
