"""
Native PostgreSQL transformations for O&M KPIs.
These functions execute SQL directly in the database to prevent memory issues.
"""

from sqlalchemy import text
import logging
from infrastructure.config.settings import OM_SOURCE_TABLE

log = logging.getLogger("extract.sql_transform_om")

def execute_om_team_productivity_dashboard(engine):
    """KPI O&M-1: Team Productivity Dashboard Pre-aggregation."""
    log.info("Executing SQL for O&M KPI 1: Team Productivity Dashboard (Pre-aggregation)")
    with engine.begin() as conn:
        # Create table if it doesn't exist (failsafe for local dev if migration missing)
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sql_om_team_productivity_dashboard (
            id BIGSERIAL PRIMARY KEY,
            project VARCHAR(200),
            discom VARCHAR(200),
            zone VARCHAR(200),
            circle VARCHAR(200),
            division VARCHAR(200),
            subdivision VARCHAR(200),
            meter_category VARCHAR(100),
            technician VARCHAR(200),
            closed_day DATE,
            closed_tickets BIGINT
        );
        """))
        
        conn.execute(text("TRUNCATE TABLE sql_om_team_productivity_dashboard CASCADE;"))
        
        conn.execute(text(f"""
        INSERT INTO sql_om_team_productivity_dashboard (
            project, discom, zone, circle, division, subdivision,
            meter_category, technician, closed_day, closed_tickets
        )
        SELECT
            UPPER(TRIM(project)),
            discom,
            zone,
            circle,
            division,
            sub_division,
            UPPER(TRIM(meter_category)),
            COALESCE(NULLIF(TRIM(technician), ''), supervisor) as technician,
            closed_date::date,
            COUNT(*)
        FROM {OM_SOURCE_TABLE}
        WHERE closed_date IS NOT NULL
          AND COALESCE(NULLIF(TRIM(technician), ''), supervisor) IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7,8,9;
        """))

def execute_om_open_ageing(engine):
    """KPI 3: Open ticket ageing."""
    log.info("Executing SQL for O&M KPI 3: Open Ageing")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_om_open_ageing CASCADE;"))
        conn.execute(text(f"""
        INSERT INTO sql_om_open_ageing (
            project, discom, zone, circle, division, subdivision, substation, feeder, dtr, meter_category,
            ticket_id, created_date, ageing_days, technician, agency, complaint_by
        )
        SELECT 
            project, discom, zone, circle, division, 
            sub_division as subdivision, NULL as substation, feeder, dtr, meter_category,
            ticket_id, created_date, 
            EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_date))/86400.0,
            technician, agency, complaint_by
        FROM {OM_SOURCE_TABLE}
        WHERE closed_date IS NULL;
        """))

def execute_om_avg_closure_time(engine):
    """KPI 4: Avg closure time."""
    log.info("Executing SQL for O&M KPI 4: Avg Closure Time")
    with engine.begin() as conn:
        # Drop and recreate to ensure schema updates (adding closed_tickets, closed_date)
        conn.execute(text("DROP TABLE IF EXISTS sql_om_avg_closure_time CASCADE;"))
        conn.execute(text("""
        CREATE TABLE sql_om_avg_closure_time (
            id BIGSERIAL PRIMARY KEY,
            project VARCHAR(200),
            discom VARCHAR(200),
            zone VARCHAR(200),
            circle VARCHAR(200),
            division VARCHAR(200),
            subdivision VARCHAR(200),
            substation VARCHAR(200),
            feeder VARCHAR(200),
            dtr VARCHAR(200),
            meter_category VARCHAR(100),
            period_type VARCHAR(10),
            period_value_created VARCHAR(50),
            period_value_closed VARCHAR(50),
            avg_resolution_days FLOAT,
            closed_tickets BIGINT,
            closed_date DATE
        );
        """))
        
        # 1. Daily
        conn.execute(text(f"""
        INSERT INTO sql_om_avg_closure_time (
            project, discom, zone, circle, division, subdivision, substation, feeder, dtr, meter_category,
            period_type, period_value_created, period_value_closed, avg_resolution_days,
            closed_tickets, closed_date
        )
        SELECT 
            project, discom, zone, circle, division, 
            sub_division as subdivision, NULL as substation, feeder, dtr, meter_category,
            'daily', TO_CHAR(created_date, 'DD-MM-YY'), TO_CHAR(closed_date, 'DD-MM-YY'),
            AVG(EXTRACT(EPOCH FROM (closed_date - created_date))/86400.0),
            COUNT(*),
            closed_date::date
        FROM {OM_SOURCE_TABLE}
        WHERE closed_date IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13,16;
        """))


def execute_om_closed_analysis(engine):
    """KPI 5: Closed analysis."""
    log.info("Executing SQL for O&M KPI 5: Closed Analysis")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_om_closed_analysis CASCADE;"))
        
        # 1. Daily
        conn.execute(text(f"""
        INSERT INTO sql_om_closed_analysis (
            project, discom, zone, circle, division, subdivision, substation, feeder, dtr, meter_category,
            complaint_type, complaint_category, period_type, period_value, closed_tickets
        )
        SELECT 
            project, discom, zone, circle, division, 
            sub_division as subdivision, NULL as substation, feeder, dtr, meter_category,
            complaint_type, complaint_category, 'daily', TO_CHAR(closed_date, 'DD-MM-YY'), COUNT(*)
        FROM {OM_SOURCE_TABLE}
        WHERE closed_date IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14;
        """))
