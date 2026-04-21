"""
Native PostgreSQL transformations for O&M KPIs.
These functions execute SQL directly in the database to prevent memory issues.
"""

from sqlalchemy import text
import logging

log = logging.getLogger("extract.sql_transform_om")

def execute_om_productivity_team(engine):
    """KPI 1: Productivity per team."""
    log.info("Executing SQL for O&M KPI 1: Productivity per Team")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_om_productivity_team CASCADE;"))
        
        # 1. Daily
        conn.execute(text("""
        INSERT INTO sql_om_productivity_team (
            project, discom, zone, circle, division, subdivision, substation, feeder, dtr, meter_category,
            technician, agency, period_type, period_value, closed_tickets
        )
        SELECT 
            project, discom, zone, circle, division, 
            sub_division as subdivision, NULL as substation, feeder, dtr, meter_category,
            technician, agency, 'daily', TO_CHAR(closed_date, 'DD-MM-YY'), COUNT(*)
        FROM unified_complaints
        WHERE closed_date IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14;
        """))
        
        # 2. Weekly
        conn.execute(text("""
        INSERT INTO sql_om_productivity_team (
            project, discom, zone, circle, division, subdivision, substation, feeder, dtr, meter_category,
            technician, agency, period_type, period_value, closed_tickets
        )
        SELECT 
            project, discom, zone, circle, division, 
            sub_division as subdivision, NULL as substation, feeder, dtr, meter_category,
            technician, agency, 'weekly', TO_CHAR(DATE_TRUNC('week', closed_date), 'DD-MM-YY'), COUNT(*)
        FROM unified_complaints
        WHERE closed_date IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14;
        """))
        
        # 3. Monthly
        conn.execute(text("""
        INSERT INTO sql_om_productivity_team (
            project, discom, zone, circle, division, subdivision, substation, feeder, dtr, meter_category,
            technician, agency, period_type, period_value, closed_tickets
        )
        SELECT 
            project, discom, zone, circle, division, 
            sub_division as subdivision, NULL as substation, feeder, dtr, meter_category,
            technician, agency, 'monthly', TO_CHAR(DATE_TRUNC('month', closed_date), 'DD-MM-YY'), COUNT(*)
        FROM unified_complaints
        WHERE closed_date IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14;
        """))

def execute_om_productivity_trend(engine):
    """KPI 2: Productivity trend."""
    log.info("Executing SQL for O&M KPI 2: Productivity Trend")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_om_productivity_trend CASCADE;"))
        conn.execute(text("""
        INSERT INTO sql_om_productivity_trend (
            project, discom, zone, circle, division, subdivision, substation, feeder, dtr, meter_category,
            closed_month, total_closed_tickets
        )
        SELECT 
            project, discom, zone, circle, division, 
            sub_division as subdivision, NULL as substation, feeder, dtr, meter_category,
            TO_CHAR(DATE_TRUNC('month', closed_date), 'DD-MM-YY'), COUNT(*)
        FROM unified_complaints
        WHERE closed_date IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11;
        """))

def execute_om_open_ageing(engine):
    """KPI 3: Open ticket ageing."""
    log.info("Executing SQL for O&M KPI 3: Open Ageing")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_om_open_ageing CASCADE;"))
        conn.execute(text("""
        INSERT INTO sql_om_open_ageing (
            project, discom, zone, circle, division, subdivision, substation, feeder, dtr, meter_category,
            ticket_id, created_date, ageing_days, technician, agency
        )
        SELECT 
            project, discom, zone, circle, division, 
            sub_division as subdivision, NULL as substation, feeder, dtr, meter_category,
            ticket_id, created_date, 
            EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_date))/86400.0,
            technician, agency
        FROM unified_complaints
        WHERE closed_date IS NULL;
        """))

def execute_om_avg_closure_time(engine):
    """KPI 4: Avg closure time."""
    log.info("Executing SQL for O&M KPI 4: Avg Closure Time")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_om_avg_closure_time CASCADE;"))
        
        # 1. Daily
        conn.execute(text("""
        INSERT INTO sql_om_avg_closure_time (
            project, discom, zone, circle, division, subdivision, substation, feeder, dtr, meter_category,
            period_type, period_value_created, period_value_closed, avg_resolution_days
        )
        SELECT 
            project, discom, zone, circle, division, 
            sub_division as subdivision, NULL as substation, feeder, dtr, meter_category,
            'daily', TO_CHAR(created_date, 'DD-MM-YY'), TO_CHAR(closed_date, 'DD-MM-YY'),
            AVG(EXTRACT(EPOCH FROM (closed_date - created_date))/86400.0)
        FROM unified_complaints
        WHERE closed_date IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """))

def execute_om_closed_analysis(engine):
    """KPI 5: Closed analysis."""
    log.info("Executing SQL for O&M KPI 5: Closed Analysis")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_om_closed_analysis CASCADE;"))
        
        # 1. Daily
        conn.execute(text("""
        INSERT INTO sql_om_closed_analysis (
            project, discom, zone, circle, division, subdivision, substation, feeder, dtr, meter_category,
            complaint_type, complaint_category, period_type, period_value, closed_tickets
        )
        SELECT 
            project, discom, zone, circle, division, 
            sub_division as subdivision, NULL as substation, feeder, dtr, meter_category,
            complaint_type, complaint_category, 'daily', TO_CHAR(closed_date, 'DD-MM-YY'), COUNT(*)
        FROM unified_complaints
        WHERE closed_date IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14;
        """))
