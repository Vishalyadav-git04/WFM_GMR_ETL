"""
SQLAlchemy ORM models for the parallel (Shadow) KPI result tables.
These tables prefix the original table names with `sql_` to allow
pure SQL push-down logic to be safely tested alongside the original tables.
"""

from sqlalchemy import Column, Integer, BigInteger, Float, String, Date, DateTime
from .models import Base, MIDimensionMixin, OMDimensionMixin

# ── MI KPI Tables (Shadow) ───────────────────────────────────────────────────────

class SqlMIProgress(MIDimensionMixin, Base):
    __tablename__ = "sql_mi_progress"
    period_type = Column(String(10))   # daily / weekly / monthly
    period_value = Column(String(50))  # the date or week/month string
    total_mi_progress = Column(BigInteger)


class SqlMIProductivity(MIDimensionMixin, Base):
    __tablename__ = "sql_mi_productivity"
    technician = Column(String(200))
    period_type = Column(String(10))   # daily / weekly / monthly
    period_value = Column(String(50))  # the date or week/month string
    daily_installations = Column(BigInteger)


class SqlMonthlyProductivity(MIDimensionMixin, Base):
    __tablename__ = "sql_monthly_productivity"
    period_type = Column(String(10))   # monthly
    period_value = Column(String(50))  # the month string
    location_monthly_installations = Column(BigInteger)
    total_monthly_installations = Column(BigInteger)


class SqlInventoryUtilization(MIDimensionMixin, Base):
    __tablename__ = "sql_inventory_utilization"
    period_type = Column(String(10))   # daily(KPI5) / weekly / monthly
    period_value = Column(String(50))  # the date or week/month string
    total_inventory = Column(BigInteger)
    total_installed = Column(BigInteger)
    utilization_rate_pct = Column(Float)
    remaining_stock = Column(BigInteger)


class SqlStockAgeing(MIDimensionMixin, Base):
    __tablename__ = "sql_stock_ageing"
    period_type = Column(String(10))   # monthly
    period_value = Column(String(50))  # the date string
    age_0_30 = Column(BigInteger, default=0)
    age_31_60 = Column(BigInteger, default=0)
    age_61_90 = Column(BigInteger, default=0)
    age_90_plus = Column(BigInteger, default=0)


class SqlMIvsSAT(MIDimensionMixin, Base):
    __tablename__ = "sql_mi_vs_sat"
    period_type = Column(String(10))   # daily
    period_value = Column(String(50))  # the date
    total_mi = Column(BigInteger)
    total_sat = Column(BigInteger)
    sat_1 = Column(BigInteger, default=0)
    sat_2 = Column(BigInteger, default=0)
    sat_3 = Column(BigInteger, default=0)
    sat_4 = Column(BigInteger, default=0)
    sat_5 = Column(BigInteger, default=0)
    sat_6 = Column(BigInteger, default=0)
    sat_7 = Column(BigInteger, default=0)
    sat_8 = Column(BigInteger, default=0)
    sat_9 = Column(BigInteger, default=0)
    sat_progress_pct = Column(Float)


class SqlNonSATAgeing(MIDimensionMixin, Base):
    __tablename__ = "sql_non_sat_ageing"
    meter_serial_number = Column(String(100))
    installation_date = Column(Date)
    ageing_days = Column(Integer)


class SqlMeterJourneyAvgTime(MIDimensionMixin, Base):
    __tablename__ = "sql_meter_journey_avg_time"
    period_type = Column(String(20))
    period_value = Column(String(50))
    inventory_to_store = Column(Float)
    store_to_agency = Column(Float)
    agency_to_meter_installation = Column(Float)
    meter_installation_to_sat = Column(Float)
    sat_to_invoice = Column(Float)
    invoice_to_revenue = Column(Float)
    total_journey = Column(Float)
    meter_count = Column(BigInteger)


class SqlMeterCurrentStage(MIDimensionMixin, Base):
    __tablename__ = "sql_meter_current_stage"
    # Pre-aggregated funnel metrics (replaces stage-based columns)
    inventory = Column(BigInteger, nullable=False, default=0)
    installed = Column(BigInteger, nullable=False, default=0)
    sat_done = Column(BigInteger, nullable=False, default=0)
    revenue_collected = Column(BigInteger, nullable=False, default=0)


# ── Dashboard Command Center Tables ───────────────────────────────────────

class DashboardCommandCenter(Base):
    __tablename__ = "dashboard_command_center"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project = Column(String(200))
    inventory = Column(BigInteger)
    installed = Column(BigInteger)
    total_sat = Column(BigInteger)
    total_invoice = Column(BigInteger)
    sat_1_eligibility = Column(BigInteger)
    sat_2_eligibility = Column(BigInteger)
    sat_3_eligibility = Column(BigInteger)
    sat_4_eligibility = Column(BigInteger)
    sat_5_eligibility = Column(BigInteger)
    sat_6_eligibility = Column(BigInteger)
    sat_7_eligibility = Column(BigInteger)
    sat_8_eligibility = Column(BigInteger, default=0)
    sat_9_eligibility = Column(BigInteger, default=0)
    sat_1_achievement = Column(BigInteger)
    sat_2_achievement = Column(BigInteger)
    sat_3_achievement = Column(BigInteger)
    sat_4_achievement = Column(BigInteger)
    sat_5_achievement = Column(BigInteger)
    sat_6_achievement = Column(BigInteger)
    sat_7_achievement = Column(BigInteger)
    sat_8_achievement = Column(BigInteger, default=0)
    sat_9_achievement = Column(BigInteger, default=0)
    sat_1_throughput_pct = Column(Float)
    sat_2_throughput_pct = Column(Float)
    sat_3_throughput_pct = Column(Float)
    sat_4_throughput_pct = Column(Float)
    sat_5_throughput_pct = Column(Float)
    sat_6_throughput_pct = Column(Float)
    sat_7_throughput_pct = Column(Float)
    sat_8_throughput_pct = Column(Float, default=0)
    sat_9_throughput_pct = Column(Float, default=0)


class DashboardCommandCenterTrend(Base):
    __tablename__ = "dashboard_command_center_trend"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project = Column(String(200))
    period_type = Column(String(50))
    period_value = Column(String(50))
    inventory_added = Column(BigInteger)
    installed_added = Column(BigInteger)
    s1_added = Column(BigInteger)
    s2_added = Column(BigInteger)
    s3_added = Column(BigInteger)
    s4_added = Column(BigInteger)
    s5_added = Column(BigInteger)
    s6_added = Column(BigInteger)
    s7_added = Column(BigInteger)
    s8_added = Column(BigInteger, default=0)
    s9_added = Column(BigInteger, default=0)


class DashboardCommandCenterMilestone(Base):
    __tablename__ = "dashboard_command_center_milestone"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project = Column(String(200))
    stage = Column(String(50))
    start_date = Column(Date)
    lumpsum_inv_date = Column(Date)
    pmpm_inv_date = Column(Date)
    lumpsum_col_date = Column(Date)
    pmpm_col_date = Column(Date)


# ── O&M KPI Tables (Shadow) ─────────────────────────────────────────────────────

class SqlOMProductivityTeam(OMDimensionMixin, Base):
    __tablename__ = "sql_om_productivity_team"
    technician = Column(String(200))
    agency = Column(String(200))
    period_type = Column(String(10))   # daily / weekly / monthly
    period_value = Column(String(50))  # the date or month string
    closed_tickets = Column(BigInteger)


class SqlOMProductivityTrend(OMDimensionMixin, Base):
    __tablename__ = "sql_om_productivity_trend"
    closed_month = Column(String(20))
    total_closed_tickets = Column(BigInteger)


class SqlOMOpenAgeing(OMDimensionMixin, Base):
    __tablename__ = "sql_om_open_ageing"
    ticket_id = Column(String(100))
    created_date = Column(DateTime)
    ageing_days = Column(Float)
    technician = Column(String(200))
    agency = Column(String(200))
    complaint_by = Column(String(200))


class SqlOMAvgClosureTime(OMDimensionMixin, Base):
    __tablename__ = "sql_om_avg_closure_time"
    period_type = Column(String(10))
    period_value_created = Column(String(50))
    period_value_closed = Column(String(50))
    avg_resolution_days = Column(Float)


class SqlOMClosedAnalysis(OMDimensionMixin, Base):
    __tablename__ = "sql_om_closed_analysis"
    complaint_type = Column(String(200))
    complaint_category = Column(String(200))
    period_type = Column(String(10))
    period_value = Column(String(50))
    closed_tickets = Column(BigInteger)
