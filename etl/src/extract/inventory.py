"""
Extract inventory data from CSV.
"""

import polars as pl
from infrastructure.config.settings import INVENTORY_TABLE
from infrastructure.database.setup import get_engine
from infrastructure.utils.date_parser import parse_mixed_dates
from infrastructure.logging.logger import get_logger

log = get_logger("extract.inventory")


def extract_inventory() -> pl.LazyFrame:
    """Load the inventory data from database and parse date columns."""
    log.info("Reading inventory from table: %s", INVENTORY_TABLE)

    # Use project AS "Project" mapping to preserve downstream logic
    query = f'SELECT *, project AS "Project" FROM {INVENTORY_TABLE}'

    df = pl.read_database(
        query=query,
        connection=get_engine(),
    )

    # Convert to LazyFrame for consistent pipeline logic
    df = df.lazy()

    df = df.with_columns(
        parsed_DIDate=parse_mixed_dates("DIDate"),
        parsed_InstalledTS=parse_mixed_dates("InstalledTS"),
    )

    log.info("Inventory LazyFrame ready")
    return df
