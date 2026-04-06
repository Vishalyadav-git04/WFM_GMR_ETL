"""
MI (Meter Installation) KPI transformations.
Each function accepts LazyFrame(s) and returns a LazyFrame – pure transforms, no I/O.
"""

from datetime import datetime
import polars as pl
from infrastructure.config.settings import MI_DIMENSIONS


# ── KPI 1 : MI Progress ─────────────────────────────────────────────────

def kpi_1_mi_progress(df_install: pl.LazyFrame) -> dict[str, pl.LazyFrame]:
    """Total meter installations grouped by dimensions and daily/weekly/monthly periods."""
    df = df_install.filter(pl.col("parsed_install_date").is_not_null()).with_columns(
        Install_Day=pl.col("parsed_install_date").dt.strftime("%Y-%m-%d"),
        Install_Week=pl.col("parsed_install_date").dt.strftime("%Y-W%U"),
        Install_Month=pl.col("parsed_install_date").dt.strftime("%Y-%m"),
    )

    results = {}
    
    # 1. Daily
    results["daily"] = df.group_by(MI_DIMENSIONS + ["Install_Day"]).agg(
        Total_MI_Progress=pl.len()
    )
    
    # 2. Weekly
    results["weekly"] = df.group_by(MI_DIMENSIONS + ["Install_Week"]).agg(
        Total_MI_Progress=pl.len()
    )
    
    # 3. Monthly
    results["monthly"] = df.group_by(MI_DIMENSIONS + ["Install_Month"]).agg(
        Total_MI_Progress=pl.len()
    )
    
    return results


# ── KPI 2 : MI Productivity ─────────────────────────────────────────────

def kpi_2_mi_productivity(df_install: pl.LazyFrame) -> dict[str, pl.LazyFrame]:
    """Productivity per team grouped by Technician and Daily/Weekly/Monthly."""
    df = df_install.filter(pl.col("parsed_install_date").is_not_null()).with_columns(
        Install_Day=pl.col("parsed_install_date").dt.strftime("%Y-%m-%d"),
        Install_Week=pl.col("parsed_install_date").dt.strftime("%Y-W%U"),
        Install_Month=pl.col("parsed_install_date").dt.strftime("%Y-%m"),
    )
    results = {}
    results["daily"] = df.group_by(MI_DIMENSIONS + ["Technician", "Install_Day"]).agg(pl.len().alias("Daily_Installations"))
    results["weekly"] = df.group_by(MI_DIMENSIONS + ["Technician", "Install_Week"]).agg(pl.len().alias("Daily_Installations"))
    results["monthly"] = df.group_by(MI_DIMENSIONS + ["Technician", "Install_Month"]).agg(pl.len().alias("Daily_Installations"))
    return results


# ── KPI 3 : Monthly Productivity Trend ──────────────────────────────────

def kpi_3_monthly_productivity(df_install: pl.LazyFrame) -> dict[str, pl.LazyFrame]:
    """Monthly installation counts at location and global level."""
    df = (
        df_install.filter(pl.col("parsed_install_date").is_not_null())
        .with_columns(
            pl.col("parsed_install_date").dt.strftime("%Y-%m").alias("Install_Month")
        )
        .group_by(MI_DIMENSIONS + ["Install_Month"])
        .agg(pl.len().alias("Location_Monthly_Installations"))
        .with_columns(
            pl.col("Location_Monthly_Installations").sum().over("Install_Month").alias("Total_Monthly_Installations")
        )
    )
    return {"monthly": df}


# ── KPI 4 : Inventory Utilization Rate ──────────────────────────────────

def kpi_4_inventory_utilization(
    df_inventory: pl.LazyFrame,
    df_install: pl.LazyFrame,
) -> dict[str, pl.LazyFrame]:
    """Inventory utilization rate (weekly/monthly)"""
    df_joined = df_inventory.join(
        df_install.select(["newMeterNumber", "parsed_install_date"] + MI_DIMENSIONS),
        left_on="MeterSerialNumber",
        right_on="newMeterNumber",
        how="left",
    ).with_columns(
        Install_Week=pl.col("parsed_install_date").dt.strftime("%Y-W%U"),
        Install_Month=pl.col("parsed_install_date").dt.strftime("%Y-%m"),
    )

    results = {}
    # Weekly
    results["weekly"] = df_joined.group_by(MI_DIMENSIONS + ["Install_Week"]).agg(
        pl.len().alias("Total_Inventory"),
        pl.col("parsed_install_date").is_not_null().sum().alias("Total_Installed"),
    ).with_columns(
        (pl.col("Total_Installed") / pl.col("Total_Inventory") * 100).alias("Utilization_Rate_Pct"),
        (pl.col("Total_Inventory") - pl.col("Total_Installed")).alias("Remaining_Stock"),
    )
    
    # Monthly
    results["monthly"] = df_joined.group_by(MI_DIMENSIONS + ["Install_Month"]).agg(
        pl.len().alias("Total_Inventory"),
        pl.col("parsed_install_date").is_not_null().sum().alias("Total_Installed"),
    ).with_columns(
        (pl.col("Total_Installed") / pl.col("Total_Inventory") * 100).alias("Utilization_Rate_Pct"),
        (pl.col("Total_Inventory") - pl.col("Total_Installed")).alias("Remaining_Stock"),
    )
    return results

# ── KPI 5 : MI Pace Vs Stock Availability ───────────────────────────────

def kpi_5_mi_pace_vs_stock(
    df_inventory: pl.LazyFrame,
    df_install: pl.LazyFrame,
) -> dict[str, pl.LazyFrame]:
    """Daily installations vs remaining stock"""
    df_joined = df_inventory.join(
        df_install.select(["newMeterNumber", "parsed_install_date"] + MI_DIMENSIONS),
        left_on="MeterSerialNumber",
        right_on="newMeterNumber",
        how="left",
    ).with_columns(
        Install_Day=pl.col("parsed_install_date").dt.strftime("%Y-%m-%d"),
    )
    
    results = {}
    results["daily"] = df_joined.group_by(MI_DIMENSIONS + ["Install_Day"]).agg(
        pl.len().alias("Total_Inventory"),
        pl.col("parsed_install_date").is_not_null().sum().alias("Total_Installed"),
    ).with_columns(
        (pl.col("Total_Installed") / pl.col("Total_Inventory") * 100).alias("Utilization_Rate_Pct"),
        (pl.col("Total_Inventory") - pl.col("Total_Installed")).alias("Remaining_Stock"),
    )
    return results

# ── KPI 6 : Unutilized Stock Ageing ─────────────────────────────────────

def kpi_6_stock_ageing(df_inventory: pl.LazyFrame) -> pl.LazyFrame:
    """Ageing days for meters that have not been installed."""
    return df_inventory.filter(
        pl.col("parsed_InstalledTS").is_null()
    ).with_columns(
        Ageing_Days=(datetime.today().date() - pl.col("parsed_DIDate")).dt.total_days()
    ).select([
        "MeterSerialNumber", "parsed_DIDate", "parsed_InstalledTS", "Ageing_Days"
    ])


# ── KPI 7 : MI vs SAT Progress ──────────────────────────────────────────

def kpi_7_mi_vs_sat(df_install: pl.LazyFrame) -> pl.LazyFrame:
    """MI count vs SAT count and detailed SAT stage tracking grouped by daily grain."""
    # 1. Base installations with stages
    df = df_install.with_columns(
        Install_Day=pl.col("parsed_install_date").dt.strftime("%Y-%m-%d"),
        sat_stage=pl.col("SAT_SAT_No").str.to_lowercase().str.strip_chars()
    )

    # 2. Daily Grouping with SAT stage pivot
    return df.group_by(MI_DIMENSIONS + ["Install_Day"]).agg(
        total_mi=pl.col("newMeterNumber").drop_nulls().count(),
        total_sat=pl.col("sat_stage").filter(pl.col("sat_stage").str.contains("sat-")).count(),
        sat_1=pl.col("sat_stage").filter(pl.col("sat_stage").str.contains("sat-1")).count(),
        sat_2=pl.col("sat_stage").filter(pl.col("sat_stage").str.contains("sat-2")).count(),
        sat_3=pl.col("sat_stage").filter(pl.col("sat_stage").str.contains("sat-3")).count(),
        sat_4=pl.col("sat_stage").filter(pl.col("sat_stage").str.contains("sat-4")).count(),
        sat_5=pl.col("sat_stage").filter(pl.col("sat_stage").str.contains("sat-5")).count(),
        sat_6=pl.col("sat_stage").filter(pl.col("sat_stage").str.contains("sat-6")).count(),
        sat_7=pl.col("sat_stage").filter(pl.col("sat_stage").str.contains("sat-7")).count(),
    ).with_columns(
        sat_progress_pct=pl.when(pl.col("total_mi") > 0)
        .then(pl.col("total_sat") / pl.col("total_mi") * 100)
        .otherwise(0.0)
    )
