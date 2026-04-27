from fastapi import APIRouter, Depends, Query
from typing import Optional, List, Dict, Any

from infrastructure.database.setup import get_session
from adapters.repository.sqlalchemy_om_repo import SQLAlchemyOMRepository
from usecases.om.om_usecase import OMUseCase
from adapters.api.schemas import (
    OMOpenAgeingOut,
    OMAvgClosureTimeOut, OMClosedAnalysisOut, OMTeamProductivityDashboardOut,
    OMProductivityTrendDashboardOut, OMOpenAgeingDashboardOut,
    OMAvgClosureTimeDashboardOut
)

router = APIRouter(prefix="/api/om", tags=["O&M KPIs"])

def get_om_usecase():
    session = get_session()
    try:
        repo = SQLAlchemyOMRepository(session)
        yield OMUseCase(repo)
    finally:
        session.close()

@router.get("/productivity-team/dashboard",
            response_model=OMTeamProductivityDashboardOut,
            summary="O&M Team Productivity Dashboard")
def get_productivity_team_dashboard(
    duration: Optional[str] = Query("daily"),
    level: Optional[str] = Query("discom"),
    project: Optional[str] = Query("all"),
    category: Optional[str] = Query("total"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    feeder: Optional[str] = None,
    dtr: Optional[str] = None,
    om_usecase: OMUseCase = Depends(get_om_usecase),
):
    filters = locals()
    filters.pop("om_usecase")
    return om_usecase.get_productivity_team_dashboard(filters)

@router.get("/productivity-trend/dashboard",
            response_model=OMProductivityTrendDashboardOut,
            summary="O&M Productivity Trend Dashboard")
def get_productivity_trend_dashboard(
    duration: Optional[str] = Query("monthly"),
    level: Optional[str] = Query("discom"),
    project: Optional[str] = Query("all"),
    category: Optional[str] = Query("total"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    feeder: Optional[str] = None,
    dtr: Optional[str] = None,
    om_usecase: OMUseCase = Depends(get_om_usecase),
):
    filters = locals()
    filters.pop("om_usecase")
    return om_usecase.get_productivity_trend_dashboard(filters)

@router.get("/open-ageing", response_model=List[OMOpenAgeingOut], summary="Get O&M Open Ticket Ageing")
def get_open_ageing(
    discom: Optional[str] = None, zone: Optional[str] = None, circle: Optional[str] = None,
    division: Optional[str] = None, subdivision: Optional[str] = None,
    feeder: Optional[str] = None, dtr: Optional[str] = None,
    project: Optional[str] = None, meter_category: Optional[str] = None,
    om_category: Optional[str] = Query(None, description="Legacy alias for meter_category"),
    limit: int = Query(1000, le=50000), offset: int = Query(0, ge=0),
    start_date: Optional[str] = None, end_date: Optional[str] = None,
    om_usecase: OMUseCase = Depends(get_om_usecase),
):
    filters = locals()
    filters.pop("om_usecase")
    if filters.get("om_category") and not filters.get("meter_category"):
        filters["meter_category"] = filters.pop("om_category")
    return om_usecase.get_open_ageing(filters, limit, offset)

@router.get("/open-ageing/dashboard",
            response_model=OMOpenAgeingDashboardOut,
            summary="O&M Open Ticket Ageing Dashboard")
def get_open_ageing_dashboard(
    duration: Optional[str] = Query("daily"),
    level: Optional[str] = Query("discom"),
    project: Optional[str] = Query("all"),
    category: Optional[str] = Query("total"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    feeder: Optional[str] = None,
    dtr: Optional[str] = None,
    om_usecase: OMUseCase = Depends(get_om_usecase),
):
    filters = locals()
    filters.pop("om_usecase")
    return om_usecase.get_open_ageing_dashboard(filters)

@router.get("/avg-closure-time", response_model=List[OMAvgClosureTimeOut], summary="Get O&M Average Ticket Closure Time")
def get_avg_closure_time(
    discom: Optional[str] = None, zone: Optional[str] = None, circle: Optional[str] = None,
    division: Optional[str] = None, subdivision: Optional[str] = None,
    feeder: Optional[str] = None, dtr: Optional[str] = None,
    project: Optional[str] = None, meter_category: Optional[str] = None,
    om_category: Optional[str] = Query(None, description="Legacy alias for meter_category"),
    period: Optional[str] = Query(None, description="daily | weekly | monthly"),
    limit: int = Query(1000, le=50000), offset: int = Query(0, ge=0),
    start_date: Optional[str] = None, end_date: Optional[str] = None,
    om_usecase: OMUseCase = Depends(get_om_usecase),
):
    filters = locals()
    filters.pop("om_usecase")
    if filters.get("om_category") and not filters.get("meter_category"):
        filters["meter_category"] = filters.pop("om_category")
    return om_usecase.get_avg_closure_time(filters, limit, offset)

@router.get("/avg-closure-time/dashboard",
            response_model=OMAvgClosureTimeDashboardOut,
            summary="O&M Average Ticket Closure Time Dashboard")
def get_avg_closure_time_dashboard(
    duration: Optional[str] = Query("monthly"),
    level: Optional[str] = Query("discom"),
    project: Optional[str] = Query("all"),
    category: Optional[str] = Query("total"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    feeder: Optional[str] = None,
    dtr: Optional[str] = None,
    om_usecase: OMUseCase = Depends(get_om_usecase),
):
    filters = locals()
    filters.pop("om_usecase")
    return om_usecase.get_avg_closure_time_dashboard(filters)

@router.get("/closed-analysis", response_model=List[OMClosedAnalysisOut], summary="Get O&M Closed Ticket Analysis by Type/Category")
def get_closed_analysis(
    discom: Optional[str] = None, zone: Optional[str] = None, circle: Optional[str] = None,
    division: Optional[str] = None, subdivision: Optional[str] = None,
    feeder: Optional[str] = None, dtr: Optional[str] = None,
    project: Optional[str] = None, meter_category: Optional[str] = None,
    om_category: Optional[str] = Query(None, description="Legacy alias for meter_category"),
    period: Optional[str] = Query(None, description="daily | weekly | monthly"),
    limit: int = Query(1000, le=50000), offset: int = Query(0, ge=0),
    start_date: Optional[str] = None, end_date: Optional[str] = None,
    om_usecase: OMUseCase = Depends(get_om_usecase),
):
    filters = locals()
    filters.pop("om_usecase")
    if filters.get("om_category") and not filters.get("meter_category"):
        filters["meter_category"] = filters.pop("om_category")
    return om_usecase.get_closed_analysis(filters, limit, offset)
