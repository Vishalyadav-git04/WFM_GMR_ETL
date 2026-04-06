from sqlalchemy import Engine, text
from infrastructure.database.setup import get_engine
from infrastructure.logging.logger import get_logger
import polars as pl
import pandas as pd

log = get_logger("writer")

def init_tables(engine: Engine, base: any):
    log.info("Initializing database tables...")
    base.metadata.create_all(engine)

def write_kpi(table_name: str, df: pl.DataFrame, column_map: dict[str, str] | None = None):
    engine = get_engine()

    if column_map:
        df = df.rename(column_map)

    pdf = df.to_pandas()
    pdf.columns = [c.lower() for c in pdf.columns]

    from sqlalchemy import inspect as sa_inspect
    inspector = sa_inspect(engine)
    db_columns = {col["name"] for col in inspector.get_columns(table_name)}
    db_columns.discard("id")
    valid_cols = [c for c in pdf.columns if c in db_columns]
    pdf = pdf[valid_cols]

    log.info("Writing %s rows to [%s] ...", f"{len(pdf):,}", table_name)

    with engine.begin() as conn:
        conn.execute(text(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE'))
        pdf.to_sql(table_name, conn, if_exists="append", index=False, method="multi", chunksize=5000)

    log.info("[%s] load complete", table_name)
