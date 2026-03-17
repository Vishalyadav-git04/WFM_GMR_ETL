"""
Truncate-and-load writer: collects Polars LazyFrames and bulk-inserts into PostgreSQL.
"""

import polars as pl
from sqlalchemy import text
from load.database import get_engine
from load.models import Base
from utils.logger import get_logger

log = get_logger("load.writer")


def init_tables():
    """Create all tables if they don't exist."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    log.info("Database tables ensured")


def write_kpi(table_name: str, df: pl.DataFrame, column_map: dict[str, str] | None = None):
    """
    Truncate the target table and bulk-insert the DataFrame.

    Args:
        table_name: PostgreSQL table name.
        df: Collected Polars DataFrame.
        column_map: Optional {polars_col: db_col} rename mapping.
    """
    engine = get_engine()

    # Rename columns to match the DB schema
    if column_map:
        df = df.rename(column_map)

    # Convert to pandas for to_sql
    pdf = df.to_pandas()

    # Lowercase all column names to match SQLAlchemy model
    pdf.columns = [c.lower() for c in pdf.columns]

    # Only keep columns that exist in the target table
    from sqlalchemy import inspect as sa_inspect
    inspector = sa_inspect(engine)
    db_columns = {col["name"] for col in inspector.get_columns(table_name)}
    db_columns.discard("id")  # auto-increment, not in DataFrame
    valid_cols = [c for c in pdf.columns if c in db_columns]
    pdf = pdf[valid_cols]

    log.info("Writing %s rows to [%s] …", f"{len(pdf):,}", table_name)

    with engine.begin() as conn:
        conn.execute(text(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE'))
        pdf.to_sql(table_name, conn, if_exists="append", index=False, method="multi", chunksize=5000)

    log.info("[%s] load complete", table_name)
