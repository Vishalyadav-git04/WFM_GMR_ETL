from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

@dataclass
class MIDimension:
    project: Optional[str] = None
    discom: Optional[str] = None
    zone: Optional[str] = None
    circle: Optional[str] = None
    division: Optional[str] = None
    subdivision: Optional[str] = None
    substation: Optional[str] = None
    feeder: Optional[str] = None
    dtr: Optional[str] = None
    new_meter_type: Optional[str] = None
    meter_category: Optional[str] = None

@dataclass
class OMDimension:
    project: Optional[str] = None
    discom: Optional[str] = None
    zone: Optional[str] = None
    circle: Optional[str] = None
    division: Optional[str] = None
    subdivision: Optional[str] = None
    substation: Optional[str] = None
    feeder: Optional[str] = None
    dtr: Optional[str] = None
    meter_category: Optional[str] = None

@dataclass
class MIProgressEntity(MIDimension):
    period_type: str = ""
    period_value: str = ""
    total_mi_progress: int = 0

@dataclass
class MIProductivityEntity(MIDimension):
    technician: str = ""
    period_type: str = ""
    period_value: str = ""
    daily_installations: int = 0

@dataclass
class MonthlyProductivityEntity(MIDimension):
    period_type: str = "monthly"
    period_value: str = ""
    location_monthly_installations: int = 0
    total_monthly_installations: int = 0

@dataclass
class InventoryUtilizationEntity(MIDimension):
    period_type: str = ""
    period_value: str = ""
    total_inventory: int = 0
    total_installed: int = 0
    utilization_rate_pct: float = 0.0
    remaining_stock: int = 0

@dataclass
class StockAgeingEntity:
    meter_serial_number: str
    di_date: Optional[date] = None
    installed_ts: Optional[date] = None
    ageing_days: int = 0

@dataclass
class MIvsSATEntity(MIDimension):
    period_type: str = "daily"
    period_value: str = ""
    total_mi: int = 0
    total_sat: int = 0
    sat_1: int = 0
    sat_2: int = 0
    sat_3: int = 0
    sat_4: int = 0
    sat_5: int = 0
    sat_6: int = 0
    sat_7: int = 0
    sat_progress_pct: float = 0.0

@dataclass
class NonSATAgeingEntity(MIDimension):
    meter_serial_number: str = ""
    installation_date: Optional[date] = None
    ageing_days: int = 0

@dataclass
class OMProductivityTeamEntity(OMDimension):
    technician: str = ""
    agency: str = ""
    period_type: str = ""
    period_value: str = ""
    closed_tickets: int = 0

@dataclass
class OMProductivityTrendEntity(OMDimension):
    closed_month: str = ""
    total_closed_tickets: int = 0

@dataclass
class OMOpenAgeingEntity(OMDimension):
    ticket_id: str = ""
    created_date: Optional[datetime] = None
    ageing_days: float = 0.0
    technician: str = ""
    agency: str = ""

@dataclass
class OMAvgClosureTimeEntity(OMDimension):
    period_type: str = ""
    period_value_created: str = ""
    period_value_closed: str = ""
    avg_resolution_days: float = 0.0

@dataclass
class OMClosedAnalysisEntity(OMDimension):
    complaint_type: str = ""
    complaint_category: str = ""
    period_type: str = ""
    period_value: str = ""
    closed_tickets: int = 0

@dataclass
class ComplaintEntity(OMDimension):
    ticket_id: str = ""
    complaint_type: str = ""
    complaint_category: str = ""
    complaint_description: str = ""
    complaint_status: str = ""
    created_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None
    technician: str = ""
    agency: str = ""

@dataclass
class ETLRunLogEntity:
    pipeline: str
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    id: Optional[int] = None
