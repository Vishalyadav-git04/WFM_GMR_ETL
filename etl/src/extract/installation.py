"""
Extract installation data from CSV.
"""

import polars as pl
from infrastructure.config.settings import INSTALL_TABLE
from infrastructure.database.setup import get_engine
from infrastructure.utils.date_parser import parse_mixed_dates
from infrastructure.logging.logger import get_logger

log = get_logger("extract.installation")


def extract_installation() -> pl.LazyFrame:
    """Load the installation data from database and parse date columns."""
    log.info("Reading installation from table: %s", INSTALL_TABLE)

    query = f"SELECT * FROM {INSTALL_TABLE}"
    
    # Use read_database to pull data from PG
    df = pl.read_database(
        query=query,
        connection=get_engine(),
    )

    # Convert to LazyFrame for consistent pipeline logic
    df = df.lazy()

    df = df.with_columns(
        parsed_install_date=parse_mixed_dates("installationDate"),
    )

    log.info("Installation LazyFrame ready")
    return df
