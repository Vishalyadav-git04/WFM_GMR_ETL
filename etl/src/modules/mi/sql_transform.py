"""
Native PostgreSQL transformations for MI KPIs.
These functions execute SQL directly in the database to prevent memory issues.
"""

from sqlalchemy import text
import logging

log = logging.getLogger("extract.sql_transform")




def execute_kpi_1_mi_progress(engine):
    """Executes KPI 1 (MI Progress) directly in the database."""
    log.info("Executing SQL for KPI 1: MI Progress")
    
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_mi_progress CASCADE;"))
        
        # 1. Daily
        conn.execute(text(f"""
        INSERT INTO sql_mi_progress (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            period_type, period_value, total_mi_progress
        )
        SELECT 
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, metertype, 
            COALESCE(
                UPPER(TRIM(connection_type)),
                CASE 
                    WHEN metertype = '3PLTCTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'DT'
                    WHEN metertype = 'HTCTPTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'FEEDER'
                    ELSE 'CONSUMER'
                END
            ) as connection_type,
            'daily', TO_CHAR(mi_date, 'DD-MM-YY'), COUNT(*)
        FROM unified_installation_inventory_data
        WHERE mi_date IS NOT NULL AND sat_no IS NOT NULL AND TRIM(sat_no) != ''
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """))
        
        # 2. Weekly (Monday)
        conn.execute(text(f"""
        INSERT INTO sql_mi_progress (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            period_type, period_value, total_mi_progress
        )
        SELECT 
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, metertype, 
            COALESCE(
                UPPER(TRIM(connection_type)),
                CASE 
                    WHEN metertype = '3PLTCTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'DT'
                    WHEN metertype = 'HTCTPTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'FEEDER'
                    ELSE 'CONSUMER'
                END
            ) as connection_type,
            'weekly', TO_CHAR(DATE_TRUNC('week', mi_date), 'DD-MM-YY'), COUNT(*)
        FROM unified_installation_inventory_data
        WHERE mi_date IS NOT NULL AND sat_no IS NOT NULL AND TRIM(sat_no) != ''
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """))
        
        # 3. Monthly (1st)
        conn.execute(text(f"""
        INSERT INTO sql_mi_progress (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            period_type, period_value, total_mi_progress
        )
        SELECT 
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, metertype, 
            COALESCE(
                UPPER(TRIM(connection_type)),
                CASE 
                    WHEN metertype = '3PLTCTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'DT'
                    WHEN metertype = 'HTCTPTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'FEEDER'
                    ELSE 'CONSUMER'
                END
            ) as connection_type,
            'monthly', TO_CHAR(DATE_TRUNC('month', mi_date), 'DD-MM-YY'), COUNT(*)
        FROM unified_installation_inventory_data
        WHERE mi_date IS NOT NULL AND sat_no IS NOT NULL AND TRIM(sat_no) != ''
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """))


def execute_kpi_2_mi_productivity(engine):
    """Executes KPI 2 (MI Productivity) directly in the database."""
    log.info("Executing SQL for KPI 2: MI Productivity")
    
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_mi_productivity CASCADE;"))
        
        # 1. Daily
        conn.execute(text(f"""
        INSERT INTO sql_mi_productivity (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            technician, period_type, period_value, daily_installations
        )
        SELECT 
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, metertype, 
            COALESCE(
                UPPER(TRIM(connection_type)),
                CASE 
                    WHEN metertype = '3PLTCTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'DT'
                    WHEN metertype = 'HTCTPTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'FEEDER'
                    ELSE 'CONSUMER'
                END
            ) as connection_type, technicianname,
            'daily', TO_CHAR(mi_date, 'DD-MM-YY'), COUNT(*)
        FROM unified_installation_inventory_data
        WHERE mi_date IS NOT NULL AND sat_no IS NOT NULL AND TRIM(sat_no) != ''
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14;
        """))
        
        # 2. Weekly
        conn.execute(text(f"""
        INSERT INTO sql_mi_productivity (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            technician, period_type, period_value, daily_installations
        )
        SELECT 
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, metertype, 
            COALESCE(
                UPPER(TRIM(connection_type)),
                CASE 
                    WHEN metertype = '3PLTCTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'DT'
                    WHEN metertype = 'HTCTPTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'FEEDER'
                    ELSE 'CONSUMER'
                END
            ) as connection_type, technicianname,
            'weekly', TO_CHAR(DATE_TRUNC('week', mi_date), 'DD-MM-YY'), COUNT(*)
        FROM unified_installation_inventory_data
        WHERE mi_date IS NOT NULL AND sat_no IS NOT NULL AND TRIM(sat_no) != ''
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14;
        """))
        
        # 3. Monthly
        conn.execute(text(f"""
        INSERT INTO sql_mi_productivity (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            technician, period_type, period_value, daily_installations
        )
        SELECT 
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, metertype, 
            COALESCE(
                UPPER(TRIM(connection_type)),
                CASE 
                    WHEN metertype = '3PLTCTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'DT'
                    WHEN metertype = 'HTCTPTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'FEEDER'
                    ELSE 'CONSUMER'
                END
            ) as connection_type, technicianname,
            'monthly', TO_CHAR(DATE_TRUNC('month', mi_date), 'DD-MM-YY'), COUNT(*)
        FROM unified_installation_inventory_data
        WHERE mi_date IS NOT NULL AND sat_no IS NOT NULL AND TRIM(sat_no) != ''
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14;
        """))


def execute_kpi_3_monthly_productivity(engine):
    """Executes KPI 3 directly in the database."""
    log.info("Executing SQL for KPI 3: Monthly Productivity")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_monthly_productivity CASCADE;"))
        
        sql = f"""
        WITH location_counts AS (
            SELECT 
                project, discom, zone, circle, division, subdivision, 
                substation, feeder, dtr, metertype, 
                COALESCE(
                    UPPER(TRIM(connection_type)),
                    CASE 
                        WHEN metertype = '3PLTCTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'DT'
                        WHEN metertype = 'HTCTPTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'FEEDER'
                        ELSE 'CONSUMER'
                    END
                ) as connection_type,
                TO_CHAR(DATE_TRUNC('month', mi_date), 'DD-MM-YY') as period_val,
                COUNT(*) as loc_count
            FROM unified_installation_inventory_data
            WHERE mi_date IS NOT NULL AND sat_no IS NOT NULL AND TRIM(sat_no) != ''
            GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12
        ),
        total_counts AS (
            SELECT period_val, SUM(loc_count) as tot_count
            FROM location_counts
            GROUP BY period_val
        )
        INSERT INTO sql_monthly_productivity (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            period_type, period_value, location_monthly_installations, total_monthly_installations
        )
        SELECT 
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, metertype, connection_type,
            'monthly', lc.period_val, lc.loc_count, tc.tot_count
        FROM location_counts lc
        JOIN total_counts tc ON lc.period_val = tc.period_val;
        """
        conn.execute(text(sql))


def execute_kpi_4_5_inventory_utilization(engine):
    """Executes KPI 4 & 5 (Inventory Utilization & Pace vs Stock) directly in the database."""
    log.info("Executing SQL for KPI 4 & 5: Inventory Utilization")
    
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_inventory_utilization CASCADE;"))
        
        # Weekly
        conn.execute(text(f"""
        INSERT INTO sql_inventory_utilization (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            period_type, period_value, total_inventory, total_installed, utilization_rate_pct, remaining_stock
        )
        SELECT 
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, metertype, 
            COALESCE(
                UPPER(TRIM(connection_type)),
                CASE 
                    WHEN metertype = '3PLTCTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'DT'
                    WHEN metertype = 'HTCTPTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'FEEDER'
                    ELSE 'CONSUMER'
                END
            ) as connection_type,
            'weekly', TO_CHAR(DATE_TRUNC('week', mi_date), 'DD-MM-YY'),
            COUNT(*),
            COUNT(*) FILTER (WHERE mi_date IS NOT NULL AND sat_no IS NOT NULL AND TRIM(sat_no) != ''),
            CASE WHEN COUNT(*) > 0 THEN COUNT(*) FILTER (WHERE mi_date IS NOT NULL AND sat_no IS NOT NULL AND TRIM(sat_no) != '')::float / COUNT(*)::float * 100 ELSE 0 END,
            COUNT(*) - COUNT(*) FILTER (WHERE mi_date IS NOT NULL AND sat_no IS NOT NULL AND TRIM(sat_no) != '')
        FROM unified_installation_inventory_data
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """))
        
        # Monthly
        conn.execute(text(f"""
        INSERT INTO sql_inventory_utilization (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            period_type, period_value, total_inventory, total_installed, utilization_rate_pct, remaining_stock
        )
        SELECT 
            UPPER(TRIM(project)) as project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, metertype, 
            COALESCE(
                UPPER(TRIM(connection_type)),
                CASE 
                    WHEN metertype = '3PLTCTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'DT'
                    WHEN metertype = 'HTCTPTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'FEEDER'
                    ELSE 'CONSUMER'
                END
            ) as connection_type,
            'monthly', TO_CHAR(DATE_TRUNC('month', COALESCE(didate, mi_date)), 'DD-MM-YY'),
            COUNT(*),
            COUNT(*) FILTER (WHERE mi_date IS NOT NULL AND sat_no IS NOT NULL AND TRIM(sat_no) != ''),
            CASE WHEN COUNT(*) > 0 THEN COUNT(*) FILTER (WHERE mi_date IS NOT NULL AND sat_no IS NOT NULL AND TRIM(sat_no) != '')::float / COUNT(*)::float * 100 ELSE 0 END,
            COUNT(*) - COUNT(*) FILTER (WHERE mi_date IS NOT NULL AND sat_no IS NOT NULL AND TRIM(sat_no) != '')
        FROM unified_installation_inventory_data
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """))

        # KPI 5 (Daily)
        conn.execute(text(f"""
        INSERT INTO sql_inventory_utilization (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            period_type, period_value, total_inventory, total_installed, utilization_rate_pct, remaining_stock
        )
        SELECT 
            UPPER(TRIM(project)) as project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, metertype, 
            COALESCE(
                UPPER(TRIM(connection_type)),
                CASE 
                    WHEN metertype = '3PLTCTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'DT'
                    WHEN metertype = 'HTCTPTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'FEEDER'
                    ELSE 'CONSUMER'
                END
            ) as connection_type,
            'daily', TO_CHAR(COALESCE(didate, mi_date), 'DD-MM-YY'),
            COUNT(*),
            COUNT(*) FILTER (WHERE mi_date IS NOT NULL AND sat_no IS NOT NULL AND TRIM(sat_no) != ''),
            CASE WHEN COUNT(*) > 0 THEN COUNT(*) FILTER (WHERE mi_date IS NOT NULL AND sat_no IS NOT NULL AND TRIM(sat_no) != '')::float / COUNT(*)::float * 100 ELSE 0 END,
            COUNT(*) - COUNT(*) FILTER (WHERE mi_date IS NOT NULL AND sat_no IS NOT NULL AND TRIM(sat_no) != '')
        FROM unified_installation_inventory_data
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """))


def execute_kpi_6_stock_ageing(engine):
    """Executes KPI 6 directly in the database."""
    log.info("Executing SQL for KPI 6: Stock Ageing")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_stock_ageing CASCADE;"))
        
        sql = f"""
        WITH ageing_base AS (
            SELECT 
                project, discom, zone, circle, division, subdivision, 
                substation, feeder, dtr, metertype, 
                COALESCE(
                    UPPER(TRIM(connection_type)),
                    CASE 
                        WHEN metertype = '3PLTCTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'DT'
                        WHEN metertype = 'HTCTPTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'FEEDER'
                        ELSE 'CONSUMER'
                    END
                ) as connection_type,
                didate,
                CURRENT_DATE - didate::date as days_diff
            FROM unified_installation_inventory_data
            WHERE installedts IS NULL AND didate IS NOT NULL
        )
        INSERT INTO sql_stock_ageing (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            period_type, period_value, age_0_30, age_31_60, age_61_90, age_90_plus
        )
        SELECT 
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, metertype, connection_type,
            'monthly', TO_CHAR(DATE_TRUNC('month', didate), 'DD-MM-YY'),
            COUNT(*) FILTER (WHERE days_diff <= 30),
            COUNT(*) FILTER (WHERE days_diff > 30 AND days_diff <= 60),
            COUNT(*) FILTER (WHERE days_diff > 60 AND days_diff <= 90),
            COUNT(*) FILTER (WHERE days_diff > 90)
        FROM ageing_base
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """
        conn.execute(text(sql))


def execute_kpi_7_mi_vs_sat(engine):
    """Executes KPI 7 directly in the DB."""
    log.info("Executing SQL for KPI 7: MI vs SAT")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_mi_vs_sat CASCADE;"))
        
        sql = f"""
        WITH base AS (
            SELECT 
                UPPER(TRIM(project)) as project, discom, zone, circle, division, subdivision, 
                substation, feeder, dtr, metertype, 
                COALESCE(
                    UPPER(TRIM(connection_type)),
                    CASE 
                        WHEN metertype = '3PLTCTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'DT'
                        WHEN metertype = 'HTCTPTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'FEEDER'
                        ELSE 'CONSUMER'
                    END
                ) as connection_type, meterserialnumber,
                LOWER(TRIM(sat_no)) as sat_stage,
                mi_date::date as install_date
            FROM unified_installation_inventory_data
        ),
        pivoted AS (
            SELECT 
                project, discom, zone, circle, division, subdivision, 
                substation, feeder, dtr, metertype, connection_type,
                TO_CHAR(install_date, 'DD-MM-YY') as period_val,
                COUNT(meterserialnumber) as total_mi,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-%') as total_sat,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-1%') as s1,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-2%') as s2,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-3%') as s3,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-4%') as s4,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-5%') as s5,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-6%') as s6,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-7%') as s7,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-8%') as s8,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-9%') as s9
            FROM base
            WHERE install_date IS NOT NULL AND sat_stage IS NOT NULL AND sat_stage != ''
            GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12
        )
        INSERT INTO sql_mi_vs_sat (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            period_type, period_value, total_mi, total_sat, 
            sat_1, sat_2, sat_3, sat_4, sat_5, sat_6, sat_7, sat_8, sat_9, sat_progress_pct
        )
        SELECT 
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, metertype, connection_type,
            'daily', period_val, 
            total_mi, total_sat, s1, s2, s3, s4, s5, s6, s7, s8, s9,
            CASE WHEN total_mi > 0 THEN (total_sat::float / total_mi::float * 100) ELSE 0 END
        FROM pivoted;
        """
        conn.execute(text(sql))


def execute_kpi_8_non_sat_ageing(engine):
    """Executes KPI 8 (Non-SAT Ageing) directly in the database."""
    log.info("Executing SQL for MI KPI 8: Non-SAT Ageing")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_non_sat_ageing CASCADE;"))
        
        sql = f"""
        INSERT INTO sql_non_sat_ageing (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category,
            meter_serial_number, installation_date, ageing_days
        )
        SELECT 
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, metertype, 
            COALESCE(
                UPPER(TRIM(connection_type)),
                CASE 
                    WHEN metertype = '3PLTCTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'DT'
                    WHEN metertype = 'HTCTPTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'FEEDER'
                    ELSE 'CONSUMER'
                END
            ),
            meterserialnumber,
            mi_date::date,
            CURRENT_DATE - mi_date::date
        FROM unified_installation_inventory_data
        WHERE mi_date IS NOT NULL AND sat_no IS NOT NULL AND TRIM(sat_no) != ''
          AND (LOWER(TRIM(sat_no)) NOT LIKE 'sat-%');
        """
        conn.execute(text(sql))
def execute_kpi_9_meter_journey(engine):
    """Executes KPI 9 (Meter Journey Avg Time) directly in the database."""
    log.info("Executing SQL for MI KPI 9: Meter Journey Avg Time")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_meter_journey_avg_time CASCADE;"))

        _mj_dims = """
            project, discom, zone, circle, division, subdivision,
            substation, feeder, dtr, new_meter_type, meter_category,
            period_type, period_value,
            inventory_to_store, store_to_agency, agency_to_meter_installation,
            meter_installation_to_sat, sat_to_invoice, invoice_to_revenue,
            total_journey, meter_count
        """
        _mj_cat = """
            COALESCE(
                UPPER(TRIM(connection_type)),
                CASE
                    WHEN metertype = '3PLTCTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'DT'
                    WHEN metertype = 'HTCTPTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'FEEDER'
                    ELSE 'CONSUMER'
                END
            )
        """
        _mj_avgs = """
            AVG(gmrtoagencyts::date - didate::date),
            AVG(agencytosupts::date - gmrtoagencyts::date),
            AVG(installedts::date - agencytosupts::date),
            AVG(sat_date::date - installedts::date),
            AVG(pmpm_invoice_date::date - sat_date::date),
            AVG(pmpm_collection_date::date - pmpm_invoice_date::date),
            AVG(pmpm_collection_date::date - didate::date),
            COUNT(*)
        """
        _mj_where = """
        FROM unified_installation_inventory_data
        WHERE pmpm_collection_date IS NOT NULL
          AND sat_date <= (SELECT MAX(sat_date) FROM unified_installation_inventory_data)
        """

        conn.execute(text(f"""
        INSERT INTO sql_meter_journey_avg_time ({_mj_dims.strip()})
        SELECT
            project, discom, zone, circle, division, subdivision,
            substation, feeder, dtr, metertype,
            {_mj_cat.strip()},
            'weekly', TO_CHAR(DATE_TRUNC('week', pmpm_collection_date::timestamp), 'DD-MM-YY'),
            {_mj_avgs.strip()}
        {_mj_where.strip()}
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """))

        conn.execute(text(f"""
        INSERT INTO sql_meter_journey_avg_time ({_mj_dims.strip()})
        SELECT
            project, discom, zone, circle, division, subdivision,
            substation, feeder, dtr, metertype,
            {_mj_cat.strip()},
            'monthly', TO_CHAR(DATE_TRUNC('month', pmpm_collection_date::timestamp), 'DD-MM-YY'),
            {_mj_avgs.strip()}
        {_mj_where.strip()}
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """))

        conn.execute(text(f"""
        INSERT INTO sql_meter_journey_avg_time ({_mj_dims.strip()})
        SELECT
            project, discom, zone, circle, division, subdivision,
            substation, feeder, dtr, metertype,
            {_mj_cat.strip()},
            'daily', TO_CHAR(pmpm_collection_date::date, 'DD-MM-YY'),
            {_mj_avgs.strip()}
        {_mj_where.strip()}
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """))


def execute_kpi_10_meter_stage(engine):
    """Populates sql_meter_current_stage with pre-aggregated funnel metrics (Inventory → Installed → SAT → Revenue)."""
    log.info("Executing ETL for KPI 10: Meter Funnel Summary")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_meter_current_stage CASCADE;"))
        
        sql = """
        INSERT INTO sql_meter_current_stage (
            project, discom, zone, circle, division, subdivision,
            substation, feeder, dtr, new_meter_type, meter_category,
            inventory, installed, sat_done, revenue_collected
        )
        SELECT 
            UPPER(TRIM(project)) as project,
            discom, 
            zone, 
            circle, 
            division, 
            subdivision,
            substation, 
            feeder, 
            dtr,
            metertype as new_meter_type,
            COALESCE(
                UPPER(TRIM(connection_type)),
                CASE 
                    WHEN metertype = '3PLTCTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'DT'
                    WHEN metertype = 'HTCTPTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'FEEDER'
                    ELSE 'CONSUMER'
                END
            ) as meter_category,
            COUNT(*) as inventory,
            COUNT(*) FILTER (WHERE mi_date IS NOT NULL AND sat_no IS NOT NULL AND TRIM(sat_no) != '') as installed,
            COUNT(*) FILTER (WHERE sat_date IS NOT NULL) as sat_done,
            COUNT(*) FILTER (WHERE pmpm_collection_date IS NOT NULL) as revenue_collected
        FROM unified_installation_inventory_data
        GROUP BY 
            UPPER(TRIM(project)), discom, zone, circle, division, subdivision,
            substation, feeder, dtr, metertype,
            COALESCE(
                UPPER(TRIM(connection_type)),
                CASE 
                    WHEN metertype = '3PLTCTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'DT'
                    WHEN metertype = 'HTCTPTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'FEEDER'
                    ELSE 'CONSUMER'
                END
            );
        """
        conn.execute(text(sql))
        log.info("KPI 10 Funnel Summary ETL completed")


def execute_command_center_kpi(engine):
    """Executes the specialized dashboard logic for Command Center."""
    log.info("Executing SQL for Command Center Dashboard Snapshot")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE dashboard_command_center CASCADE;"))

        sql = f"""
        WITH combined AS (
            SELECT
                UPPER(TRIM(project)) as project_name,
                COUNT(*) as inventory,
                COUNT(*) FILTER (WHERE mi_date IS NOT NULL AND sat_no IS NOT NULL AND TRIM(sat_no) != '') as installed,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-%') as total_sat,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-%') as total_invoice,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-1%') as s1,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-2%') as s2,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-3%') as s3,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-4%') as s4,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-5%') as s5,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-6%') as s6,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-7%') as s7,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-8%') as s8,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-9%') as s9
            FROM unified_installation_inventory_data
            GROUP BY 1
        )
        INSERT INTO dashboard_command_center (
            project, inventory, installed, total_sat, total_invoice,
            sat_1_eligibility, sat_2_eligibility, sat_3_eligibility, sat_4_eligibility, 
            sat_5_eligibility, sat_6_eligibility, sat_7_eligibility, sat_8_eligibility, sat_9_eligibility,
            sat_1_achievement, sat_2_achievement, sat_3_achievement, sat_4_achievement, 
            sat_5_achievement, sat_6_achievement, sat_7_achievement, sat_8_achievement, sat_9_achievement,
            sat_1_throughput_pct, sat_2_throughput_pct, sat_3_throughput_pct, sat_4_throughput_pct, 
            sat_5_throughput_pct, sat_6_throughput_pct, sat_7_throughput_pct, sat_8_throughput_pct, sat_9_throughput_pct
        )
        SELECT 
            project_name,
            inventory,
            installed,
            total_sat,
            total_invoice,
            -- Eligibility (Based on doc 6.1: Installed - sum of subsequent stages)
            installed - (s2+s3+s4+s5+s6+s7+s8+s9) as e1,
            installed - (s3+s4+s5+s6+s7+s8+s9) as e2,
            installed - (s4+s5+s6+s7+s8+s9) as e3,
            installed - (s5+s6+s7+s8+s9) as e4,
            installed - (s6+s7+s8+s9) as e5,
            installed - (s7+s8+s9) as e6,
            installed - (s8+s9) as e7,
            installed - s9 as e8,
            installed as e9,
            -- Achievement (Based on doc 6.1: Cumulative sum of stages)
            s1 as a1,
            s1+s2 as a2,
            s1+s2+s3 as a3,
            s1+s2+s3+s4 as a4,
            s1+s2+s3+s4+s5 as a5,
            s1+s2+s3+s4+s5+s6 as a6,
            s1+s2+s3+s4+s5+s6+s7 as a7,
            s1+s2+s3+s4+s5+s6+s7+s8 as a8,
            s1+s2+s3+s4+s5+s6+s7+s8+s9 as a9,
            -- Throughput Pct (Achievement / Eligibility)
            CASE WHEN (installed - (s2+s3+s4+s5+s6+s7+s8+s9)) > 0 THEN (s1)::float / (installed - (s2+s3+s4+s5+s6+s7+s8+s9))::float * 100 ELSE 0 END,
            CASE WHEN (installed - (s3+s4+s5+s6+s7+s8+s9)) > 0 THEN (s1+s2)::float / (installed - (s3+s4+s5+s6+s7+s8+s9))::float * 100 ELSE 0 END,
            CASE WHEN (installed - (s4+s5+s6+s7+s8+s9)) > 0 THEN (s1+s2+s3)::float / (installed - (s4+s5+s6+s7+s8+s9))::float * 100 ELSE 0 END,
            CASE WHEN (installed - (s5+s6+s7+s8+s9)) > 0 THEN (s1+s2+s3+s4)::float / (installed - (s5+s6+s7+s8+s9))::float * 100 ELSE 0 END,
            CASE WHEN (installed - (s6+s7+s8+s9)) > 0 THEN (s1+s2+s3+s4+s5)::float / (installed - (s6+s7+s8+s9))::float * 100 ELSE 0 END,
            CASE WHEN (installed - (s7+s8+s9)) > 0 THEN (s1+s2+s3+s4+s5+s6)::float / (installed - (s7+s8+s9))::float * 100 ELSE 0 END,
            CASE WHEN (installed - (s8+s9)) > 0 THEN (s1+s2+s3+s4+s5+s6+s7)::float / (installed - (s8+s9))::float * 100 ELSE 0 END,
            CASE WHEN (installed - s9) > 0 THEN (s1+s2+s3+s4+s5+s6+s7+s8)::float / (installed - s9)::float * 100 ELSE 0 END,
            CASE WHEN (installed) > 0 THEN (s1+s2+s3+s4+s5+s6+s7+s8+s9)::float / (installed)::float * 100 ELSE 0 END
        FROM combined;
        """
        conn.execute(text(sql))


def execute_command_center_trend(engine):
    """Executes time-series tracking for the Command Center Dashboard matching Excel reporting buckets."""
    log.info("Executing SQL for Command Center Dashboard Trends (Excel-Aligned)")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE dashboard_command_center_trend CASCADE;"))

        # 1. Monthly Trends
        sql_monthly = """
        WITH inventory_act AS (
            SELECT 
                UPPER(TRIM(project)) as project,
                TO_CHAR(DATE_TRUNC('month', didate), 'Mon-YY') as period_value,
                DATE_TRUNC('month', didate) as sort_date,
                COUNT(*) as inventory_added
            FROM unified_installation_inventory_data
            WHERE didate IS NOT NULL
            GROUP BY 1, 2, 3
        ),
        progress_act AS (
            SELECT 
                UPPER(TRIM(project)) as project,
                TO_CHAR(DATE_TRUNC('month', mi_date), 'Mon-YY') as period_value,
                DATE_TRUNC('month', mi_date) as sort_date,
                COUNT(*) FILTER (WHERE sat_no IS NOT NULL AND TRIM(sat_no) != '') as installed_added,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-1%') as s1_added,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-2%') as s2_added,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-3%') as s3_added,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-4%') as s4_added,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-5%') as s5_added,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-6%') as s6_added,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-7%') as s7_added,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-8%') as s8_added,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-9%') as s9_added
            FROM unified_installation_inventory_data
            WHERE mi_date IS NOT NULL
            GROUP BY 1, 2, 3
        ),
        all_periods AS (
            SELECT project, period_value, sort_date FROM inventory_act
            UNION SELECT project, period_value, sort_date FROM progress_act
        )
        INSERT INTO dashboard_command_center_trend (
            project, period_type, period_value, 
            inventory_added, installed_added, 
            s1_added, s2_added, s3_added, s4_added,
            s5_added, s6_added, s7_added, s8_added, s9_added
        )
        SELECT 
            ap.project, 'monthly', ap.period_value,
            COALESCE(i.inventory_added, 0),
            COALESCE(p.installed_added, 0),
            COALESCE(p.s1_added, 0), COALESCE(p.s2_added, 0), COALESCE(p.s3_added, 0),
            COALESCE(p.s4_added, 0), COALESCE(p.s5_added, 0), COALESCE(p.s6_added, 0),
            COALESCE(p.s7_added, 0), COALESCE(p.s8_added, 0), COALESCE(p.s9_added, 0)
        FROM all_periods ap
        LEFT JOIN inventory_act i ON ap.project = i.project AND ap.period_value = i.period_value
        LEFT JOIN progress_act p ON ap.project = p.project AND ap.period_value = p.period_value
        ORDER BY ap.project, ap.sort_date;
        """
        conn.execute(text(sql_monthly))

        # 2. Quarterly Trends
        sql_quarterly = """
        WITH inventory_act AS (
            SELECT 
                UPPER(TRIM(project)) as project,
                TO_CHAR(DATE_TRUNC('quarter', didate), 'YYYY-"Q"Q') as period_value,
                DATE_TRUNC('quarter', didate) as sort_date,
                COUNT(*) as inventory_added
            FROM unified_installation_inventory_data
            WHERE didate IS NOT NULL
            GROUP BY 1, 2, 3
        ),
        progress_act AS (
            SELECT 
                UPPER(TRIM(project)) as project,
                TO_CHAR(DATE_TRUNC('quarter', mi_date), 'YYYY-"Q"Q') as period_value,
                DATE_TRUNC('quarter', mi_date) as sort_date,
                COUNT(*) FILTER (WHERE sat_no IS NOT NULL AND TRIM(sat_no) != '') as installed_added,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-1%') as s1_added,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-2%') as s2_added,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-3%') as s3_added,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-4%') as s4_added,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-5%') as s5_added,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-6%') as s6_added,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-7%') as s7_added,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-8%') as s8_added,
                COUNT(*) FILTER (WHERE LOWER(TRIM(sat_no)) LIKE 'sat-9%') as s9_added
            FROM unified_installation_inventory_data
            WHERE mi_date IS NOT NULL
            GROUP BY 1, 2, 3
        ),
        all_periods AS (
            SELECT project, period_value, sort_date FROM inventory_act
            UNION SELECT project, period_value, sort_date FROM progress_act
        )
        INSERT INTO dashboard_command_center_trend (
            project, period_type, period_value, 
            inventory_added, installed_added, 
            s1_added, s2_added, s3_added, s4_added,
            s5_added, s6_added, s7_added, s8_added, s9_added
        )
        SELECT 
            ap.project, 'quarterly', ap.period_value,
            COALESCE(i.inventory_added, 0),
            COALESCE(p.installed_added, 0),
            COALESCE(p.s1_added, 0), COALESCE(p.s2_added, 0), COALESCE(p.s3_added, 0),
            COALESCE(p.s4_added, 0), COALESCE(p.s5_added, 0), COALESCE(p.s6_added, 0),
            COALESCE(p.s7_added, 0), COALESCE(p.s8_added, 0), COALESCE(p.s9_added, 0)
        FROM all_periods ap
        LEFT JOIN inventory_act i ON ap.project = i.project AND ap.period_value = i.period_value
        LEFT JOIN progress_act p ON ap.project = p.project AND ap.period_value = p.period_value
        ORDER BY ap.project, ap.sort_date;
        """
        conn.execute(text(sql_quarterly))


def execute_command_center_milestones(engine):
    """Calculates lowest chronological date per stage for Command Center milestones."""
    log.info("Executing SQL for Command Center Dashboard Milestones")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE dashboard_command_center_milestone CASCADE;"))

        # Map 'sat-X' lowercased string to a clean 'sX' identifier, and then find minimum dates
        sql = f"""
        WITH parsed AS (
            SELECT 
                UPPER(TRIM(project)) as proj,
                CASE 
                    WHEN LOWER(TRIM(sat_no)) LIKE 'sat-1%' THEN 's1'
                    WHEN LOWER(TRIM(sat_no)) LIKE 'sat-2%' THEN 's2'
                    WHEN LOWER(TRIM(sat_no)) LIKE 'sat-3%' THEN 's3'
                    WHEN LOWER(TRIM(sat_no)) LIKE 'sat-4%' THEN 's4'
                    WHEN LOWER(TRIM(sat_no)) LIKE 'sat-5%' THEN 's5'
                    WHEN LOWER(TRIM(sat_no)) LIKE 'sat-6%' THEN 's6'
                    WHEN LOWER(TRIM(sat_no)) LIKE 'sat-7%' THEN 's7'
                    WHEN LOWER(TRIM(sat_no)) LIKE 'sat-8%' THEN 's8'
                    WHEN LOWER(TRIM(sat_no)) LIKE 'sat-9%' THEN 's9'
                    ELSE NULL
                END as stage,
                sat_date as v_sat,
                lumpsum_invoice_date as v_li,
                pmpm_invoice_date as v_pi,
                lumpsum_collection_date as v_lc,
                pmpm_collection_date as v_pc
            FROM unified_installation_inventory_data
        )
        INSERT INTO dashboard_command_center_milestone (
            project, stage, start_date, 
            lumpsum_inv_date, pmpm_inv_date, 
            lumpsum_col_date, pmpm_col_date
        )
        SELECT 
            proj, stage,
            MIN(v_sat), MIN(v_li), MIN(v_pi), MIN(v_lc), MIN(v_pc)
        FROM parsed
        WHERE stage IS NOT NULL
        GROUP BY proj, stage;
        """
        conn.execute(text(sql))


def execute_kpi_11_mi_sat_invoice(engine):
    """Executes KPI 11 (MI vs SAT vs Invoice) directly in the database."""
    log.info("Executing SQL for KPI 11: MI vs SAT vs Invoice")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_mi_sat_invoice CASCADE;"))
        
        sql = f"""
        INSERT INTO sql_mi_sat_invoice (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            period_type, period_value, total_mi, total_sat, total_invoice
        )
        SELECT 
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, metertype, 
            COALESCE(
                UPPER(TRIM(connection_type)),
                CASE 
                    WHEN metertype = '3PLTCTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'DT'
                    WHEN metertype = 'HTCTPTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'FEEDER'
                    ELSE 'CONSUMER'
                END
            ) as connection_type,
            'monthly', TO_CHAR(DATE_TRUNC('month', mi_date), 'DD-MM-YY'),
            COUNT(*) as total_mi,
            COUNT(*) FILTER (WHERE sat_date IS NOT NULL) as total_sat,
            COUNT(*) FILTER (WHERE lumpsum_invoice_date IS NOT NULL OR pmpm_invoice_date IS NOT NULL) as total_invoice
        FROM unified_installation_inventory_data
        WHERE mi_date IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """
        conn.execute(text(sql))


def execute_kpi_12_revenue_realized(engine):
    """Executes KPI 12 (Revenue Realized) directly in the database."""
    log.info("Executing SQL for KPI 12: Revenue Realized")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_revenue_realized CASCADE;"))
        
        sql = f"""
        INSERT INTO sql_revenue_realized (
            project, discom, zone, circle, division, subdivision,
            substation, feeder, dtr, new_meter_type, meter_category,
            period_type, period_value,
            total_lumpsum_invoice, total_pmpm_invoice,
            total_lumpsum_collection, total_pmpm_collection
        )
        SELECT
            project, discom, zone, circle, division, subdivision,
            substation, feeder, dtr, metertype,
            COALESCE(
                UPPER(TRIM(connection_type)),
                CASE
                    WHEN metertype = '3PLTCTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'DT'
                    WHEN metertype = 'HTCTPTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'FEEDER'
                    ELSE 'CONSUMER'
                END
            ) as connection_type,
            'monthly' as period_type,
            TO_CHAR(
                COALESCE(
                    DATE_TRUNC('month', lumpsum_collection_date),
                    DATE_TRUNC('month', pmpm_collection_date),
                    DATE_TRUNC('month', lumpsum_invoice_date),
                    DATE_TRUNC('month', pmpm_invoice_date)
                ),
                'DD-MM-YY'
            ) as period_value,
            COUNT(*) FILTER (WHERE lumpsum_invoice_date IS NOT NULL) as total_lumpsum_invoice,
            COUNT(*) FILTER (WHERE pmpm_invoice_date IS NOT NULL) as total_pmpm_invoice,
            COUNT(*) FILTER (WHERE lumpsum_collection_date IS NOT NULL) as total_lumpsum_collection,
            COUNT(*) FILTER (WHERE pmpm_collection_date IS NOT NULL) as total_pmpm_collection
        FROM unified_installation_inventory_data
        WHERE lumpsum_invoice_date IS NOT NULL
           OR pmpm_invoice_date IS NOT NULL
           OR lumpsum_collection_date IS NOT NULL
           OR pmpm_collection_date IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """
        conn.execute(text(sql))


def execute_kpi_13_revenue_ageing(engine):
    """Executes KPI 13 (Revenue Ageing) directly in the database."""
    log.info("Executing SQL for KPI 13: Revenue Ageing")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_revenue_ageing CASCADE;"))
        
        sql = f"""
        WITH ageing_base AS (
            SELECT 
                project, discom, zone, circle, division, subdivision, 
                substation, feeder, dtr, metertype, 
                COALESCE(
                    UPPER(TRIM(connection_type)),
                    CASE 
                        WHEN metertype = '3PLTCTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'DT'
                        WHEN metertype = 'HTCTPTSM' AND (consumer_name IS NULL OR TRIM(consumer_name) = '') THEN 'FEEDER'
                        ELSE 'CONSUMER'
                    END
                ) as connection_type,
                sat_date,
                CURRENT_DATE - sat_date::date as days_diff
            FROM unified_installation_inventory_data
            WHERE sat_date IS NOT NULL 
              AND lumpsum_collection_date IS NULL 
              AND pmpm_collection_date IS NULL
        )
        INSERT INTO sql_revenue_ageing (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            period_type, period_value, age_0_30, age_31_60, age_61_90, age_90_plus
        )
        SELECT 
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, metertype, connection_type,
            'monthly', TO_CHAR(DATE_TRUNC('month', sat_date), 'DD-MM-YY'),
            COUNT(*) FILTER (WHERE days_diff <= 30),
            COUNT(*) FILTER (WHERE days_diff > 30 AND days_diff <= 60),
            COUNT(*) FILTER (WHERE days_diff > 60 AND days_diff <= 90),
            COUNT(*) FILTER (WHERE days_diff > 90)
        FROM ageing_base
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """
        conn.execute(text(sql))


def execute_kpi_14_defective_meters(engine):
    """
    KPI 14: Defective Meters.
    Categorizes complaints from complaints_master into Meter Burnt, Meter Faulty, and Others.
    """
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_defective_meters CASCADE;"))
        
        sql = """
        INSERT INTO sql_defective_meters (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, meter_category, new_meter_type, 
            defective_type, period_value, meter_count
        )
        WITH cleaned_complaints AS (
            SELECT 
                project, discom, zone, circle, division, subdivision, 
                feeder, dtr, meter_category, old_smart_meter_number,
                TRIM(REPLACE(REPLACE(complaint_type, '"', ''), CHR(160), ' ')) as clean_type,
                created_date
            FROM complaints_master
        ),
        categorized AS (
            SELECT 
                *,
                CASE 
                    WHEN clean_type IN ('Meter burnt', 'Meter Sparking or Sparking at Meter terminal', 'Meter Terminal Burnt') THEN 'Meter Burnt'
                    WHEN clean_type = 'Meter faulty or not working' THEN 'Meter Faulty'
                    ELSE 'Others'
                END as defective_type
            FROM cleaned_complaints
        ),
        joined AS (
            SELECT 
                c.*, 
                COALESCE(inv.substation, 'Unknown') as substation_inv,
                COALESCE(inv.metertype, 'Unknown') as metertype_inv,
                COALESCE(
                    UPPER(TRIM(c.meter_category)),
                    CASE 
                        WHEN inv.metertype = '3PLTCTSM' AND (inv.consumer_name IS NULL OR TRIM(inv.consumer_name) = '') THEN 'DT'
                        WHEN inv.metertype = 'HTCTPTSM' AND (inv.consumer_name IS NULL OR TRIM(inv.consumer_name) = '') THEN 'FEEDER'
                        ELSE 'CONSUMER'
                    END
                ) as refined_category
            FROM categorized c
            LEFT JOIN unified_installation_inventory_data inv ON c.old_smart_meter_number = inv.meterserialnumber
        )
        SELECT 
            project, discom, zone, circle, division, subdivision, 
            substation_inv, feeder, dtr, refined_category, metertype_inv,
            defective_type,
            TO_CHAR(DATE_TRUNC('month', created_date), 'DD-MM-YY'),
            COUNT(*)
        FROM joined
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """
        conn.execute(text(sql))
