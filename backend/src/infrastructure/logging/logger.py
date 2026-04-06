"""
Structured logging for the ETL pipeline.
"""

import logging
import sys


def get_logger(name: str = "etl") -> logging.Logger:
    """Return a configured logger with timestamp + level formatting."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)

    return logger
