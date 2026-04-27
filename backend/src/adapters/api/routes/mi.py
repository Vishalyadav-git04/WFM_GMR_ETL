from fastapi import APIRouter, Depends, Query
from typing import Optional, Dict, Any

from infrastructure.database.setup import get_session
from adapters.repository.sqlalchemy_mi_repo import SQLAlchemyMIRepository
from usecases.mi.mi_usecase import MIUseCase
from adapters.api.schemas import (
    InventoryUtilizationSummaryOut, PaceVsStockSummaryOut,
    MIvsSATSummaryOut, StockAgeingDashboardOut,
    NonSATAgeingDashboardOut, MeterJourneyDashboardOut,
    MeterStageFunnelSummaryOut,
    MIvsSATvsInvoiceSummaryOut, RevenueRealizedSummaryOut, RevenueAgeingSummaryOut,
    DefectiveMetersSummaryOut,
    MIProgressDashboardOut,
    MITeamProductivityDashboardOut,
    MIProductivityTrendDashboardOut,
)

router = APIRouter(prefix="/api/mi", tags=["MI KPIs"])

def get_mi_usecase():
    session = get_session()
    try:
        repo = SQLAlchemyMIRepository(session)
        yield MIUseCase(repo)
    finally:
        session.close()



@router.get("/progress/dashboard", response_model=MIProgressDashboardOut, summary="Get MI Progress Dashboard (Trend + Comparison)")
def get_mi_progress_dashboard(
    duration: Optional[str] = Query(None, description="Duration: daily, weekly, or monthly"),
    category: Optional[str] = Query(None, description="Category: total, consumer, feeder, dt"),
    level: Optional[str] = Query(None, description="Level: discom, zone, circle, division, subdivision"),
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    substation: Optional[str] = None,
    feeder: Optional[str] = None,
    dtr: Optional[str] = None,
    new_meter_type: Optional[str] = None,
    project: Optional[str] = Query(None, description="Project: all, kashi, agra, triveni"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    result = mi_usecase.get_progress_dashboard(filters)
    return MIProgressDashboardOut(**result)

@router.get("/productivity/team/dashboard",
            response_model=MITeamProductivityDashboardOut,
            summary="MI Technician Productivity Dashboard (Trend + Comparison)")
def get_mi_productivity_team_dashboard(
    duration: Optional[str] = Query("daily", description="Aggregation granularity: daily / weekly / monthly"),
    level: Optional[str] = Query("discom", description="Cluster level for comparison: project, discom, zone, circle, division, subdivision"),
    project: Optional[str] = Query("all", description="Project filter: all / AGRA / KASHI / TRIVENI"),
    category: Optional[str] = Query("total", description="Meter category: total / consumer / feeder / dt"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    substation: Optional[str] = None,
    feeder: Optional[str] = None,
    dtr: Optional[str] = None,
    new_meter_type: Optional[str] = None,
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    result = mi_usecase.get_productivity_team_dashboard(filters)
    return MITeamProductivityDashboardOut(**result)


@router.get(
    "/productivity/trend/dashboard",
    response_model=MIProductivityTrendDashboardOut,
    summary="MI Technician Productivity Trend Dashboard (Monthly by default)",
)
def get_mi_productivity_trend_dashboard(
    duration: Optional[str] = Query(
        "monthly",
        description="Aggregation granularity: daily / weekly / monthly (default: monthly)",
    ),
    level: Optional[str] = Query(
        "discom",
        description="Cluster level for comparison: project, discom, zone, circle, division, subdivision",
    ),
    project: Optional[str] = Query("all", description="Project filter: all / AGRA / KASHI / TRIVENI"),
    category: Optional[str] = Query("total", description="Meter category: total / consumer / feeder / dt"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    substation: Optional[str] = None,
    feeder: Optional[str] = None,
    dtr: Optional[str] = None,
    new_meter_type: Optional[str] = None,
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    result = mi_usecase.get_productivity_trend_dashboard(filters)
    return MIProductivityTrendDashboardOut(**result)

@router.get("/inventory-utilization/summary", response_model=InventoryUtilizationSummaryOut, summary="Get Inventory Utilization Aggregated Summary")
def get_inventory_utilization_summary(
    duration: Optional[str] = Query("daily", description="Aggregation granularity: daily, weekly, or monthly"),
    level: Optional[str] = Query("discom", description="Hierarchy level for comparison grouping"),
    category: Optional[str] = Query("total", description="Optional meter category filter"),
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    substation: Optional[str] = None,
    feeder: Optional[str] = None,
    dtr: Optional[str] = None,
    new_meter_type: Optional[str] = None,
    meter_category: Optional[str] = None,
    project: Optional[str] = None,
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    result = mi_usecase.get_inventory_utilization_summary(filters)
    return InventoryUtilizationSummaryOut(**result)

@router.get("/pace-vs-stock/summary", response_model=PaceVsStockSummaryOut, summary="Get MI Pace vs Stock Aggregated Summary")
def get_pace_vs_stock_summary(
    duration: Optional[str] = Query("daily", description="Aggregation granularity: daily, weekly, or monthly"),
    level: Optional[str] = Query("discom", description="Hierarchy level for comparison grouping"),
    category: Optional[str] = Query("total", description="Optional meter category filter"),
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    substation: Optional[str] = None,
    feeder: Optional[str] = None,
    dtr: Optional[str] = None,
    new_meter_type: Optional[str] = None,
    meter_category: Optional[str] = None,
    project: Optional[str] = None,
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    filters["is_pace_vs_stock"] = True
    result = mi_usecase.get_pace_vs_stock_summary(filters)
    return PaceVsStockSummaryOut(**result)

@router.get("/stock-ageing/dashboard", response_model=StockAgeingDashboardOut, summary="Get Stock Ageing Dashboard")
def get_stock_ageing_dashboard(
    duration: Optional[str] = Query("monthly", description="monthly, weekly, daily"),
    level: Optional[str] = Query("discom", description="Hierarchy level for grouping"),
    project: Optional[str] = Query("all", description="all, kashi, agra, triveni"),
    start_date: Optional[str] = Query(None, description="Start date"),
    end_date: Optional[str] = Query(None, description="End date"),
    discom: Optional[str] = None, zone: Optional[str] = None,
    circle: Optional[str] = None, division: Optional[str] = None,
    subdivision: Optional[str] = None, substation: Optional[str] = None,
    feeder: Optional[str] = None, dtr: Optional[str] = None,
    new_meter_type: Optional[str] = None, meter_category: Optional[str] = None,
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    result = mi_usecase.get_stock_ageing_dashboard(filters)
    return StockAgeingDashboardOut(**result)

@router.get("/mi-vs-sat/summary", response_model=MIvsSATSummaryOut, summary="Get MI vs SAT Aggregated Summary")
def get_mi_vs_sat_summary(
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    substation: Optional[str] = None,
    feeder: Optional[str] = None,
    dtr: Optional[str] = None,
    new_meter_type: Optional[str] = None,
    duration: Optional[str] = Query(None, description="Aggregation granularity: daily, weekly, monthly"),
    category: Optional[str] = Query(None, description="Filter by meter category: consumer, feeder, dt"),
    project: Optional[str] = Query(None, description="Project filter: all, kashi, agra, triveni"),
    level: Optional[str] = Query(None, description="Hierarchy level for comparison grouping: discom, zone, circle, division, subdivision"),
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    result = mi_usecase.get_mi_vs_sat_summary(filters)
    return MIvsSATSummaryOut(**result)

@router.get("/non-sat-ageing/dashboard", response_model=NonSATAgeingDashboardOut, summary="Get Non SAT Ageing Dashboard")
def get_non_sat_ageing_dashboard(
    duration: Optional[str] = Query("daily", description="monthly, weekly, daily"),
    category: Optional[str] = Query("total", description="total, consumer, feeder, dt"),
    level: Optional[str] = Query("discom", description="Hierarchy level for grouping"),
    project: Optional[str] = Query("all", description="all, kashi, agra, triveni"),
    start_date: Optional[str] = Query(None, description="Start date"),
    end_date: Optional[str] = Query(None, description="End date"),
    discom: Optional[str] = None, zone: Optional[str] = None,
    circle: Optional[str] = None, division: Optional[str] = None,
    subdivision: Optional[str] = None, substation: Optional[str] = None,
    feeder: Optional[str] = None, dtr: Optional[str] = None,
    new_meter_type: Optional[str] = None,
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    result = mi_usecase.get_non_sat_ageing_dashboard(filters)
    return NonSATAgeingDashboardOut(**result)

@router.get(
    "/meter-journey/dashboard",
    response_model=MeterJourneyDashboardOut,
    summary="Meter journey dashboard (pre-aggregated table + weighted roll-up + comparison)",
)
def get_meter_journey_dashboard(
    duration: str = Query(
        "daily",
        description="daily, weekly, or monthly — selects ``period_type`` on sql_meter_journey_avg_time",
    ),
    category: Optional[str] = Query(None, description="total, consumer, feeder, dt"),
    level: Optional[str] = Query(None, description="discom, zone, circle, division, subdivision, substation, feeder, dtr"),
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    substation: Optional[str] = None,
    feeder: Optional[str] = None,
    dtr: Optional[str] = None,
    new_meter_type: Optional[str] = None,
    meter_category: Optional[str] = None,
    project: Optional[str] = Query(None, description="Project: all, kashi, agra, triveni"),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD — filter on ``period_value`` as a date"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD — filter on ``period_value`` as a date"),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    result = mi_usecase.get_meter_journey_dashboard(filters)
    return MeterJourneyDashboardOut(**result)


@router.get(
    "/meter-stage",
    response_model=MeterStageFunnelSummaryOut,
    summary="Get Meter Funnel Summary (Inventory → Installed → SAT → Revenue Collected)",
    description="""
Returns pre-aggregated counts at four funnel stages:
- **inventory**: total meters available
- **installed**: meters with MI complete (`mi_date IS NOT NULL`) and a SAT number (`sat_no IS NOT NULL`)
- **sat_done**: meters with SAT date set (`sat_date IS NOT NULL`)
- **revenue_collected**: meters with PMPM collection date (`pmpm_collection_date IS NOT NULL`)

Results are grouped by geographic + type dimensions. 
- `category_breakdown` nests by meter_category (CONSUMER/FEEDER/DT) and meter_type.
- `comparison` groups by the selected `level` (discom/zone/circle/...) with optional `project=all` composite labels.
""",
)
def get_meter_stage(
    category: Optional[str] = Query(None, description="total, consumer, feeder, dt"),
    level: Optional[str] = Query(
        None,
        description="discom, zone, circle, division, subdivision, substation, feeder, dtr",
    ),
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    substation: Optional[str] = None,
    feeder: Optional[str] = None,
    dtr: Optional[str] = None,
    new_meter_type: Optional[str] = None,
    meter_category: Optional[str] = None,
    project: Optional[str] = Query(None, description="Project: all, AGRA, KASHI, TRIVENI"),
    start_date: Optional[str] = Query(None, description="Start date for filtering relevant date columns"),
    end_date: Optional[str] = Query(None, description="End date for filtering relevant date columns"),
    limit: int = Query(1000, le=50000, description="Ignored — present for backward compatibility"),
    offset: int = Query(0, ge=0, description="Ignored — present for backward compatibility"),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    # limit/offset not needed for summary grain; ignore
    result = mi_usecase.get_meter_stage_dashboard(filters, limit=0, offset=0)
    return MeterStageFunnelSummaryOut(**result)

@router.get("/command-center/{region}", summary="Get Command Center Dashboard Snapshot")
def get_command_center_dashboard(
    region: str,
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    """
    Returns the comprehensive Command Center Dashboard data structure for a given region (kashi, agra, triveni).
    """
    return mi_usecase.get_command_center_dashboard(region)


@router.get("/mi-vs-sat-vs-invoice/summary", response_model=MIvsSATvsInvoiceSummaryOut, summary="Get MI vs SAT vs Invoice Funnel Summary")
def get_mi_sat_invoice_summary(
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    substation: Optional[str] = None,
    feeder: Optional[str] = None,
    dtr: Optional[str] = None,
    new_meter_type: Optional[str] = None,
    meter_category: Optional[str] = None,
    category: Optional[str] = Query(None, description="Filter by meter category: consumer, feeder, dt"),
    project: Optional[str] = Query(None, description="Project filter: all, kashi, agra, triveni"),
    level: Optional[str] = Query(None, description="Hierarchy level for comparison grouping: discom, zone, circle, division, subdivision"),
    duration: Optional[str] = Query(None, description="Aggregation granularity: daily, weekly, monthly"),
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    result = mi_usecase.get_mi_sat_invoice_summary(filters)
    return MIvsSATvsInvoiceSummaryOut(**result)


@router.get("/revenue-realized/summary", response_model=RevenueRealizedSummaryOut, summary="Get Revenue Realized Summary")
def get_revenue_realized_summary(
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    substation: Optional[str] = None,
    feeder: Optional[str] = None,
    dtr: Optional[str] = None,
    new_meter_type: Optional[str] = None,
    meter_category: Optional[str] = None,
    project: Optional[str] = None,
    duration: Optional[str] = Query(None, description="Period granularity (daily, weekly, monthly)"),
    level: Optional[str] = Query(None, description="Grouping level for comparison (discom, zone, circle, division, subdivision, substation, feeder, dtr)"),
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    result = mi_usecase.get_revenue_realized_summary(filters)
    return RevenueRealizedSummaryOut(**result)


@router.get("/revenue-ageing/summary", response_model=RevenueAgeingSummaryOut, summary="Get Revenue Ageing (SAT to Collection) Summary")
def get_revenue_ageing_summary(
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    substation: Optional[str] = None,
    feeder: Optional[str] = None,
    dtr: Optional[str] = None,
    new_meter_type: Optional[str] = None,
    meter_category: Optional[str] = None,
    category: Optional[str] = Query(None, description="Optional: consumer, feeder, dt (alias for meter_category)"),
    project: Optional[str] = None,
    duration: Optional[str] = Query(
        "monthly",
        description="Must match sql_revenue_ageing.period_type: monthly (default), daily, weekly, as_on",
    ),
    level: Optional[str] = Query("discom", description="Comparison grouping: discom, zone, circle, division, subdivision"),
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    result = mi_usecase.get_revenue_ageing_summary(filters)
    return RevenueAgeingSummaryOut(**result)


@router.get("/defective-meters/summary", response_model=DefectiveMetersSummaryOut, summary="Get Defective Meters Summary")
def get_defective_meters_summary(
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    substation: Optional[str] = None,
    feeder: Optional[str] = None,
    dtr: Optional[str] = None,
    new_meter_type: Optional[str] = None,
    meter_category: Optional[str] = None,
    project: Optional[str] = Query(None, description="Project: all, agra, kashi, triveni"),
    level: Optional[str] = Query(None, description="Hierarchy level for comparison grouping: discom, zone, circle, division, subdivision"),
    duration: Optional[str] = Query(None, description="Aggregation granularity: daily, weekly, or monthly"),
    category: Optional[str] = Query(None, description="Filter by meter category: consumer, feeder, dt"),
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    result = mi_usecase.get_defective_meters_summary(filters)
    return DefectiveMetersSummaryOut(**result)
