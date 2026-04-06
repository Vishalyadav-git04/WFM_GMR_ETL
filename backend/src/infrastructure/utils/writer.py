from sqlalchemy import Engine
from infrastructure.database.setup import get_engine
from infrastructure.logger import get_logger

log = get_logger("writer")

def init_tables(engine: Engine, base: Any):
    log.info("Initializing database tables...")
    base.metadata.create_all(engine)

def write_kpi(df: Any, table_name: str, engine: Engine):
    log.info("Writing KPI to table: %s", table_name)
    # logic using df.to_sql or similar
    pass
