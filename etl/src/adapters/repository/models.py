"""
SQLAlchemy ORM models for KPI result tables.
"""

from sqlalchemy import (
    Column, Integer, BigInteger, Float, String, Date, DateTime, Text,
    func,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# ── Helper mixin for the common MI dimension columns ────────────────────
class MIDimensionMixin:
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project = Column(String(200))
    discom = Column(String(200))
    zone = Column(String(200))
    circle = Column(String(200))
    division = Column(String(200))
    subdivision = Column(String(200))
    substation = Column(String(200))
    feeder = Column(String(200))
    dtr = Column(String(200))
    new_meter_type = Column(String(200))
    meter_category = Column(String(100))


class OMDimensionMixin:
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project = Column(String(200))
    discom = Column(String(200))
    zone = Column(String(200))
    circle = Column(String(200))
    division = Column(String(200))
    subdivision = Column(String(200))
    substation = Column(String(200))
    feeder = Column(String(200))
    dtr = Column(String(200))
    meter_category = Column(String(100))  # renamed from om_category


# ── MI KPI Tables ───────────────────────────────────────────────────────

class MIProgress(MIDimensionMixin, Base):
    __tablename__ = "mi_progress"
    period_type = Column(String(10))   # daily / weekly / monthly
    period_value = Column(String(50))  # the date or week/month string
    total_mi_progress = Column(BigInteger)


class MIProductivity(MIDimensionMixin, Base):
    __tablename__ = "mi_productivity"
    technician = Column(String(200))
    period_type = Column(String(10))   # daily / weekly / monthly
    period_value = Column(String(50))  # the date or week/month string
    daily_installations = Column(BigInteger)


class MonthlyProductivity(MIDimensionMixin, Base):
    __tablename__ = "monthly_productivity"
    period_type = Column(String(10))   # monthly
    period_value = Column(String(50))  # the month string
    location_monthly_installations = Column(BigInteger)
    total_monthly_installations = Column(BigInteger)


class InventoryUtilization(MIDimensionMixin, Base):
    __tablename__ = "inventory_utilization"
    period_type = Column(String(10))   # daily(KPI5) / weekly / monthly
    period_value = Column(String(50))  # the date or week/month string
    total_inventory = Column(BigInteger)
    total_installed = Column(BigInteger)
    utilization_rate_pct = Column(Float)
    remaining_stock = Column(BigInteger)


class StockAgeing(Base):
    __tablename__ = "stock_ageing"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    meter_serial_number = Column(String(100))
    di_date = Column(Date)
    installed_ts = Column(Date)
    ageing_days = Column(Integer)


class MIvsSAT(MIDimensionMixin, Base):
    __tablename__ = "mi_vs_sat"
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
    sat_progress_pct = Column(Float)


class NonSATAgeing(MIDimensionMixin, Base):
    __tablename__ = "non_sat_ageing"
    meter_serial_number = Column(String(100))
    installation_date = Column(Date)
    ageing_days = Column(Integer)

# ── Command Center Dashboard Tables ───────────────────────────────────────

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
    sat_1_achievement = Column(BigInteger)
    sat_2_achievement = Column(BigInteger)
    sat_3_achievement = Column(BigInteger)
    sat_4_achievement = Column(BigInteger)
    sat_5_achievement = Column(BigInteger)
    sat_6_achievement = Column(BigInteger)
    sat_7_achievement = Column(BigInteger)
    sat_8_achievement = Column(BigInteger, default=0)
    sat_1_throughput_pct = Column(Float)
    sat_2_throughput_pct = Column(Float)
    sat_3_throughput_pct = Column(Float)
    sat_4_throughput_pct = Column(Float)
    sat_5_throughput_pct = Column(Float)
    sat_6_throughput_pct = Column(Float)
    sat_7_throughput_pct = Column(Float)
    sat_8_throughput_pct = Column(Float, default=0)


class DashboardCommandCenterTrend(Base):
    __tablename__ = "dashboard_command_center_trend"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project = Column(String(200))
    period_type = Column(String(20))
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

class DashboardCommandCenterMilestone(Base):
    __tablename__ = "dashboard_command_center_milestone"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project = Column(String(200))
    stage = Column(String(20))
    start_date = Column(Date)
    lumpsum_inv_date = Column(Date)
    pmpm_inv_date = Column(Date)
    lumpsum_col_date = Column(Date)
    pmpm_col_date = Column(Date)


# ── O&M KPI Tables ─────────────────────────────────────────────────────

class OMProductivityTeam(OMDimensionMixin, Base):
    __tablename__ = "om_productivity_team"
    technician = Column(String(200))
    agency = Column(String(200))
    period_type = Column(String(10))   # daily / weekly / monthly
    period_value = Column(String(50))  # the date or month string
    closed_tickets = Column(BigInteger)


class OMProductivityTrend(OMDimensionMixin, Base):
    __tablename__ = "om_productivity_trend"
    closed_month = Column(String(20))
    total_closed_tickets = Column(BigInteger)


class OMOpenAgeing(OMDimensionMixin, Base):
    __tablename__ = "om_open_ageing"
    ticket_id = Column(String(100))
    created_date = Column(DateTime)
    ageing_days = Column(Float)
    technician = Column(String(200))
    agency = Column(String(200))


class OMAvgClosureTime(OMDimensionMixin, Base):
    __tablename__ = "om_avg_closure_time"
    period_type = Column(String(10))
    period_value_created = Column(String(50))
    period_value_closed = Column(String(50))
    avg_resolution_days = Column(Float)


class OMClosedAnalysis(OMDimensionMixin, Base):
    __tablename__ = "om_closed_analysis"
    complaint_type = Column(String(200))
    complaint_category = Column(String(200))
    period_type = Column(String(10))
    period_value = Column(String(50))
    closed_tickets = Column(BigInteger)


# ── ETL Run Log ─────────────────────────────────────────────────────────

class ETLRunLog(Base):
    __tablename__ = "etl_run_log"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    pipeline = Column(String(20))
    status = Column(String(20))
    started_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime)
    error = Column(Text)


class ComplaintsMaster(Base):
    __tablename__ = "complaints_master"
    ticket_id = Column(String(200), primary_key=True)
    complaint_type = Column(Text)
    complaint_category = Column(Text)
    complaint_description = Column(Text)
    complaint_status = Column(Text)
    created_date = Column(DateTime)
    closed_date = Column(DateTime)
    technician = Column(Text)
    agency = Column(Text)
    discom = Column(Text)
    zone = Column(Text)
    circle = Column(Text)
    division = Column(Text)
    subdivision = Column(Text)
    feeder = Column(Text)
    dtr = Column(Text)
    project = Column(Text)
    meter_category = Column(Text)

