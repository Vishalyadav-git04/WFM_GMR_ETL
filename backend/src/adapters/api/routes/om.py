from fastapi import APIRouter, Depends, Query
from typing import Optional, List, Dict, Any

from infrastructure.database.setup import get_session
from adapters.repository.sqlalchemy_om_repo import SQLAlchemyOMRepository
from usecases.om.om_usecase import OMUseCase
from adapters.api.schemas import (
    OMProductivityTeamOut, OMProductivityTrendOut, OMOpenAgeingOut,
    OMAvgClosureTimeOut, OMClosedAnalysisOut,
)

router = APIRouter(prefix="/api/om", tags=["O&M KPIs"])

def get_om_usecase():
    session = get_session()
    try:
        repo = SQLAlchemyOMRepository(session)
        yield OMUseCase(repo)
    finally:
        session.close()

@router.get("/productivity-team", response_model=List[OMProductivityTeamOut], summary="Get O&M Productivity per Team")
def get_productivity_team(
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
    return om_usecase.get_productivity_team(filters, limit, offset)

@router.get("/productivity-trend", response_model=List[OMProductivityTrendOut], summary="Get O&M Productivity Trend (Monthly)")
def get_productivity_trend(
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
    return om_usecase.get_productivity_trend(filters, limit, offset)

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
