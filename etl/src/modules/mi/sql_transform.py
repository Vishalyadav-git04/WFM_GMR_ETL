"""
Native PostgreSQL transformations for MI KPIs.
These functions execute SQL directly in the database to prevent memory issues.
"""

from sqlalchemy import text
import logging

log = logging.getLogger("extract.sql_transform")


def _get_date_parsing_sql(col_name):
    """Standardized date parsing CASE logic for various input formats."""
    return f"""
    CASE 
      WHEN "{col_name}" ~ '^\\d{{4}}-\\d{{1,2}}-\\d{{1,2}}' THEN TO_DATE(split_part("{col_name}", ' ', 1), 'YYYY-MM-DD')
      WHEN "{col_name}" ~ '^\\d{{1,2}}/\\d{{1,2}}/\\d{{4}}' THEN TO_DATE(split_part("{col_name}", ' ', 1), 'DD/MM/YYYY')
      WHEN "{col_name}" ~ '^\\d{{1,2}}-\\d{{1,2}}-\\d{{4}}' THEN TO_DATE(split_part("{col_name}", ' ', 1), 'DD-MM-YYYY')
      WHEN "{col_name}" ~ '^\\d{{1,2}}-\\d{{1,2}}-\\d{{2}}' THEN TO_DATE(split_part("{col_name}", ' ', 1), 'DD-MM-YY')
      ELSE NULL 
    END
    """


def execute_kpi_1_mi_progress(engine):
    """Executes KPI 1 (MI Progress) directly in the database."""
    log.info("Executing SQL for KPI 1: MI Progress")
    
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_mi_progress CASCADE;"))
        
        parsed_date = _get_date_parsing_sql("installationDate")
        
        base_query = f"""
        WITH parsed_data AS (
            SELECT
                "Project", "Discom", "Zone", "Circle", "Division", "SubDivision", 
                "SubStation", "Feeder", "DTR", "newMeterType", "MeterCategory",
                {parsed_date} AS valid_date
            FROM new_installation_data
            WHERE "installationDate" IS NOT NULL
        )
        """
        
        # 1. Daily
        conn.execute(text(f"""
        {base_query}
        INSERT INTO sql_mi_progress (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            period_type, period_value, total_mi_progress
        )
        SELECT 
            "Project", "Discom", "Zone", "Circle", "Division", "SubDivision", 
            "SubStation", "Feeder", "DTR", "newMeterType", "MeterCategory",
            'daily', TO_CHAR(valid_date, 'DD-MM-YY'), COUNT(*)
        FROM parsed_data WHERE valid_date IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """))
        
        # 2. Weekly (Monday)
        conn.execute(text(f"""
        {base_query}
        INSERT INTO sql_mi_progress (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            period_type, period_value, total_mi_progress
        )
        SELECT 
            "Project", "Discom", "Zone", "Circle", "Division", "SubDivision", 
            "SubStation", "Feeder", "DTR", "newMeterType", "MeterCategory",
            'weekly', TO_CHAR(DATE_TRUNC('week', valid_date), 'DD-MM-YY'), COUNT(*)
        FROM parsed_data WHERE valid_date IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """))
        
        # 3. Monthly (1st)
        conn.execute(text(f"""
        {base_query}
        INSERT INTO sql_mi_progress (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            period_type, period_value, total_mi_progress
        )
        SELECT 
            "Project", "Discom", "Zone", "Circle", "Division", "SubDivision", 
            "SubStation", "Feeder", "DTR", "newMeterType", "MeterCategory",
            'monthly', TO_CHAR(DATE_TRUNC('month', valid_date), 'DD-MM-YY'), COUNT(*)
        FROM parsed_data WHERE valid_date IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """))


def execute_kpi_2_mi_productivity(engine):
    """Executes KPI 2 (MI Productivity) directly in the database."""
    log.info("Executing SQL for KPI 2: MI Productivity")
    
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_mi_productivity CASCADE;"))
        
        parsed_date = _get_date_parsing_sql("installationDate")
        
        base_query = f"""
        WITH parsed_data AS (
            SELECT
                "Project", "Discom", "Zone", "Circle", "Division", "SubDivision", 
                "SubStation", "Feeder", "DTR", "newMeterType", "MeterCategory", "Technician",
                {parsed_date} AS valid_date
            FROM new_installation_data
            WHERE "installationDate" IS NOT NULL
        )
        """
        
        # 1. Daily
        conn.execute(text(f"""
        {base_query}
        INSERT INTO sql_mi_productivity (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            technician, period_type, period_value, daily_installations
        )
        SELECT 
            "Project", "Discom", "Zone", "Circle", "Division", "SubDivision", 
            "SubStation", "Feeder", "DTR", "newMeterType", "MeterCategory", "Technician",
            'daily', TO_CHAR(valid_date, 'DD-MM-YY'), COUNT(*)
        FROM parsed_data WHERE valid_date IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14;
        """))
        
        # 2. Weekly
        conn.execute(text(f"""
        {base_query}
        INSERT INTO sql_mi_productivity (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            technician, period_type, period_value, daily_installations
        )
        SELECT 
            "Project", "Discom", "Zone", "Circle", "Division", "SubDivision", 
            "SubStation", "Feeder", "DTR", "newMeterType", "MeterCategory", "Technician",
            'weekly', TO_CHAR(DATE_TRUNC('week', valid_date), 'DD-MM-YY'), COUNT(*)
        FROM parsed_data WHERE valid_date IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14;
        """))
        
        # 3. Monthly
        conn.execute(text(f"""
        {base_query}
        INSERT INTO sql_mi_productivity (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            technician, period_type, period_value, daily_installations
        )
        SELECT 
            "Project", "Discom", "Zone", "Circle", "Division", "SubDivision", 
            "SubStation", "Feeder", "DTR", "newMeterType", "MeterCategory", "Technician",
            'monthly', TO_CHAR(DATE_TRUNC('month', valid_date), 'DD-MM-YY'), COUNT(*)
        FROM parsed_data WHERE valid_date IS NOT NULL
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14;
        """))


def execute_kpi_3_monthly_productivity(engine):
    """Executes KPI 3 directly in the database."""
    log.info("Executing SQL for KPI 3: Monthly Productivity")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_monthly_productivity CASCADE;"))
        
        parsed_date = _get_date_parsing_sql("installationDate")
        
        sql = f"""
        WITH location_counts AS (
            SELECT 
                "Project", "Discom", "Zone", "Circle", "Division", "SubDivision", 
                "SubStation", "Feeder", "DTR", "newMeterType", "MeterCategory",
                TO_CHAR(DATE_TRUNC('month', {parsed_date}), 'DD-MM-YY') as period_val,
                COUNT(*) as loc_count
            FROM new_installation_data
            WHERE "installationDate" IS NOT NULL
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
            "Project", "Discom", "Zone", "Circle", "Division", "SubDivision", 
            "SubStation", "Feeder", "DTR", "newMeterType", "MeterCategory",
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
        
        parsed_inst_date = _get_date_parsing_sql("installationDate")
        
        base_join_query = f"""
        WITH joined_data AS (
            SELECT 
                inv.project AS p, 
                inst."Discom" AS d, inst."Zone" AS z, inst."Circle" AS c, inst."Division" AS div, inst."SubDivision" AS sub, 
                inst."SubStation" AS ss, inst."Feeder" AS f, inst."DTR" AS dtr, inst."newMeterType" AS mt, inst."MeterCategory" AS mc,
                {parsed_inst_date} as idt
            FROM new_inventory_data inv
            LEFT JOIN new_installation_data inst ON inv."MeterSerialNumber" = inst."newMeterNumber"
        )
        """
        
        # Weekly
        conn.execute(text(f"""
        {base_join_query}
        INSERT INTO sql_inventory_utilization (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            period_type, period_value, total_inventory, total_installed, utilization_rate_pct, remaining_stock
        )
        SELECT 
            p, d, z, c, div, sub, ss, f, dtr, mt, mc,
            'weekly', TO_CHAR(DATE_TRUNC('week', idt), 'DD-MM-YY'),
            COUNT(*),
            COUNT(idt),
            CASE WHEN COUNT(*) > 0 THEN COUNT(idt)::float / COUNT(*)::float * 100 ELSE 0 END,
            COUNT(*) - COUNT(idt)
        FROM joined_data
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """))
        
        # Monthly
        conn.execute(text(f"""
        {base_join_query}
        INSERT INTO sql_inventory_utilization (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            period_type, period_value, total_inventory, total_installed, utilization_rate_pct, remaining_stock
        )
        SELECT 
            p, d, z, c, div, sub, ss, f, dtr, mt, mc,
            'monthly', TO_CHAR(DATE_TRUNC('month', idt), 'DD-MM-YY'),
            COUNT(*),
            COUNT(idt),
            CASE WHEN COUNT(*) > 0 THEN COUNT(idt)::float / COUNT(*)::float * 100 ELSE 0 END,
            COUNT(*) - COUNT(idt)
        FROM joined_data
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """))

        # KPI 5 (Daily)
        conn.execute(text(f"""
        {base_join_query}
        INSERT INTO sql_inventory_utilization (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            period_type, period_value, total_inventory, total_installed, utilization_rate_pct, remaining_stock
        )
        SELECT 
            p, d, z, c, div, sub, ss, f, dtr, mt, mc,
            'daily', TO_CHAR(idt, 'DD-MM-YY'),
            COUNT(*),
            COUNT(idt),
            CASE WHEN COUNT(*) > 0 THEN COUNT(idt)::float / COUNT(*)::float * 100 ELSE 0 END,
            COUNT(*) - COUNT(idt)
        FROM joined_data
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13;
        """))


def execute_kpi_6_stock_ageing(engine):
    """Executes KPI 6 directly in the database."""
    log.info("Executing SQL for KPI 6: Stock Ageing")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_stock_ageing CASCADE;"))
        
        parsed_di_date = _get_date_parsing_sql("DIDate")
        parsed_inst_ts = _get_date_parsing_sql("InstalledTS")
        
        sql = f"""
        INSERT INTO sql_stock_ageing (
            meter_serial_number, di_date, installed_ts, ageing_days
        )
        SELECT 
            "MeterSerialNumber",
            {parsed_di_date} as parsed_di,
            {parsed_inst_ts} as parsed_inst,
            CURRENT_DATE - {parsed_di_date}
        FROM new_inventory_data
        WHERE {parsed_inst_ts} IS NULL;
        """
        conn.execute(text(sql))


def execute_kpi_7_mi_vs_sat(engine):
    """Executes KPI 7 directly in the DB."""
    log.info("Executing SQL for KPI 7: MI vs SAT")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_mi_vs_sat CASCADE;"))
        
        parsed_inst_date = _get_date_parsing_sql("installationDate")
        
        sql = f"""
        WITH base AS (
            SELECT 
                "Project", "Discom", "Zone", "Circle", "Division", "SubDivision", 
                "SubStation", "Feeder", "DTR", "newMeterType", "MeterCategory", "newMeterNumber",
                LOWER(TRIM("SAT_SAT_No")) as sat_stage,
                {parsed_inst_date} as install_date
            FROM new_installation_data
        ),
        pivoted AS (
            SELECT 
                "Project", "Discom", "Zone", "Circle", "Division", "SubDivision", 
                "SubStation", "Feeder", "DTR", "newMeterType", "MeterCategory",
                TO_CHAR(install_date, 'YYYY-MM-DD') as period_val,
                COUNT("newMeterNumber") as total_mi,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-%') as total_sat,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-1%') as sat_1,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-2%') as sat_2,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-3%') as sat_3,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-4%') as sat_4,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-5%') as sat_5,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-6%') as sat_6,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-7%') as sat_7
            FROM base
            WHERE install_date IS NOT NULL
            GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12
        )
        INSERT INTO sql_mi_vs_sat (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            period_type, period_value, total_mi, total_sat, 
            sat_1, sat_2, sat_3, sat_4, sat_5, sat_6, sat_7, sat_progress_pct
        )
        SELECT 
            *,
            'daily', period_val, 
            total_mi, total_sat, sat_1, sat_2, sat_3, sat_4, sat_5, sat_6, sat_7,
            CASE WHEN total_mi > 0 THEN (total_sat::float / total_mi::float * 100) ELSE 0 END
        FROM pivoted;
        """
        # Note: The * above in SELECT * FROM pivoted includes the grouping cols, 
        # so I need to be explicit to match the INSERT columns.
        
        # Explicit version:
        sql_explicit = f"""
        WITH base AS (
            SELECT 
                "Project", "Discom", "Zone", "Circle", "Division", "SubDivision", 
                "SubStation", "Feeder", "DTR", "newMeterType", "MeterCategory", "newMeterNumber",
                LOWER(TRIM("SAT_SAT_No")) as sat_stage,
                {parsed_inst_date} as install_date
            FROM new_installation_data
        ),
        pivoted AS (
            SELECT 
                "Project", "Discom", "Zone", "Circle", "Division", "SubDivision", 
                "SubStation", "Feeder", "DTR", "newMeterType", "MeterCategory",
                TO_CHAR(install_date, 'DD-MM-YY') as period_val,
                COUNT("newMeterNumber") as total_mi,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-%') as total_sat,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-1%') as sat_1,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-2%') as sat_2,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-3%') as sat_3,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-4%') as sat_4,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-5%') as sat_5,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-6%') as sat_6,
                COUNT(*) FILTER (WHERE sat_stage LIKE 'sat-7%') as sat_7
            FROM base
            WHERE install_date IS NOT NULL
            GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12
        )
        INSERT INTO sql_mi_vs_sat (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category, 
            period_type, period_value, total_mi, total_sat, 
            sat_1, sat_2, sat_3, sat_4, sat_5, sat_6, sat_7, sat_progress_pct
        )
        SELECT 
            "Project", "Discom", "Zone", "Circle", "Division", "SubDivision", 
            "SubStation", "Feeder", "DTR", "newMeterType", "MeterCategory",
            'daily', period_val, 
            total_mi, total_sat, sat_1, sat_2, sat_3, sat_4, sat_5, sat_6, sat_7,
            CASE WHEN total_mi > 0 THEN (total_sat::float / total_mi::float * 100) ELSE 0 END
        FROM pivoted;
        """
        conn.execute(text(sql_explicit))


def execute_kpi_8_non_sat_ageing(engine):
    """Executes KPI 8 (Non-SAT Ageing) directly in the database."""
    log.info("Executing SQL for MI KPI 8: Non-SAT Ageing")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_non_sat_ageing CASCADE;"))
        
        parsed_inst_date = _get_date_parsing_sql("installationDate")
        
        sql = f"""
        INSERT INTO sql_non_sat_ageing (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category,
            meter_serial_number, installation_date, ageing_days
        )
        SELECT 
            "Project", "Discom", "Zone", "Circle", "Division", "SubDivision", 
            "SubStation", "Feeder", "DTR", "newMeterType", "MeterCategory",
            "newMeterNumber",
            {parsed_inst_date},
            CURRENT_DATE - {parsed_inst_date}
        FROM new_installation_data
        WHERE {parsed_inst_date} IS NOT NULL
          AND (LOWER(TRIM("SAT_SAT_No")) NOT LIKE 'sat-%' OR "SAT_SAT_No" IS NULL);
        """
        conn.execute(text(sql))
def execute_kpi_9_meter_journey(engine):
    """Executes KPI 9 (Meter Journey Avg Time) directly in the database."""
    log.info("Executing SQL for MI KPI 9: Meter Journey Avg Time")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_meter_journey_avg_time CASCADE;"))
        
        # Parse relevant inventory dates
        d_di = _get_date_parsing_sql("DIDate")
        d_gmr_to_ag = _get_date_parsing_sql("GMRToAgencyTS")
        d_ag_to_sup = _get_date_parsing_sql("AgencyToSupTS")
        d_sup_to_tech = _get_date_parsing_sql("SupToTechTS")
        d_installed = _get_date_parsing_sql("InstalledTS")
        
        # Parse installation dates
        d_sat = _get_date_parsing_sql("SAT_Date")
        d_pmpm = _get_date_parsing_sql("pmpm_Collection_date")
        
        sql = f"""
        INSERT INTO sql_meter_journey_avg_time (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category,
            di_to_gmr, gmr_to_agency, agency_to_sup, sup_to_install, 
            install_to_sat, sat_to_revenue, total_journey
        )
        SELECT 
            inst."Project", inst."Discom", inst."Zone", inst."Circle", inst."Division", inst."SubDivision", 
            inst."SubStation", inst."Feeder", inst."DTR", inst."newMeterType", inst."MeterCategory",
            AVG({d_gmr_to_ag} - {d_di}),
            AVG({d_ag_to_sup} - {d_gmr_to_ag}),
            AVG({d_sup_to_tech} - {d_ag_to_sup}),
            AVG({d_installed} - {d_sup_to_tech}),
            AVG({d_sat} - {d_installed}),
            AVG({d_pmpm} - {d_sat}),
            AVG({d_pmpm} - {d_di})
        FROM new_inventory_data inv
        INNER JOIN new_installation_data inst ON inv."MeterSerialNumber" = inst."newMeterNumber"
        WHERE {d_pmpm} IS NOT NULL
          AND {d_sat} <= (SELECT MAX({d_sat}) FROM new_installation_data)
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11;
        """
        conn.execute(text(sql))


def execute_kpi_10_meter_stage(engine):
    """Executes KPI 10 (Meter Current Stage) directly in the database."""
    log.info("Executing SQL for MI KPI 10: Meter Current Stage")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE sql_meter_current_stage CASCADE;"))
        
        # Parse relevant dates
        d_di = _get_date_parsing_sql("DIDate")
        d_gmr_to_ag = _get_date_parsing_sql("GMRToAgencyTS")
        d_ag_to_sup = _get_date_parsing_sql("AgencyToSupTS")
        d_sup_to_tech = _get_date_parsing_sql("SupToTechTS")
        d_installed = _get_date_parsing_sql("InstalledTS")
        d_sat = _get_date_parsing_sql("SAT_Date")
        d_pmpm = _get_date_parsing_sql("pmpm_Collection_date")
        
        sql = f"""
        INSERT INTO sql_meter_current_stage (
            project, discom, zone, circle, division, subdivision, 
            substation, feeder, dtr, new_meter_type, meter_category,
            current_stage, meter_count
        )
        SELECT 
            inst."Project", inst."Discom", inst."Zone", inst."Circle", inst."Division", inst."SubDivision", 
            inst."SubStation", inst."Feeder", inst."DTR", inst."newMeterType", inst."MeterCategory",
            CASE
                WHEN {d_di} IS NOT NULL AND {d_gmr_to_ag} IS NULL THEN 'At GMR Warehouse'
                WHEN {d_gmr_to_ag} IS NOT NULL AND {d_ag_to_sup} IS NULL THEN 'With Agency'
                WHEN {d_ag_to_sup} IS NOT NULL AND {d_sup_to_tech} IS NULL THEN 'With Supervisor'
                WHEN {d_sup_to_tech} IS NOT NULL AND {d_installed} IS NULL THEN 'With Technician'
                WHEN {d_installed} IS NOT NULL AND {d_sat} IS NULL THEN 'Installed Pending SAT'
                WHEN {d_sat} IS NOT NULL AND {d_pmpm} IS NULL THEN 'SAT Done - Revenue Pending'
                ELSE 'Unknown'
            END as current_stage_val,
            COUNT(*)
        FROM new_inventory_data inv
        INNER JOIN new_installation_data inst ON inv."MeterSerialNumber" = inst."newMeterNumber"
        WHERE {d_pmpm} IS NULL
          AND {d_sat} <= (SELECT MAX({d_sat}) FROM new_installation_data)
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12;
        """
        conn.execute(text(sql))


def execute_command_center_kpi(engine):
    """Executes the specialized dashboard logic for Command Center."""
    log.info("Executing SQL for Command Center Dashboard Snapshot")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE dashboard_command_center CASCADE;"))

        # Date extractors based on user bounds:
        # Inventory till 28-02-26
        # Installed till 28-02-26
        # Total SAT till 31-01-26
        # Total Invoice 05-02-26 (Assume Lumpsum_Invoice_Date or pmpm_Invoice_date. We will use Lumpsum_Invoice_Date as proxy for Invoice)
        d_di = _get_date_parsing_sql("DIDate")
        d_inst = _get_date_parsing_sql("installationDate")
        d_sat = _get_date_parsing_sql("SAT_Date")
        d_inv = _get_date_parsing_sql("Lumpsum_Invoice_Date")

        sql = f"""
        WITH cte_inv AS (
            SELECT 
                UPPER(TRIM(project)) as project_name,
                COUNT("MeterSerialNumber") as inv_count
            FROM new_inventory_data
            WHERE {d_di} <= '2026-02-28'
            GROUP BY 1
        ),
        cte_inst AS (
            SELECT 
                UPPER(TRIM("Project")) as project_name,
                COUNT("newMeterNumber") as inst_count
            FROM new_installation_data
            WHERE {d_inst} <= '2026-02-28'
            GROUP BY 1
        ),
        cte_sat AS (
            SELECT
                UPPER(TRIM("Project")) as project_name,
                COUNT(*) FILTER (WHERE LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-%' AND {d_sat} <= '2026-01-31') as sat_total,
                COUNT(*) FILTER (WHERE LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-%' AND {d_inv} <= '2026-02-05') as inv_total,
                COUNT(*) FILTER (WHERE LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-1%' AND {d_sat} <= '2026-01-31') as s1,
                COUNT(*) FILTER (WHERE LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-2%' AND {d_sat} <= '2026-01-31') as s2,
                COUNT(*) FILTER (WHERE LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-3%' AND {d_sat} <= '2026-01-31') as s3,
                COUNT(*) FILTER (WHERE LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-4%' AND {d_sat} <= '2026-01-31') as s4,
                COUNT(*) FILTER (WHERE LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-5%' AND {d_sat} <= '2026-01-31') as s5,
                COUNT(*) FILTER (WHERE LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-6%' AND {d_sat} <= '2026-01-31') as s6,
                COUNT(*) FILTER (WHERE LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-7%' AND {d_sat} <= '2026-01-31') as s7
            FROM new_installation_data
            GROUP BY 1
        ),
        combined AS (
            SELECT
                COALESCE(i.project_name, s.project_name, v.project_name) as project,
                COALESCE(v.inv_count, 0) as inventory,
                COALESCE(i.inst_count, 0) as installed,
                COALESCE(s.sat_total, 0) as total_sat,
                COALESCE(s.inv_total, 0) as total_invoice,
                COALESCE(s.s1, 0) as s1,
                COALESCE(s.s2, 0) as s2,
                COALESCE(s.s3, 0) as s3,
                COALESCE(s.s4, 0) as s4,
                COALESCE(s.s5, 0) as s5,
                COALESCE(s.s6, 0) as s6,
                COALESCE(s.s7, 0) as s7
            FROM cte_inst i
            FULL OUTER JOIN cte_sat s ON i.project_name = s.project_name
            FULL OUTER JOIN cte_inv v ON i.project_name = v.project_name
            WHERE COALESCE(i.project_name, s.project_name, v.project_name) IS NOT NULL
        )
        INSERT INTO dashboard_command_center (
            project, inventory, installed, total_sat, total_invoice,
            sat_1_eligibility, sat_2_eligibility, sat_3_eligibility, sat_4_eligibility, 
            sat_5_eligibility, sat_6_eligibility, sat_7_eligibility, sat_8_eligibility,
            sat_1_achievement, sat_2_achievement, sat_3_achievement, sat_4_achievement, 
            sat_5_achievement, sat_6_achievement, sat_7_achievement, sat_8_achievement,
            sat_1_throughput_pct, sat_2_throughput_pct, sat_3_throughput_pct, sat_4_throughput_pct, 
            sat_5_throughput_pct, sat_6_throughput_pct, sat_7_throughput_pct, sat_8_throughput_pct
        )
        SELECT 
            project,
            inventory,
            installed,
            total_sat,
            total_invoice,
            -- Eligibility
            installed - (s2+s3+s4+s5+s6+s7) as e1,
            installed - (s3+s4+s5+s6+s7) as e2,
            installed - (s4+s5+s6+s7) as e3,
            installed - (s5+s6+s7) as e4,
            installed - (s6+s7) as e5,
            installed - (s7) as e6,
            installed as e7,
            0 as e8,
            -- Achievement
            s1 as a1,
            s1+s2 as a2,
            s1+s2+s3 as a3,
            s1+s2+s3+s4 as a4,
            s1+s2+s3+s4+s5 as a5,
            s1+s2+s3+s4+s5+s6 as a6,
            s1+s2+s3+s4+s5+s6+s7 as a7,
            0 as a8,
            -- Throughput Pct
            CASE WHEN (installed - (s2+s3+s4+s5+s6+s7)) > 0 THEN s1::float / (installed - (s2+s3+s4+s5+s6+s7))::float * 100 ELSE 0 END,
            CASE WHEN (installed - (s3+s4+s5+s6+s7)) > 0 THEN (s1+s2)::float / (installed - (s3+s4+s5+s6+s7))::float * 100 ELSE 0 END,
            CASE WHEN (installed - (s4+s5+s6+s7)) > 0 THEN (s1+s2+s3)::float / (installed - (s4+s5+s6+s7))::float * 100 ELSE 0 END,
            CASE WHEN (installed - (s5+s6+s7)) > 0 THEN (s1+s2+s3+s4)::float / (installed - (s5+s6+s7))::float * 100 ELSE 0 END,
            CASE WHEN (installed - (s6+s7)) > 0 THEN (s1+s2+s3+s4+s5)::float / (installed - (s6+s7))::float * 100 ELSE 0 END,
            CASE WHEN (installed - (s7)) > 0 THEN (s1+s2+s3+s4+s5+s6)::float / (installed - (s7))::float * 100 ELSE 0 END,
            CASE WHEN installed > 0 THEN (s1+s2+s3+s4+s5+s6+s7)::float / installed::float * 100 ELSE 0 END,
            0 as tp8
        FROM combined;
        """
        conn.execute(text(sql))


def execute_command_center_trend(engine):
    """Executes time-series tracking for the Command Center Dashboard."""
    log.info("Executing SQL for Command Center Dashboard Trends")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE dashboard_command_center_trend CASCADE;"))

        d_di = _get_date_parsing_sql("DIDate")
        d_inst = _get_date_parsing_sql("installationDate")
        d_sat = _get_date_parsing_sql("SAT_Date")

        # Create unifying views for metrics grouped by month & quarter
        base_query = f"""
        WITH inv_data AS (
            SELECT 
                UPPER(TRIM(project)) as proj, 
                TO_CHAR(DATE_TRUNC('month', {d_di}), 'Mon-YY') as y_month,
                TO_CHAR(DATE_TRUNC('quarter', {d_di}), 'YYYY-"Q"Q') as y_quarter,
                COUNT(*) as c_inv
            FROM new_inventory_data 
            WHERE {d_di} IS NOT NULL AND {d_di} <= '2026-02-28'
            GROUP BY 1,2,3
        ),
        inst_sat_data AS (
            SELECT 
                UPPER(TRIM("Project")) as proj, 
                TO_CHAR(DATE_TRUNC('month', {d_inst}), 'Mon-YY') as y_month,
                TO_CHAR(DATE_TRUNC('quarter', {d_inst}), 'YYYY-"Q"Q') as y_quarter,
                COUNT(*) as c_inst,
                COUNT(*) FILTER (WHERE LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-1%' AND {d_sat} <= '2026-01-31') as s1_c,
                COUNT(*) FILTER (WHERE LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-2%' AND {d_sat} <= '2026-01-31') as s2_c,
                COUNT(*) FILTER (WHERE LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-3%' AND {d_sat} <= '2026-01-31') as s3_c,
                COUNT(*) FILTER (WHERE LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-4%' AND {d_sat} <= '2026-01-31') as s4_c,
                COUNT(*) FILTER (WHERE LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-5%' AND {d_sat} <= '2026-01-31') as s5_c,
                COUNT(*) FILTER (WHERE LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-6%' AND {d_sat} <= '2026-01-31') as s6_c,
                COUNT(*) FILTER (WHERE LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-7%' AND {d_sat} <= '2026-01-31') as s7_c,
                COUNT(*) FILTER (WHERE LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-8%' AND {d_sat} <= '2026-01-31') as s8_c
            FROM new_installation_data 
            WHERE {d_inst} IS NOT NULL AND {d_inst} <= '2026-02-28'
            GROUP BY 1,2,3
        )
        """

        # Monthly Trends (Cumulative vs Periodic)
        conn.execute(text(f"""
        {base_query},
        periods AS (
            SELECT proj, y_month FROM inv_data
            UNION SELECT proj, y_month FROM inst_sat_data
        ),
        monthly_joined AS (
            SELECT p.proj, p.y_month,
                   COALESCE(v.c_inv, 0) as inventory_added,
                   COALESCE(i.c_inst, 0) as installed_added,
                   COALESCE(i.s1_c, 0) as s1_added, COALESCE(i.s2_c, 0) as s2_added,
                   COALESCE(i.s3_c, 0) as s3_added, COALESCE(i.s4_c, 0) as s4_added,
                   COALESCE(i.s5_c, 0) as s5_added, COALESCE(i.s6_c, 0) as s6_added,
                   COALESCE(i.s7_c, 0) as s7_added, COALESCE(i.s8_c, 0) as s8_added
            FROM periods p
            LEFT JOIN inv_data v ON p.proj = v.proj AND p.y_month = v.y_month
            LEFT JOIN inst_sat_data i ON p.proj = i.proj AND p.y_month = i.y_month
            WHERE p.y_month IS NOT NULL
        )
        INSERT INTO dashboard_command_center_trend (
            project, period_type, period_value, 
            inventory_added, installed_added, 
            s1_added, s2_added, s3_added, s4_added,
            s5_added, s6_added, s7_added, s8_added
        )
        SELECT 
            proj, 'monthly', y_month, 
            inventory_added, installed_added,
            s1_added, s2_added, s3_added, s4_added,
            s5_added, s6_added, s7_added, s8_added
        FROM monthly_joined;
        """))

        # Quarterly Trends (Cumulative vs Periodic)
        conn.execute(text(f"""
        {base_query},
        q_periods AS (
            SELECT proj, y_quarter FROM inv_data
            UNION SELECT proj, y_quarter FROM inst_sat_data
        ),
        quarterly_joined AS (
            SELECT p.proj, p.y_quarter,
                   COALESCE(SUM(v.c_inv), 0) as inventory_added,
                   COALESCE(SUM(i.c_inst), 0) as installed_added,
                   COALESCE(SUM(i.s1_c), 0) as s1_added, COALESCE(SUM(i.s2_c), 0) as s2_added,
                   COALESCE(SUM(i.s3_c), 0) as s3_added, COALESCE(SUM(i.s4_c), 0) as s4_added,
                   COALESCE(SUM(i.s5_c), 0) as s5_added, COALESCE(SUM(i.s6_c), 0) as s6_added,
                   COALESCE(SUM(i.s7_c), 0) as s7_added, COALESCE(SUM(i.s8_c), 0) as s8_added
            FROM q_periods p
            LEFT JOIN inv_data v ON p.proj = v.proj AND p.y_quarter = v.y_quarter
            LEFT JOIN inst_sat_data i ON p.proj = i.proj AND p.y_quarter = i.y_quarter
            WHERE p.y_quarter IS NOT NULL
            GROUP BY p.proj, p.y_quarter
        )
        INSERT INTO dashboard_command_center_trend (
            project, period_type, period_value, 
            inventory_added, installed_added, 
            s1_added, s2_added, s3_added, s4_added,
            s5_added, s6_added, s7_added, s8_added
        )
        SELECT 
            proj, 'quarterly', y_quarter, 
            inventory_added, installed_added,
            s1_added, s2_added, s3_added, s4_added,
            s5_added, s6_added, s7_added, s8_added
        FROM quarterly_joined;
        """))


def execute_command_center_milestones(engine):
    """Calculates lowest chronological date per stage for Command Center milestones."""
    log.info("Executing SQL for Command Center Dashboard Milestones")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE dashboard_command_center_milestone CASCADE;"))

        d_sat = _get_date_parsing_sql("SAT_Date")
        d_li = _get_date_parsing_sql("Lumpsum_Invoice_Date")
        d_lc = _get_date_parsing_sql("Lumpsum_Collection_Date")
        d_pi = _get_date_parsing_sql("pmpm_Invoice_date")
        d_pc = _get_date_parsing_sql("pmpm_Collection_date")

        # Map 'sat-X' lowercased string to a clean 'sX' identifier, and then find minimum dates
        sql = f"""
        WITH parsed AS (
            SELECT 
                UPPER(TRIM("Project")) as proj,
                CASE 
                    WHEN LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-1%' THEN 's1'
                    WHEN LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-2%' THEN 's2'
                    WHEN LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-3%' THEN 's3'
                    WHEN LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-4%' THEN 's4'
                    WHEN LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-5%' THEN 's5'
                    WHEN LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-6%' THEN 's6'
                    WHEN LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-7%' THEN 's7'
                    WHEN LOWER(TRIM("SAT_SAT_No")) LIKE 'sat-8%' THEN 's8'
                    ELSE NULL
                END as stage,
                {d_sat} as v_sat,
                {d_li} as v_li,
                {d_pi} as v_pi,
                {d_lc} as v_lc,
                {d_pc} as v_pc
            FROM new_installation_data
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
