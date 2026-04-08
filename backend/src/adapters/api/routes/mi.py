from fastapi import APIRouter, Depends, Query
from typing import Optional, List, Dict, Any

from infrastructure.database.setup import get_session
from adapters.repository.sqlalchemy_mi_repo import SQLAlchemyMIRepository
from usecases.mi.mi_usecase import MIUseCase
from adapters.api.schemas import (
    MIProgressOut, MIProgressSummaryOut, MIProductivityOut, 
    MonthlyProductivityOut, MonthlyProductivitySummaryOut,
    InventoryUtilizationOut, InventoryUtilizationSummaryOut,
    StockAgeingOut, MIvsSATOut, MIvsSATSummaryOut,
    MINonSATAgeingOut, MeterJourneyOut, MeterStageOut,
)

router = APIRouter(prefix="/api/mi", tags=["MI KPIs"])

def get_mi_usecase():
    session = get_session()
    try:
        repo = SQLAlchemyMIRepository(session)
        yield MIUseCase(repo)
    finally:
        session.close()

@router.get("/progress", response_model=List[MIProgressOut], summary="Get MI Progress Trend")
def get_mi_progress(
    period: Optional[str] = Query(None, description="Filter by period: daily, weekly, or monthly"),
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
    limit: int = Query(1000, le=50000),
    offset: int = Query(0, ge=0),
    project: Optional[str] = None,
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    return mi_usecase.get_mi_progress(filters, limit, offset)

@router.get("/progress/summary", response_model=MIProgressSummaryOut, summary="Get MI Progress Summary")
def get_mi_progress_summary(
    period: Optional[str] = Query(None, description="Filter by period: daily, weekly, or monthly"),
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
    result = mi_usecase.get_progress_summary(filters)
    return MIProgressSummaryOut(**result)

@router.get("/productivity", response_model=List[MIProductivityOut], summary="Get MI Productivity (Per Technician)")
def get_mi_productivity(
    period: Optional[str] = Query(None, description="Filter by period: daily, weekly, or monthly"),
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
    technician: Optional[str] = None,
    limit: int = Query(1000, le=50000),
    offset: int = Query(0, ge=0),
    project: Optional[str] = None,
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    return mi_usecase.get_mi_productivity(filters, limit, offset)

@router.get("/monthly-productivity", response_model=List[MonthlyProductivityOut], summary="Get Monthly Productivity List")
def get_monthly_productivity(
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
    period_value: Optional[str] = Query(None, description="Month in YYYY-MM format"),
    limit: int = Query(1000, le=50000),
    offset: int = Query(0, ge=0),
    project: Optional[str] = None,
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    return mi_usecase.get_monthly_productivity(filters, limit, offset)

@router.get("/monthly-productivity/summary", response_model=MonthlyProductivitySummaryOut, summary="Get Monthly Installations Total")
def get_monthly_productivity_summary(
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
    period_value: Optional[str] = Query(None, description="Month in YYYY-MM format"),
    project: Optional[str] = None,
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    result = mi_usecase.get_monthly_productivity_summary(filters)
    return MonthlyProductivitySummaryOut(**result)

@router.get("/inventory-utilization", response_model=List[InventoryUtilizationOut], summary="Get Inventory Utilization Trend")
def get_inventory_utilization(
    period: Optional[str] = Query(None, description="Filter by period: daily, weekly, or monthly"),
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
    limit: int = Query(1000, le=50000),
    offset: int = Query(0, ge=0),
    project: Optional[str] = None,
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    return mi_usecase.get_inventory_utilization(filters, limit, offset)

@router.get("/inventory-utilization/summary", response_model=InventoryUtilizationSummaryOut, summary="Get Inventory Utilization Aggregated Summary")
def get_inventory_utilization_summary(
    period: Optional[str] = Query(None, description="Filter by period: daily, weekly, or monthly"),
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

@router.get("/pace-vs-stock", response_model=List[InventoryUtilizationOut], summary="Get MI Pace vs Stock Trend")
def get_pace_vs_stock(
    period: Optional[str] = Query(None, description="Filter by period: daily, weekly, or monthly"),
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    project: Optional[str] = None,
    limit: int = Query(1000),
    offset: int = Query(0),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    return mi_usecase.get_pace_vs_stock(filters, limit, offset)

@router.get("/pace-vs-stock/summary", response_model=InventoryUtilizationSummaryOut, summary="Get MI Pace vs Stock Aggregated Summary")
def get_pace_vs_stock_summary(
    filters: Dict[str, Any] = Depends(lambda: {}), # Simplified for summary
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    return mi_usecase.get_pace_vs_stock_summary(filters)

@router.get("/stock-ageing", response_model=List[StockAgeingOut], summary="Get Unutilized Stock Ageing Detail")
def get_stock_ageing(
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    return mi_usecase.get_stock_ageing(limit, offset)

@router.get("/mi-vs-sat", response_model=List[MIvsSATOut], summary="Get MI vs SAT List")
def get_mi_vs_sat(
    project: Optional[str] = None,
    discom: Optional[str] = None,
    limit: int = Query(1000),
    offset: int = Query(0),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    return mi_usecase.get_mi_vs_sat(filters, limit, offset)

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
    meter_category: Optional[str] = None,
    project: Optional[str] = None,
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    result = mi_usecase.get_mi_vs_sat_summary(filters)
    return MIvsSATSummaryOut(**result)

@router.get("/non-sat-ageing", response_model=List[MINonSATAgeingOut], summary="Get Non-SAT Ageing List")
def get_non_sat_ageing(
    project: Optional[str] = None,
    limit: int = Query(1000),
    offset: int = Query(0),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    return mi_usecase.get_non_sat_ageing(filters, limit, offset)

@router.get("/meter-journey", response_model=List[MeterJourneyOut], summary="Get Meter Journey Avg Time")
def get_meter_journey(
    project: Optional[str] = None,
    limit: int = Query(100),
    offset: int = Query(0),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    return mi_usecase.get_meter_journey(filters, limit, offset)

@router.get("/meter-stage", response_model=List[MeterStageOut], summary="Get Meter Current Stage Distribution")
def get_meter_stage(
    project: Optional[str] = None,
    limit: int = Query(100),
    offset: int = Query(0),
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    return mi_usecase.get_meter_stage(filters, limit, offset)

@router.get("/command-center/{region}", summary="Get Command Center Dashboard Snapshot")
def get_command_center_dashboard(
    region: str,
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
):
    """
    Returns the comprehensive Command Center Dashboard data structure for a given region (kashi, agra, triveni).
    """
    return mi_usecase.get_command_center_dashboard(region)
