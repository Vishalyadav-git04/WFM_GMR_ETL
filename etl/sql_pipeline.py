"""
Parallel SQL ETL Pipeline Orchestrator.
This runs strictly database-level push-down queries and writes
to the shadow `sql_` tables.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Ensure etl/src/ is on the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from infrastructure.logging.logger import get_logger
from infrastructure.database.setup import get_engine
from adapters.repository.sql_models import Base
from modules.mi.sql_transform import (
    execute_kpi_1_mi_progress,
    execute_kpi_2_mi_productivity,
    execute_kpi_3_monthly_productivity,
    execute_kpi_4_5_inventory_utilization,
    execute_kpi_6_stock_ageing,
    execute_kpi_7_mi_vs_sat,
    execute_kpi_8_non_sat_ageing,
    execute_kpi_9_meter_journey,
    execute_kpi_10_meter_stage,
    execute_command_center_kpi,
    execute_command_center_trend,
    execute_command_center_milestones
)
from modules.om.sql_transform import (
    execute_om_productivity_team,
    execute_om_productivity_trend,
    execute_om_open_ageing,
    execute_om_avg_closure_time,
    execute_om_closed_analysis
)

log = get_logger("sql_pipeline")

def init_sql_tables():
    """Create the sql_ prefixed shadow tables in the database."""
    log.info("Creating shadow SQL tables if they don't exist...")
    engine = get_engine()
    Base.metadata.create_all(engine)
    log.info("Shadow SQL tables exist.")


def run_mi_sql_pipeline():
    """Execute all MI SQL aggregations directly in the DB."""
    log.info("=== MI SQL Push-down Pipeline started ===")
    engine = get_engine()
    
    # Execute MI KPIs
    execute_kpi_1_mi_progress(engine)
    execute_kpi_2_mi_productivity(engine)
    execute_kpi_3_monthly_productivity(engine)
    execute_kpi_4_5_inventory_utilization(engine)
    execute_kpi_6_stock_ageing(engine)
    execute_kpi_7_mi_vs_sat(engine)
    execute_kpi_8_non_sat_ageing(engine)
    execute_kpi_9_meter_journey(engine)
    execute_kpi_10_meter_stage(engine)
    
    # Execute Dashboard
    execute_command_center_kpi(engine)
    execute_command_center_trend(engine)
    execute_command_center_milestones(engine)
    
    log.info("=== MI SQL Push-down Pipeline finished ===")


def run_om_sql_pipeline():
    """Execute all O&M SQL aggregations directly in the DB."""
    log.info("=== O&M SQL Push-down Pipeline started ===")
    engine = get_engine()
    
    # Execute O&M KPIs
    execute_om_productivity_team(engine)
    execute_om_productivity_trend(engine)
    execute_om_open_ageing(engine)
    execute_om_avg_closure_time(engine)
    execute_om_closed_analysis(engine)
    
    log.info("=== O&M SQL Push-down Pipeline finished ===")


def main():
    parser = argparse.ArgumentParser(description="Parallel SQL Push-down ETL Pipeline")
    parser.add_argument(
        "--pipeline",
        choices=["mi", "om", "all"],
        default="all",
        help="Which pipeline to run (default: all)",
    )
    args = parser.parse_args()

    init_sql_tables()
    start = datetime.now()

    try:
        if args.pipeline in ("mi", "all"):
            run_mi_sql_pipeline()
        
        if args.pipeline in ("om", "all"):
            run_om_sql_pipeline()

    except Exception as e:
        log.exception("SQL Pipeline failed")
        raise

    elapsed = datetime.now() - start
    log.info(f"Total elapsed: {elapsed}")


if __name__ == "__main__":
    main()
