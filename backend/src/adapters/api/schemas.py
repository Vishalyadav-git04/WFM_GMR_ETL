"""
Pydantic response schemas for API endpoints.
"""

from typing import Optional, Dict, List, Any

from pydantic import BaseModel, Field
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
    CONSUMER: Optional[int] = Field(None, description="MI progress count for CONSUMER category")
    FEEDER: Optional[int] = Field(None, description="MI progress count for FEEDER category")
    DT: Optional[int] = Field(None, description="MI progress count for DT category")
    total: Optional[int] = Field(None, description="Total MI progress count for the period")

    model_config = {"extra": "allow"}


class MIProgressDashboardComparisonItem(BaseModel):
    label: str = Field(..., description="Bar label (project or project|level label)")
    CONSUMER: Optional[int] = Field(None, description="MI progress count for CONSUMER category")
    FEEDER: Optional[int] = Field(None, description="MI progress count for FEEDER category")
    DT: Optional[int] = Field(None, description="MI progress count for DT category")
    total: Optional[int] = Field(None, description="Total MI progress count (sum of all categories)")

    model_config = {"extra": "allow"}

class MIProgressDashboardOut(BaseModel):
    total_progress: int = Field(..., description="Cumulative MI progress total for the selected filters")
    trend: List[MIProgressDashboardTrendPoint] = Field(default_factory=list, description="Trend series for MI Progress chart")
    comparison: List[MIProgressDashboardComparisonItem] = Field(default_factory=list, description="Comparison-by-cluster bar chart data")


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


class MIProductivityTrendSummary(BaseModel):
    total_installations: int = 0
    total_active_months: int = 0
    productivity_per_technician_per_day: float = 0.0


class MIProductivityTrendPoint(BaseModel):
    month: str
    total_installations: int = 0
    active_days: int = 0
    avg_active_technicians: float = 0.0
    productivity_per_technician_per_day: float = 0.0


class MIProductivityTrendComparisonItem(BaseModel):
    label: str
    total_installations: int = 0
    active_days: int = 0
    avg_active_technicians: float = 0.0
    productivity_per_technician_per_day: float = 0.0


class MIProductivityTrendDashboardOut(BaseModel):
    summary: MIProductivityTrendSummary
    trend: List[MIProductivityTrendPoint] = Field(default_factory=list)
    comparison: List[MIProductivityTrendComparisonItem] = Field(default_factory=list)
    category_breakdown: Dict[str, Any] = Field(default_factory=dict)


class InventoryUtilizationSummaryOut(BaseModel):
    total_inventory: int = Field(..., description="Total stock count")
    total_installed: int = Field(..., description="Total installed count")
    utilization_rate_pct: float = Field(..., description="Overall utilization percentage")
    remaining_stock: int = Field(..., description="Overall remaining stock")
    period_breakdown: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Trend rows with category-aware nested objects; when category is consumer or total, "
            "each nested bucket includes inventory, installed, and utilization_rate_pct"
        ),
    )
    comparison: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Per-cluster bars; when category is consumer or total, each nested bucket includes "
            "inventory, installed, and utilization_rate_pct"
        ),
    )


class PaceVsStockSummaryOut(InventoryUtilizationSummaryOut):
    """Same outer shape as Inventory Utilization; row-level pace uses remaining_stock vs utilization_rate_pct."""

    period_breakdown: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Trend rows; when category is consumer or total, each nested bucket includes "
            "inventory, installed, and remaining_stock (not utilization_rate_pct)"
        ),
    )
    comparison: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Per-cluster bars; when category is consumer or total, nested buckets include remaining_stock"
        ),
    )


class StockAgeingDashboardOut(BaseModel):
    total_stock: int = Field(..., description="Overall total stock")
    summary: Dict[str, Any] = Field(default_factory=dict)
    comparison: List[Dict[str, Any]] = Field(default_factory=list)



class MIvsSATSummaryOut(BaseModel):
    total_mi: int = Field(..., description="Cumulative Total MI")
    total_sat: int = Field(..., description="Cumulative Total SAT")
    sat_progress_pct: float = Field(..., description="Overall SAT progress percentage")
    summary: Dict[str, Any] = Field(default_factory=dict, description="SAT stage breakdowns with category-aware sub-keys")
    comparison: List[Dict[str, Any]] = Field(default_factory=list, description="Comparison-by-cluster with SAT stage breakdowns")


class NonSATAgeingDashboardOut(BaseModel):
    total_non_sat: int = Field(..., description="Overall total non sat count")
    summary: Dict[str, Any] = Field(default_factory=dict)
    comparison: List[Dict[str, Any]] = Field(default_factory=list)


class MeterJourneyDashboardOut(BaseModel):
    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Cohort-wide weighted averages; nested by meter-type when category=consumer",
    )
    comparison: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="One row per cluster; nested by meter-type when category=consumer",
    )


class MeterStageFunnelSummaryOut(BaseModel):
    """KPI 10 — Meter Funnel Summary ("Pending PMPM Collection")."""

    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Pending-PMPM-collection counts: inventory, installed, sat_done, "
            "invoice_done. Each is a flat int when category=feeder|dt; nested by "
            "CONSUMER/FEEDER/DT/total when category=total; nested by "
            "1PH-Consumer_meter / 3PH-Consumer_meter / LTCT-Consumer_meter / "
            "HTCT-Consumer_meter / total when category=consumer."
        ),
    )
    comparison: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "One row per level group; each row has `label` plus the same 4 "
            "fields with the same nesting rules as `summary`."
        ),
    )


class MIvsSATvsInvoiceSummaryOut(BaseModel):
    summary: Dict[str, Any] = Field(default_factory=dict)
    comparison: List[Dict[str, Any]] = Field(default_factory=list)


class RevenueRealizedSummaryOut(BaseModel):
    """KPI 12 — Revenue Realized (KPI-10-style ``summary`` + ``comparison``)."""

    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Revenue totals: total_lumpsum_invoice, total_pmpm_invoice, "
            "total_lumpsum_collection, total_pmpm_collection. Each is a flat int when "
            "category=feeder|dt; nested by CONSUMER/FEEDER/DT/total when category=total; "
            "nested by 1PH-Consumer_meter / 3PH-Consumer_meter / LTCT-Consumer_meter / "
            "HTCT-Consumer_meter / total when category=consumer."
        ),
    )
    comparison: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "One row per level group; each row has `label` plus the same four fields "
            "with the same nesting rules as `summary`."
        ),
    )


class RevenueAgeingSummaryOut(BaseModel):
    """KPI 13 — same top-level shape as KPI 6 Stock Ageing: ``summary`` + ``comparison``."""

    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Ageing buckets + total_pending. When category=consumer: each age_* is a dict "
            "1PH-Consumer_meter / 3PH-Consumer_meter / LTCT-Consumer_meter / "
            "HTCT-Consumer_meter / total. When category=total (or default): each age_* "
            "is CONSUMER / FEEDER / DT / total. When category=feeder|dt: each age_* is a flat int."
        ),
    )
    comparison: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Per-cluster rows with label + same nesting rules as summary for age_* "
            "+ total_pending."
        ),
    )


class DefectiveMetersSummaryOut(BaseModel):
    summary: Dict[str, Any] = Field(default_factory=dict)
    period_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    comparison: List[Dict[str, Any]] = Field(default_factory=list)



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
    age_less_than_3_days: OMOpenAgeingBucketBreakdown = Field(default_factory=lambda: OMOpenAgeingBucketBreakdown.model_validate({}))
    age_less_than_7_days: OMOpenAgeingBucketBreakdown = Field(default_factory=lambda: OMOpenAgeingBucketBreakdown.model_validate({}))
    age_less_than_15_days: OMOpenAgeingBucketBreakdown = Field(default_factory=lambda: OMOpenAgeingBucketBreakdown.model_validate({}))
    age_less_than_30_days: OMOpenAgeingBucketBreakdown = Field(default_factory=lambda: OMOpenAgeingBucketBreakdown.model_validate({}))
    age_less_than_3_months: OMOpenAgeingBucketBreakdown = Field(default_factory=lambda: OMOpenAgeingBucketBreakdown.model_validate({}))
    age_less_than_6_months: OMOpenAgeingBucketBreakdown = Field(default_factory=lambda: OMOpenAgeingBucketBreakdown.model_validate({}))
    age_6_months_and_above: OMOpenAgeingBucketBreakdown = Field(default_factory=lambda: OMOpenAgeingBucketBreakdown.model_validate({}))

class OMOpenAgeingSummary(BaseModel):
    total: int = 0
    auto_ticketing: int = 0
    helpdesk_1912: int = Field(0, alias="1912_helpdesk")
    others: int = 0
    age_buckets: OMOpenAgeingBuckets = Field(default_factory=lambda: OMOpenAgeingBuckets.model_validate({}))

class OMOpenAgeingTrendPoint(BaseModel):
    period_value: str
    total: int = 0
    auto_ticketing: int = 0
    helpdesk_1912: int = Field(0, alias="1912_helpdesk")
    others: int = 0

class OMOpenAgeingComparisonItem(BaseModel):
    label: str
    total: int = 0
    auto_ticketing: int = 0
    helpdesk_1912: int = Field(0, alias="1912_helpdesk")
    others: int = 0
    age_buckets: OMOpenAgeingBuckets = Field(default_factory=lambda: OMOpenAgeingBuckets.model_validate({}))

class OMOpenAgeingCategoryBreakdown(OMOpenAgeingSummary):
    pass

class OMOpenAgeingDashboardOut(BaseModel):
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


class OMClosedAnalysisDashboardSummary(BaseModel):
    auto_ticketing: int = 0
    helpdesk_1912: int = Field(0, alias="1912_helpdesk")
    others: int = 0


class OMClosedAnalysisDashboardTrendPoint(BaseModel):
    period_value: str
    auto_ticketing: int = 0
    helpdesk_1912: int = Field(0, alias="1912_helpdesk")
    others: int = 0


class OMClosedAnalysisDashboardComparisonItem(BaseModel):
    label: str
    auto_ticketing: int = 0
    helpdesk_1912: int = Field(0, alias="1912_helpdesk")
    others: int = 0


class OMClosedAnalysisDashboardCategoryBreakdown(OMClosedAnalysisDashboardSummary):
    pass


class OMClosedAnalysisDashboardOut(BaseModel):
    summary: OMClosedAnalysisDashboardSummary
    trend: List[OMClosedAnalysisDashboardTrendPoint] = Field(default_factory=list)
    comparison: List[OMClosedAnalysisDashboardComparisonItem] = Field(default_factory=list)
    category_breakdown: Dict[str, OMClosedAnalysisDashboardCategoryBreakdown] = Field(default_factory=dict)
