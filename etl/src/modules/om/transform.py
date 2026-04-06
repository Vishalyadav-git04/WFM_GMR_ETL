"""
O&M (Operations & Maintenance) KPI transformations.
Each function returns a dict[str, pl.LazyFrame] keyed by period granularity.
"""

from datetime import datetime
import polars as pl
from infrastructure.config.settings import OM_DIMENSIONS


# ── KPI 1 : Productivity per team (daily / weekly / monthly) ────────────

def kpi_1_productivity_per_team(df: pl.LazyFrame) -> dict[str, pl.LazyFrame]:
    df_closed = df.filter(pl.col("ComplaintStatus") == "Closed")
    base = OM_DIMENSIONS + ["Technician", "Agency"]
    return {
        "daily":   df_closed.group_by(base + ["Closed_Day"]).agg(pl.len().alias("Closed_Tickets")),
        "weekly":  df_closed.group_by(base + ["Closed_Week"]).agg(pl.len().alias("Closed_Tickets")),
        "monthly": df_closed.group_by(base + ["Closed_Month"]).agg(pl.len().alias("Closed_Tickets")),
    }


# ── KPI 2 : Productivity trend (monthly) ────────────────────────────────

def kpi_2_productivity_trend(df: pl.LazyFrame) -> pl.LazyFrame:
    df_closed = df.filter(pl.col("ComplaintStatus") == "Closed")
    return df_closed.group_by(OM_DIMENSIONS + ["Closed_Month"]).agg(
        pl.len().alias("Total_Closed_Tickets")
    )


# ── KPI 3 : Not-closed ticket ageing ────────────────────────────────────

def kpi_3_open_ageing(df: pl.LazyFrame) -> pl.LazyFrame:
    df_open = df.filter(pl.col("ComplaintStatus") != "Closed")
    return df_open.with_columns(
        Ageing_Days=(datetime.now() - pl.col("Parsed_CreatedDate")).dt.total_days()
    ).select(
        OM_DIMENSIONS + ["TicketId", "Parsed_CreatedDate", "Ageing_Days", "Technician", "Agency"]
    )


# ── KPI 4 : Avg ticket closure time (daily / weekly / monthly) ──────────

def kpi_4_avg_closure_time(df: pl.LazyFrame) -> dict[str, pl.LazyFrame]:
    df_closed = df.filter(pl.col("ComplaintStatus") == "Closed")
    df_ct = df_closed.with_columns(
        Resolution_Days=(pl.col("Parsed_ClosedDate") - pl.col("Parsed_CreatedDate")).dt.total_days()
    )
    return {
        "daily":   df_ct.group_by(OM_DIMENSIONS + ["Created_Day",  "Closed_Day"]).agg(
            pl.col("Resolution_Days").mean().alias("Avg_Resolution_Days")),
        "weekly":  df_ct.group_by(OM_DIMENSIONS + ["Created_Week", "Closed_Week"]).agg(
            pl.col("Resolution_Days").mean().alias("Avg_Resolution_Days")),
        "monthly": df_ct.group_by(OM_DIMENSIONS + ["Created_Month","Closed_Month"]).agg(
            pl.col("Resolution_Days").mean().alias("Avg_Resolution_Days")),
    }


# ── KPI 5 : Closed ticket analysis (daily / weekly / monthly) ───────────

def kpi_5_closed_analysis(df: pl.LazyFrame) -> dict[str, pl.LazyFrame]:
    df_closed = df.filter(pl.col("ComplaintStatus") == "Closed")
    base = OM_DIMENSIONS + ["ComplaintType", "ComplaintCategory"]
    return {
        "daily":   df_closed.group_by(base + ["Closed_Day"]).agg(pl.len().alias("Closed_Tickets")),
        "weekly":  df_closed.group_by(base + ["Closed_Week"]).agg(pl.len().alias("Closed_Tickets")),
        "monthly": df_closed.group_by(base + ["Closed_Month"]).agg(pl.len().alias("Closed_Tickets")),
    }
