"""
Pydantic response schemas for API endpoints.
"""

import math
from typing import Annotated, Optional, Dict, List, Any

from pydantic import BaseModel, BeforeValidator, Field
from datetime import datetime, date


# ── MI Schemas ───────────────────────────────────────────────────────────

class AgeingBucketBreakdown(BaseModel):
    CONSUMER: int = 0
    FEEDER: int = 0
    DT: int = 0
    total: int = 0


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






class MIProgressDashboardTrendPoint(BaseModel):
    period_value: str = Field(..., description="The specific period value (date/week/month bucket)")
    CONSUMER: int = Field(0, description="MI progress count for CONSUMER category")
    FEEDER: int = Field(0, description="MI progress count for FEEDER category")
    DT: int = Field(0, description="MI progress count for DT category")


class MIProgressDashboardComparisonItem(BaseModel):
    label: str = Field(..., description="Bar label (project or project|level label)")
    CONSUMER: int = Field(0, description="MI progress count for CONSUMER category")
    FEEDER: int = Field(0, description="MI progress count for FEEDER category")
    DT: int = Field(0, description="MI progress count for DT category")
    count: int = Field(..., description="Total MI progress count (sum of all categories)")


class MIProgressDashboardOut(BaseModel):
    total_progress: int = Field(..., description="Cumulative MI progress total for the selected filters")
    category_breakdown: Dict[str, Any] = Field(default_factory=dict, description="Nested: meter_category -> meter_type -> {count}")
    trend: List[MIProgressDashboardTrendPoint] = Field(default_factory=list, description="Trend series for MI Progress chart")
    comparison: List[MIProgressDashboardComparisonItem] = Field(default_factory=list, description="Comparison-by-cluster bar chart data")


class MIProductivityOut(MIDimensionBase):
    technician: Optional[str] = Field(None, description="Name of the technician")
    period_type: Optional[str] = Field(None, description="Grouping period: daily, weekly, or monthly")
    period_value: Optional[str] = Field(None, description="The specific date or period value")
    daily_installations: Optional[int] = Field(None, description="Total installations done by this technician")


class MITeamProductivitySummary(BaseModel):
    total_installations: int = 0
    total_active_technicians: int = 0
    total_active_days: int = 0
    productivity_per_technician_per_day: float = 0.0


class MITeamProductivityInsights(BaseModel):
    top_performing_technician: Dict[str, Any] = Field(default_factory=dict)
    lowest_performing_technician: Dict[str, Any] = Field(default_factory=dict)


class MITeamProductivityTrendPoint(BaseModel):
    date: str
    total_installations: int = 0
    active_technicians: int = 0
    productivity_per_technician_per_day: float = 0.0


class MITeamProductivityComparisonItem(BaseModel):
    label: str
    total_installations: int = 0
    active_technicians: int = 0
    productivity_per_technician_per_day: float = 0.0


class MITeamProductivityDashboardOut(BaseModel):
    summary: MITeamProductivitySummary
    insights: MITeamProductivityInsights
    trend: List[MITeamProductivityTrendPoint] = Field(default_factory=list)
    comparison: List[MITeamProductivityComparisonItem] = Field(default_factory=list)
    category_breakdown: Dict[str, Any] = Field(default_factory=dict)


class MonthlyProductivityOut(MIDimensionBase):
    period_type: Optional[str] = Field(None, description="Usually 'monthly'")
    period_value: Optional[str] = Field(None, description="Month in YYYY-MM format")
    location_monthly_installations: Optional[int] = Field(None, description="Installations for this specific location/month")
    total_monthly_installations: Optional[int] = Field(None, description="Global total installations for this month (across all regions)")

class MonthlyProductivitySummaryOut(BaseModel):
    total_installations: int = Field(..., description="Total cumulative installations for the selected month/filters")
    period_value: Optional[str] = Field(None, description="Month in YYYY-MM format")
    category_breakdown: Dict[str, Any] = Field(default_factory=dict)
    period_breakdown: Dict[str, Any] = Field(default_factory=dict)


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
    category_breakdown: Dict[str, Any] = Field(default_factory=dict)
    period_breakdown: Dict[str, Any] = Field(default_factory=dict)
    comparison: List[Dict[str, Any]] = Field(default_factory=list, description="Comparison-by-cluster bar chart data")


class PaceVsStockSummaryOut(InventoryUtilizationSummaryOut):
    """Same structure as Inventory Utilization but frontend uses remaining_stock instead of utilization_rate_pct in comparison."""
    pass


class StockAgeingOut(BaseModel):
    # Backward compatibility or granular view if needed
    age_0_30: Optional[int] = 0
    age_31_60: Optional[int] = 0
    age_61_90: Optional[int] = 0
    age_90_plus: Optional[int] = 0

    class Config:
        from_attributes = True


class StockAgeingSummaryOut(BaseModel):
    category_breakdown: Dict[str, Any] = Field(default_factory=dict)
    period_breakdown: Dict[str, Any] = Field(default_factory=dict)


class StockAgeingPeriodTrendPoint(BaseModel):
    period_value: str
    age_0_30: int = 0
    age_31_60: int = 0
    age_61_90: int = 0
    age_90_plus: int = 0
    total_stock: int = 0


class StockAgeingComparisonItem(BaseModel):
    label: str
    age_0_30: AgeingBucketBreakdown = Field(default_factory=AgeingBucketBreakdown)
    age_31_60: AgeingBucketBreakdown = Field(default_factory=AgeingBucketBreakdown)
    age_61_90: AgeingBucketBreakdown = Field(default_factory=AgeingBucketBreakdown)
    age_90_plus: AgeingBucketBreakdown = Field(default_factory=AgeingBucketBreakdown)
    total_stock: int = 0


class StockAgeingDashboardOut(BaseModel):
    total_stock: int = Field(..., description="Overall total stock")
    category_breakdown: Dict[str, Any] = Field(default_factory=dict)
    period_breakdown: List[StockAgeingPeriodTrendPoint] = Field(default_factory=list)
    comparison: List[StockAgeingComparisonItem] = Field(default_factory=list)



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
    sat_8: Optional[int] = Field(0, description="SAT Stage 8 count")
    sat_9: Optional[int] = Field(0, description="SAT Stage 9 count")
    sat_progress_pct: Optional[float] = Field(None, description="Percentage of SAT completion vs MI")


class MIvsSATComparisonItem(BaseModel):
    label: str = Field(..., description="Bar label (project or project|level label)")
    CONSUMER: int = Field(0, description="Total MI count for CONSUMER category")
    FEEDER: int = Field(0, description="Total MI count for FEEDER category")
    DT: int = Field(0, description="Total MI count for DT category")
    total_mi: int = Field(..., description="Total MI across all categories")
    total_sat: int = Field(..., description="Total SAT across all categories")
    sat_progress_pct: float = Field(..., description="SAT progress percentage")


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
    sat_8: int = Field(0, description="Total SAT Stage 8")
    sat_9: int = Field(0, description="Total SAT Stage 9")
    sat_progress_pct: float = Field(..., description="Overall SAT progress percentage")
    category_breakdown: Dict[str, Any] = Field(default_factory=dict)
    period_breakdown: Dict[str, Any] = Field(default_factory=dict)
    comparison: List[MIvsSATComparisonItem] = Field(default_factory=list, description="Comparison-by-cluster bar chart data")


class MINonSATAgeingOut(MIDimensionBase):
    meter_serial_number: Optional[str] = Field(None, description="Unique Meter Serial Number")
    installation_date: Optional[date] = Field(None, description="Date of installation")
    ageing_days: Optional[int] = Field(None, description="Number of days since installation (Ageing)")


class NonSATAgeingPeriodTrendPoint(BaseModel):
    period_value: str
    age_0_30: int = 0
    age_31_60: int = 0
    age_61_90: int = 0
    age_91_120: int = 0
    age_120_plus: int = 0
    total_non_sat: int = 0





class NonSATAgeingComparisonItem(BaseModel):
    label: str
    CONSUMER: int = 0
    FEEDER: int = 0
    DT: int = 0
    count: int = 0
    age_0_30: AgeingBucketBreakdown = Field(default_factory=AgeingBucketBreakdown)
    age_31_60: AgeingBucketBreakdown = Field(default_factory=AgeingBucketBreakdown)
    age_61_90: AgeingBucketBreakdown = Field(default_factory=AgeingBucketBreakdown)
    age_91_120: AgeingBucketBreakdown = Field(default_factory=AgeingBucketBreakdown)
    age_120_plus: AgeingBucketBreakdown = Field(default_factory=AgeingBucketBreakdown)
    total_non_sat: int = 0


class NonSATAgeingSummary(BaseModel):
    age_0_30: AgeingBucketBreakdown = Field(default_factory=AgeingBucketBreakdown)
    age_31_60: AgeingBucketBreakdown = Field(default_factory=AgeingBucketBreakdown)
    age_61_90: AgeingBucketBreakdown = Field(default_factory=AgeingBucketBreakdown)
    age_91_120: AgeingBucketBreakdown = Field(default_factory=AgeingBucketBreakdown)
    age_120_plus: AgeingBucketBreakdown = Field(default_factory=AgeingBucketBreakdown)
    total_non_sat: int = 0


class NonSATAgeingDashboardOut(BaseModel):
    total_non_sat: int = Field(..., description="Overall total non sat count")
    category_breakdown: Dict[str, int] = Field(default_factory=dict)
    summary: NonSATAgeingSummary = Field(default_factory=NonSATAgeingSummary)
    period_breakdown: List[NonSATAgeingPeriodTrendPoint] = Field(default_factory=list)
    comparison: List[NonSATAgeingComparisonItem] = Field(default_factory=list)


def _meter_journey_whole_days(v: Any) -> Any:
    """
    Whole days for API: **always round up** any fractional day using ``math.ceil`` (e.g. ``23.01`` → ``24``, ``23.0`` → ``23``).
    """
    if v is None:
        return None
    try:
        return int(math.ceil(float(v)))
    except (TypeError, ValueError):
        return None


MeterJourneyWholeDays = Annotated[
    Optional[int],
    BeforeValidator(_meter_journey_whole_days),
]


class MeterJourneyOut(MIDimensionBase):
    inventory_to_store: MeterJourneyWholeDays = Field(
        None,
        description="Avg whole days inventory to store (ceil of mean; see contract)",
    )
    store_to_agency: MeterJourneyWholeDays = Field(
        None, description="Avg whole days store handoff to agency (ceil of mean)"
    )
    agency_to_meter_installation: MeterJourneyWholeDays = Field(
        None, description="Avg whole days agency to meter installation (ceil of mean)"
    )
    meter_installation_to_sat: MeterJourneyWholeDays = Field(
        None, description="Avg whole days installation to SAT (ceil of mean)"
    )
    sat_to_invoice: MeterJourneyWholeDays = Field(None, description="Avg whole days SAT to PMPM invoice (ceil of mean)")
    invoice_to_revenue: MeterJourneyWholeDays = Field(
        None, description="Avg whole days PMPM invoice to revenue (ceil of mean)"
    )
    total_journey: MeterJourneyWholeDays = Field(None, description="Avg whole end-to-end days (ceil of mean)")
    period_type: Optional[str] = Field(
        None, description="ETL bucket: daily, weekly, or monthly (pmpm_collection_date)"
    )
    period_value: Optional[str] = Field(None, description="Bucket label, typically DD-MM-YY")
    meter_count: Optional[int] = Field(None, description="Meters in this aggregate (revenue-completed cohort)")


class MeterJourneyDashboardTrendPoint(BaseModel):
    period_value: str = Field(
        ...,
        description="Time bucket label (DD-MM-YY from ETL, bucketed by duration)",
    )
    inventory_to_store: MeterJourneyWholeDays = None
    store_to_agency: MeterJourneyWholeDays = None
    agency_to_meter_installation: MeterJourneyWholeDays = None
    meter_installation_to_sat: MeterJourneyWholeDays = None
    sat_to_invoice: MeterJourneyWholeDays = None
    invoice_to_revenue: MeterJourneyWholeDays = None
    total_journey: MeterJourneyWholeDays = None
    meter_count: int = Field(0, description="Meters with revenue in this period bucket")


class MeterJourneyDashboardComparisonItem(BaseModel):
    label: str = Field(..., description="Cluster label (project or project|level)")
    inventory_to_store: MeterJourneyWholeDays = None
    store_to_agency: MeterJourneyWholeDays = None
    agency_to_meter_installation: MeterJourneyWholeDays = None
    meter_installation_to_sat: MeterJourneyWholeDays = None
    sat_to_invoice: MeterJourneyWholeDays = None
    invoice_to_revenue: MeterJourneyWholeDays = None
    total_journey: MeterJourneyWholeDays = None
    meter_count: int = Field(0, description="Meters in this cluster for the cohort")


class MeterJourneyDashboardSummary(BaseModel):
    inventory_to_store: MeterJourneyWholeDays = None
    store_to_agency: MeterJourneyWholeDays = None
    agency_to_meter_installation: MeterJourneyWholeDays = None
    meter_installation_to_sat: MeterJourneyWholeDays = None
    sat_to_invoice: MeterJourneyWholeDays = None
    invoice_to_revenue: MeterJourneyWholeDays = None
    total_journey: MeterJourneyWholeDays = None
    meter_count: int = Field(0, description="Total meters in filtered cohort")


class MeterJourneyDashboardOut(BaseModel):
    summary: MeterJourneyDashboardSummary = Field(..., description="Cohort-wide weighted averages from pre-aggregated rows")
    trend: List[MeterJourneyDashboardTrendPoint] = Field(
        default_factory=list,
        description="One row per period_value in range (weighted roll-up across geography for each bucket)",
    )
    comparison: List[MeterJourneyDashboardComparisonItem] = Field(
        default_factory=list, description="One row per cluster after level/project rules"
    )


class FunnelMetricItem(BaseModel):
    inventory: int = 0
    installed: int = 0
    sat_done: int = 0
    revenue_collected: int = 0

    class Config:
        from_attributes = True


class MeterStageFunnelComparisonItem(BaseModel):
    label: str
    inventory: int = 0
    installed: int = 0
    sat_done: int = 0
    revenue_collected: int = 0

    class Config:
        from_attributes = True


class MeterStageFunnelSummaryOut(BaseModel):
    inventory: int
    installed: int
    sat_done: int
    revenue_collected: int
    category_breakdown: Dict[str, Any]  # { "CONSUMER": { "total": FunnelMetricItem, "1PH": FunnelMetricItem, ... }, "FEEDER": {...}, "DT": {...} }
    comparison: List[MeterStageFunnelComparisonItem]

    class Config:
        from_attributes = True


class MIvsSATvsInvoiceSummaryOut(BaseModel):
    total_mi: int = Field(..., description="Total MI count")
    total_sat: int = Field(..., description="Total SAT count")
    total_lumpsum_invoice: int = Field(..., description="Total lumpsum invoice count")
    total_pmpm_invoice: int = Field(..., description="Total pmpm invoice count")
    category_breakdown: Dict[str, Any] = Field(default_factory=dict)
    period_breakdown: Dict[str, Any] = Field(default_factory=dict)
    comparison: List[Dict[str, Any]] = Field(default_factory=list)


class RevenueRealizedSummaryOut(BaseModel):
    total_lumpsum_invoice: int = Field(..., description="Total lumpsum invoice count")
    total_pmpm_invoice: int = Field(..., description="Total pmpm invoice count")
    total_lumpsum_collection: int = Field(..., description="Total lumpsum collection count")
    total_pmpm_collection: int = Field(..., description="Total pmpm collection count")
    category_breakdown: Dict[str, Any] = Field(default_factory=dict)
    period_breakdown: Dict[str, Any] = Field(default_factory=dict)
    comparison: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Per-group revenue metrics (label + counts)",
    )


class RevenueAgeingSummaryOut(BaseModel):
    category_breakdown: Dict[str, Any] = Field(default_factory=dict)
    period_breakdown: Dict[str, Any] = Field(default_factory=dict)
    comparison: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Per-cluster ageing buckets (label + age_0_30…age_90_plus + total_pending)",
    )


class DefectiveMetersTrendPoint(BaseModel):
    period_value: str
    CONSUMER: int = 0
    FEEDER: int = 0
    DT: int = 0
    burnt: int = 0
    faulty: int = 0
    others: int = 0

class DefectiveMetersComparisonItem(BaseModel):
    label: str
    CONSUMER: int = 0
    FEEDER: int = 0
    DT: int = 0
    burnt: int = 0
    faulty: int = 0
    others: int = 0
    total_defective: int = 0

class DefectiveMetersSummaryOut(BaseModel):
    total_defective: int = Field(..., description="Total defective meter count")
    total_burnt: int = Field(..., description="Total burnt meter count")
    total_faulty: int = Field(..., description="Total faulty meter count")
    total_others: int = Field(..., description="Total others meter count")
    category_breakdown: Dict[str, Any] = Field(default_factory=dict)
    trend: List[DefectiveMetersTrendPoint] = Field(default_factory=list)
    comparison: List[DefectiveMetersComparisonItem] = Field(default_factory=list)



# ── O&M Schemas ──────────────────────────────────────────────────────────

class OMDimensionBase(BaseModel):
    project: Optional[str] = None
    discom: Optional[str] = None
    zone: Optional[str] = None
    circle: Optional[str] = None
    division: Optional[str] = None
    subdivision: Optional[str] = None
    substation: Optional[str] = None
    feeder: Optional[str] = None
    dtr: Optional[str] = None
    meter_category: Optional[str] = None  # Consumer | Feeder | DTR

    class Config:
        from_attributes = True


class OMProductivityTeamOut(OMDimensionBase):
    technician: Optional[str] = None
    agency: Optional[str] = None
    period_type: Optional[str] = None
    period_value: Optional[str] = None
    closed_tickets: Optional[int] = None


class OMTeamProductivitySummary(BaseModel):
    total_closed_tickets: int = 0
    total_active_technicians: int = 0
    productivity_per_technician_per_day: float = 0.0

class OMTeamProductivityInsights(BaseModel):
    top_performing_technician: Dict[str, Any] = Field(default_factory=dict)
    lowest_performing_technician: Dict[str, Any] = Field(default_factory=dict)

class OMTeamProductivityTrendPoint(BaseModel):
    date: str
    total_closed_tickets: int = 0
    active_technicians: int = 0
    productivity_per_technician_per_day: float = 0.0

class OMTeamProductivityComparisonItem(BaseModel):
    label: str
    total_closed_tickets: int = 0
    active_technicians: int = 0
    productivity_per_technician_per_day: float = 0.0

class OMTeamProductivityDashboardOut(BaseModel):
    summary: OMTeamProductivitySummary
    insights: OMTeamProductivityInsights
    trend: List[OMTeamProductivityTrendPoint] = Field(default_factory=list)
    comparison: List[OMTeamProductivityComparisonItem] = Field(default_factory=list)
    category_breakdown: Dict[str, Any] = Field(default_factory=dict)


class OMProductivityTrendOut(OMDimensionBase):
    closed_month: Optional[str] = None
    total_closed_tickets: Optional[int] = None


class OMProductivityTrendSummary(BaseModel):
    total_closed_tickets: int = 0
    total_active_months: int = 0
    avg_monthly_productivity_per_technician_per_day: float = 0.0

class OMProductivityTrendPoint(BaseModel):
    month: str
    total_closed_tickets: int = 0
    active_days: int = 0
    avg_active_technicians: float = 0.0
    productivity_per_technician_per_day: float = 0.0

class OMProductivityTrendComparisonItem(BaseModel):
    label: str
    productivity_per_technician_per_day: float = 0.0

class OMProductivityTrendDashboardOut(BaseModel):
    summary: OMProductivityTrendSummary
    trend: List[OMProductivityTrendPoint] = Field(default_factory=list)
    comparison: List[OMProductivityTrendComparisonItem] = Field(default_factory=list)
    category_breakdown: Dict[str, Any] = Field(default_factory=dict)


class OMOpenAgeingOut(OMDimensionBase):
    ticket_id: Optional[str] = None
    created_date: Optional[datetime] = None
    ageing_days: Optional[float] = None
    technician: Optional[str] = None
    agency: Optional[str] = None

class OMOpenAgeingBucketBreakdown(BaseModel):
    total: int = 0
    auto_ticketing: int = 0
    helpdesk_1912: int = Field(0, alias="1912_helpdesk")
    others: int = 0

class OMOpenAgeingBuckets(BaseModel):
    age_less_than_3_days: OMOpenAgeingBucketBreakdown = Field(default_factory=OMOpenAgeingBucketBreakdown)
    age_less_than_7_days: OMOpenAgeingBucketBreakdown = Field(default_factory=OMOpenAgeingBucketBreakdown)
    age_less_than_15_days: OMOpenAgeingBucketBreakdown = Field(default_factory=OMOpenAgeingBucketBreakdown)
    age_less_than_30_days: OMOpenAgeingBucketBreakdown = Field(default_factory=OMOpenAgeingBucketBreakdown)
    age_less_than_3_months: OMOpenAgeingBucketBreakdown = Field(default_factory=OMOpenAgeingBucketBreakdown)
    age_less_than_6_months: OMOpenAgeingBucketBreakdown = Field(default_factory=OMOpenAgeingBucketBreakdown)
    age_6_months_and_above: OMOpenAgeingBucketBreakdown = Field(default_factory=OMOpenAgeingBucketBreakdown)

class OMOpenAgeingSummary(BaseModel):
    total_open: int = 0
    auto_ticketing: int = 0
    helpdesk_1912: int = Field(0, alias="1912_helpdesk")
    others: int = 0
    age_buckets: OMOpenAgeingBuckets = Field(default_factory=OMOpenAgeingBuckets)

class OMOpenAgeingTrendPoint(BaseModel):
    period_value: str
    total_open: int = 0
    auto_ticketing: int = 0
    helpdesk_1912: int = Field(0, alias="1912_helpdesk")
    others: int = 0

class OMOpenAgeingComparisonItem(BaseModel):
    label: str
    total_open: int = 0
    auto_ticketing: int = 0
    helpdesk_1912: int = Field(0, alias="1912_helpdesk")
    others: int = 0
    age_buckets: OMOpenAgeingBuckets = Field(default_factory=OMOpenAgeingBuckets)

class OMOpenAgeingCategoryBreakdown(OMOpenAgeingSummary):
    pass

class OMOpenAgeingDashboardOut(BaseModel):
    total_open: int = Field(..., description="Overall total open tickets")
    summary: OMOpenAgeingSummary
    trend: List[OMOpenAgeingTrendPoint] = Field(default_factory=list)
    comparison: List[OMOpenAgeingComparisonItem] = Field(default_factory=list)
    category_breakdown: Dict[str, OMOpenAgeingCategoryBreakdown] = Field(default_factory=dict)



class OMAvgClosureTimeOut(OMDimensionBase):
    period_type: Optional[str] = None
    period_value_created: Optional[str] = None
    period_value_closed: Optional[str] = None
    avg_resolution_days: Optional[float] = None


class OMAvgClosureTimeSummary(BaseModel):
    total_closed_tickets: int = 0
    avg_resolution_days: float = 0.0


class OMAvgClosureTimeTrendPoint(BaseModel):
    period_value: str
    total_closed_tickets: int = 0
    avg_resolution_days: float = 0.0


class OMAvgClosureTimeComparisonItem(BaseModel):
    label: str
    total_closed_tickets: int = 0
    avg_resolution_days: float = 0.0


class OMAvgClosureTimeDashboardOut(BaseModel):
    summary: OMAvgClosureTimeSummary
    trend: List[OMAvgClosureTimeTrendPoint] = Field(default_factory=list)
    comparison: List[OMAvgClosureTimeComparisonItem] = Field(default_factory=list)
    category_breakdown: Dict[str, Any] = Field(default_factory=dict)


class OMClosedAnalysisOut(OMDimensionBase):
    complaint_type: Optional[str] = None
    complaint_category: Optional[str] = None
    period_type: Optional[str] = None
    period_value: Optional[str] = None
    closed_tickets: Optional[int] = None
