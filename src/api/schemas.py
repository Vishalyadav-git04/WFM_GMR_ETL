"""
Pydantic response schemas for API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime, date


# ── MI Schemas ───────────────────────────────────────────────────────────

class MIDimensionBase(BaseModel):
    project: Optional[str] = Field(None, description="Project name")
    discom: Optional[str] = Field(None, description="Distribution Company name")
    zone: Optional[str] = Field(None, description="Administrative Zone")
    circle: Optional[str] = Field(None, description="Administrative Circle")
    division: Optional[str] = Field(None, description="Administrative Division")
    subdivision: Optional[str] = Field(None, description="Administrative Sub-Division")
    substation: Optional[str] = Field(None, description="Connected Sub-Station")
    feeder: Optional[str] = Field(None, description="Connected Feeder")
    dtr: Optional[str] = Field(None, description="Connected Distribution Transformer (DTR)")
    new_meter_type: Optional[str] = Field(None, description="Type of meter (1PH, 3PH, etc.)")
    meter_category: Optional[str] = Field(None, description="Category of meter (Consumer, Feeder, DT)")

    class Config:
        from_attributes = True


class MIProgressOut(MIDimensionBase):
    period_type: Optional[str] = Field(None, description="Grouping period: daily, weekly, or monthly")
    period_value: Optional[str] = Field(None, description="The specific date or period value")
    total_mi_progress: Optional[int] = Field(None, description="Count of meters installed in this period/region")


class MIProgressSummaryOut(BaseModel):
    total_progress: int = Field(..., description="Total installations across all selected filters")
    category_breakdown: Dict[str, int] = Field(..., description="Installations broken down by Meter Category")
    period_breakdown: List[Dict[str, Any]] = Field(..., description="Trend data showing installations over time")


class MIProductivityOut(MIDimensionBase):
    technician: Optional[str] = Field(None, description="Name of the technician")
    period_type: Optional[str] = Field(None, description="Grouping period: daily, weekly, or monthly")
    period_value: Optional[str] = Field(None, description="The specific date or period value")
    daily_installations: Optional[int] = Field(None, description="Total installations done by this technician")


class MonthlyProductivityOut(MIDimensionBase):
    period_type: Optional[str] = Field(None, description="Usually 'monthly'")
    period_value: Optional[str] = Field(None, description="Month in YYYY-MM format")
    location_monthly_installations: Optional[int] = Field(None, description="Installations for this specific location/month")
    total_monthly_installations: Optional[int] = Field(None, description="Global total installations for this month (across all regions)")

class MonthlyProductivitySummaryOut(BaseModel):
    total_installations: int = Field(..., description="Total cumulative installations for the selected month/filters")
    period_value: str = Field(..., description="Month in YYYY-MM format")


class InventoryUtilizationOut(MIDimensionBase):
    period_type: Optional[str] = Field(None, description="Grouping period")
    period_value: Optional[str] = Field(None, description="The specific date or period value")
    total_inventory: Optional[int] = Field(None, description="Total stock available")
    total_installed: Optional[int] = Field(None, description="Total meters installed from stock")
    utilization_rate_pct: Optional[float] = Field(None, description="Percentage of inventory utilized")
    remaining_stock: Optional[int] = Field(None, description="Inventory still in stock")

class InventoryUtilizationSummaryOut(BaseModel):
    total_inventory: int = Field(..., description="Total stock count")
    total_installed: int = Field(..., description="Total installed count")
    utilization_rate_pct: float = Field(..., description="Overall utilization percentage")
    remaining_stock: int = Field(..., description="Overall remaining stock")


class StockAgeingOut(BaseModel):
    meter_serial_number: Optional[str] = Field(None, description="Unique Meter Serial Number")
    di_date: Optional[date] = Field(None, description="Dispatch Date of the meter")
    installed_ts: Optional[date] = Field(None, description="Installation Date (null if not installed)")
    ageing_days: Optional[int] = Field(None, description="Number of days the meter has been in unutilized stock")

    class Config:
        from_attributes = True



class MIvsSATOut(MIDimensionBase):
    period_type: Optional[str] = Field(None, description="Grouping period: daily")
    period_value: Optional[str] = Field(None, description="The specific date value")
    total_mi: Optional[int] = Field(None, description="Total Meters Installed")
    total_sat: Optional[int] = Field(None, description="Total SATs completed")
    sat_1: Optional[int] = Field(0, description="SAT Stage 1 count")
    sat_2: Optional[int] = Field(0, description="SAT Stage 2 count")
    sat_3: Optional[int] = Field(0, description="SAT Stage 3 count")
    sat_4: Optional[int] = Field(0, description="SAT Stage 4 count")
    sat_5: Optional[int] = Field(0, description="SAT Stage 5 count")
    sat_6: Optional[int] = Field(0, description="SAT Stage 6 count")
    sat_7: Optional[int] = Field(0, description="SAT Stage 7 count")
    sat_progress_pct: Optional[float] = Field(None, description="Percentage of SAT completion vs MI")


class MIvsSATSummaryOut(BaseModel):
    total_mi: int = Field(..., description="Cumulative Total MI")
    total_sat: int = Field(..., description="Cumulative Total SAT")
    sat_1: int = Field(0, description="Total SAT Stage 1")
    sat_2: int = Field(0, description="Total SAT Stage 2")
    sat_3: int = Field(0, description="Total SAT Stage 3")
    sat_4: int = Field(0, description="Total SAT Stage 4")
    sat_5: int = Field(0, description="Total SAT Stage 5")
    sat_6: int = Field(0, description="Total SAT Stage 6")
    sat_7: int = Field(0, description="Total SAT Stage 7")
    sat_progress_pct: float = Field(..., description="Overall SAT progress percentage")


# ── O&M Schemas ──────────────────────────────────────────────────────────

class OMDimensionBase(BaseModel):
    discom: Optional[str] = None
    zone: Optional[str] = None
    circle: Optional[str] = None
    division: Optional[str] = None
    subdivision: Optional[str] = None
    substation: Optional[str] = None
    om_category: Optional[str] = None

    class Config:
        from_attributes = True


class OMProductivityTeamOut(OMDimensionBase):
    technician: Optional[str] = None
    agency: Optional[str] = None
    period_type: Optional[str] = None
    period_value: Optional[str] = None
    closed_tickets: Optional[int] = None


class OMProductivityTrendOut(OMDimensionBase):
    closed_month: Optional[str] = None
    total_closed_tickets: Optional[int] = None


class OMOpenAgeingOut(OMDimensionBase):
    ticket_id: Optional[str] = None
    created_date: Optional[datetime] = None
    ageing_days: Optional[float] = None
    technician: Optional[str] = None
    agency: Optional[str] = None


class OMAvgClosureTimeOut(OMDimensionBase):
    period_type: Optional[str] = None
    period_value_created: Optional[str] = None
    period_value_closed: Optional[str] = None
    avg_resolution_days: Optional[float] = None


class OMClosedAnalysisOut(OMDimensionBase):
    complaint_type: Optional[str] = None
    complaint_category: Optional[str] = None
    period_type: Optional[str] = None
    period_value: Optional[str] = None
    closed_tickets: Optional[int] = None
