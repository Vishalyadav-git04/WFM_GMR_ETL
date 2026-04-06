"""
ETL Pipeline Orchestrator
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Ensure etl/src/ is on the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from infrastructure.logging.logger import get_logger
from infrastructure.database.setup import get_engine
from infrastructure.utils.writer import write_kpi

log = get_logger("pipeline")


# ─────────────────────────────────────────────────────────────────────────
# MI Pipeline
# ─────────────────────────────────────────────────────────────────────────

def run_mi_pipeline():
    """Extract → Transform → Load for all 7 MI KPIs."""
    from extract.installation import extract_installation
    from extract.inventory import extract_inventory
    from modules.mi.transform import (
        kpi_1_mi_progress,
        kpi_2_mi_productivity,
        kpi_3_monthly_productivity,
        kpi_4_inventory_utilization,
        kpi_5_mi_pace_vs_stock,
        kpi_6_stock_ageing,
        kpi_7_mi_vs_sat,
    )

    log.info("═══ MI Pipeline started ═══")

    # ── EXTRACT ──
    df_install = extract_installation()
    df_inventory = extract_inventory()

    # ── TRANSFORM & LOAD ──

    # KPI 1
    log.info("KPI 1: MI Progress")
    results = kpi_1_mi_progress(df_install)
    frames = []
    import polars as pl
    for period, lf in results.items():
        if period == "daily":
            period_col = "Install_Day"
        elif period == "weekly":
            period_col = "Install_Week"
        else:
            period_col = "Install_Month"
            
        df = lf.collect().with_columns(
            pl.lit(period).alias("period_type"),
            pl.col(period_col).cast(pl.Utf8).alias("period_value"),
        )
        frames.append(df)
        
    combined = pl.concat(frames, how="diagonal")
    write_kpi("mi_progress", combined, {
        "Project": "project",
        "Discom": "discom", "Zone": "zone", "Circle": "circle",
        "Division": "division", "SubDivision": "subdivision",
        "SubStation": "substation", "Feeder": "feeder", "DTR": "dtr",
        "newMeterType": "new_meter_type", "MeterCategory": "meter_category",
        "Total_MI_Progress": "total_mi_progress",
    })

    # KPI 2
    log.info("KPI 2: MI Productivity")
    results = kpi_2_mi_productivity(df_install)
    frames = []
    for period, lf in results.items():
        if period == "daily":
            period_col = "Install_Day"
        elif period == "weekly":
            period_col = "Install_Week"
        else:
            period_col = "Install_Month"
            
        df = lf.collect().with_columns(
            pl.lit(period).alias("period_type"),
            pl.col(period_col).cast(pl.Utf8).alias("period_value"),
        )
        frames.append(df)
        
    combined = pl.concat(frames, how="diagonal")
    write_kpi("mi_productivity", combined, {
        "Project": "project",
        "Discom": "discom", "Zone": "zone", "Circle": "circle",
        "Division": "division", "SubDivision": "subdivision",
        "SubStation": "substation", "Feeder": "feeder", "DTR": "dtr",
        "newMeterType": "new_meter_type", "MeterCategory": "meter_category",
        "Technician": "technician",
        "Daily_Installations": "daily_installations",
    })

    # KPI 3
    log.info("KPI 3: Monthly Productivity")
    results = kpi_3_monthly_productivity(df_install)
    frames = []
    for period, lf in results.items():
        df = lf.collect().with_columns(
            pl.lit(period).alias("period_type"),
            pl.col("Install_Month").cast(pl.Utf8).alias("period_value"),
        )
        frames.append(df)
        
    combined = pl.concat(frames, how="diagonal")
    write_kpi("monthly_productivity", combined, {
        "Project": "project",
        "Discom": "discom", "Zone": "zone", "Circle": "circle",
        "Division": "division", "SubDivision": "subdivision",
        "SubStation": "substation", "Feeder": "feeder", "DTR": "dtr",
        "newMeterType": "new_meter_type", "MeterCategory": "meter_category",
        "Location_Monthly_Installations": "location_monthly_installations",
        "Total_Monthly_Installations": "total_monthly_installations",
    })

    # KPI 4 & 5
    log.info("KPI 4 & 5: Inventory Utilization")
    results4 = kpi_4_inventory_utilization(df_inventory, df_install)
    frames = []
    for period, lf in results4.items():
        period_col = "Install_Week" if period == "weekly" else "Install_Month"
        df = lf.collect().with_columns(
            pl.lit(period).alias("period_type"),
            pl.col(period_col).cast(pl.Utf8).alias("period_value"),
        )
        frames.append(df)
        
    results5 = kpi_5_mi_pace_vs_stock(df_inventory, df_install)
    for period, lf in results5.items():  # daily
        df = lf.collect().with_columns(
            pl.lit(period).alias("period_type"),
            pl.col("Install_Day").cast(pl.Utf8).alias("period_value"),
        )
        frames.append(df)

    combined = pl.concat(frames, how="diagonal")
    write_kpi("inventory_utilization", combined, {
        "Project": "project",
        "Discom": "discom", "Zone": "zone", "Circle": "circle",
        "Division": "division", "SubDivision": "subdivision",
        "SubStation": "substation", "Feeder": "feeder", "DTR": "dtr",
        "newMeterType": "new_meter_type", "MeterCategory": "meter_category",
        "Total_Inventory": "total_inventory",
        "Total_Installed": "total_installed",
        "Utilization_Rate_Pct": "utilization_rate_pct",
        "Remaining_Stock": "remaining_stock",
    })

    # KPI 6
    log.info("KPI 6: Stock Ageing")
    result = kpi_6_stock_ageing(df_inventory).collect()
    write_kpi("stock_ageing", result, {
        "MeterSerialNumber": "meter_serial_number",
        "parsed_DIDate": "di_date",
        "parsed_InstalledTS": "installed_ts",
        "Ageing_Days": "ageing_days",
    })

    # KPI 7
    log.info("KPI 7: MI vs SAT")
    result = kpi_7_mi_vs_sat(df_install).collect().with_columns(
        pl.lit("daily").alias("period_type"),
        pl.col("Install_Day").alias("period_value")
    )
    write_kpi("mi_vs_sat", result, {
        "Project": "project",
        "Discom": "discom", "Zone": "zone", "Circle": "circle",
        "Division": "division", "SubDivision": "subdivision",
        "SubStation": "substation", "Feeder": "feeder", "DTR": "dtr",
        "newMeterType": "new_meter_type", "MeterCategory": "meter_category",
        "period_type": "period_type", "period_value": "period_value",
        "total_mi": "total_mi", "total_sat": "total_sat",
        "sat_1": "sat_1", "sat_2": "sat_2", "sat_3": "sat_3",
        "sat_4": "sat_4", "sat_5": "sat_5", "sat_6": "sat_6", "sat_7": "sat_7",
        "sat_progress_pct": "sat_progress_pct",
    })

    log.info("═══ MI Pipeline finished ═══")


# ─────────────────────────────────────────────────────────────────────────
# O&M Pipeline
# ─────────────────────────────────────────────────────────────────────────

def run_om_pipeline():
    """Extract → Transform → Load for all 5 O&M KPIs."""
    import polars as pl
    from extract.om_complaints import extract_om_complaints
    from modules.om.transform import (
        kpi_1_productivity_per_team,
        kpi_2_productivity_trend,
        kpi_3_open_ageing,
        kpi_4_avg_closure_time,
        kpi_5_closed_analysis,
    )

    log.info("═══ O&M Pipeline started ═══")

    # ── EXTRACT ──
    df_om = extract_om_complaints()

    # Column mapping for O&M dimensions
    om_dim_map = {
        "Discom": "discom", "Zone": "zone", "Circle": "circle",
        "Division": "division", "SubDivision": "subdivision",
        "SubStation": "substation", "OM_Category": "om_category",
    }

    # ── KPI 1: Productivity per team (daily / weekly / monthly) ──
    log.info("O&M KPI 1: Productivity per team")
    results = kpi_1_productivity_per_team(df_om)
    frames = []
    for period, lf in results.items():
        period_col = f"Closed_{period.title().replace('ly','').replace('i','')}"
        # Find the correct period column name
        if period == "daily":
            period_col = "Closed_Day"
        elif period == "weekly":
            period_col = "Closed_Week"
        elif period == "monthly":
            period_col = "Closed_Month"

        df = lf.collect().with_columns(
            pl.lit(period).alias("period_type"),
            pl.col(period_col).cast(pl.Utf8).alias("period_value"),
        )
        frames.append(df)

    combined = pl.concat(frames, how="diagonal")
    write_kpi("om_productivity_team", combined, {
        **om_dim_map,
        "Technician": "technician", "Agency": "agency",
        "Closed_Tickets": "closed_tickets",
    })

    # ── KPI 2: Productivity trend ──
    log.info("O&M KPI 2: Productivity trend")
    result = kpi_2_productivity_trend(df_om).collect()
    write_kpi("om_productivity_trend", result, {
        **om_dim_map,
        "Closed_Month": "closed_month",
        "Total_Closed_Tickets": "total_closed_tickets",
    })

    # ── KPI 3: Open ageing ──
    log.info("O&M KPI 3: Open ticket ageing")
    result = kpi_3_open_ageing(df_om).collect()
    write_kpi("om_open_ageing", result, {
        **om_dim_map,
        "TicketId": "ticket_id",
        "Parsed_CreatedDate": "created_date",
        "Ageing_Days": "ageing_days",
        "Technician": "technician", "Agency": "agency",
    })

    # ── KPI 4: Avg closure time ──
    log.info("O&M KPI 4: Avg closure time")
    results = kpi_4_avg_closure_time(df_om)
    frames = []
    for period, lf in results.items():
        if period == "daily":
            cr, cl = "Created_Day", "Closed_Day"
        elif period == "weekly":
            cr, cl = "Created_Week", "Closed_Week"
        else:
            cr, cl = "Created_Month", "Closed_Month"

        df = lf.collect().with_columns(
            pl.lit(period).alias("period_type"),
            pl.col(cr).cast(pl.Utf8).alias("period_value_created"),
            pl.col(cl).cast(pl.Utf8).alias("period_value_closed"),
        )
        frames.append(df)

    combined = pl.concat(frames, how="diagonal")
    write_kpi("om_avg_closure_time", combined, {
        **om_dim_map,
        "Avg_Resolution_Days": "avg_resolution_days",
    })

    # ── KPI 5: Closed analysis ──
    log.info("O&M KPI 5: Closed analysis")
    results = kpi_5_closed_analysis(df_om)
    frames = []
    for period, lf in results.items():
        if period == "daily":
            period_col = "Closed_Day"
        elif period == "weekly":
            period_col = "Closed_Week"
        else:
            period_col = "Closed_Month"

        df = lf.collect().with_columns(
            pl.lit(period).alias("period_type"),
            pl.col(period_col).cast(pl.Utf8).alias("period_value"),
        )
        frames.append(df)

    combined = pl.concat(frames, how="diagonal")
    write_kpi("om_closed_analysis", combined, {
        **om_dim_map,
        "ComplaintType": "complaint_type",
        "ComplaintCategory": "complaint_category",
        "Closed_Tickets": "closed_tickets",
    })

    log.info("═══ O&M Pipeline finished ═══")

# ─────────────────────────────────────────────────────────────────────────
# CLI Entry-point
# ─────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Smart Meter ETL Pipeline")
    parser.add_argument(
        "--pipeline",
        choices=["mi", "om", "all"],
        default="all",
        help="Which pipeline to run (default: all)",
    )
    args = parser.parse_args()

    start = datetime.now()

    try:
        if args.pipeline in ("mi", "all"):
            run_mi_pipeline()

        if args.pipeline in ("om", "all"):
            run_om_pipeline()

    except Exception as e:
        log.exception("Pipeline failed")
        raise

    elapsed = datetime.now() - start
    log.info("Total elapsed: %s", elapsed)


if __name__ == "__main__":
    main()
