"""
O&M (Operations & Maintenance) KPI API routes.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from load.database import get_session
from load.models import (
    OMProductivityTeam, OMProductivityTrend, OMOpenAgeing,
    OMAvgClosureTime, OMClosedAnalysis,
)
from api.schemas import (
    OMProductivityTeamOut, OMProductivityTrendOut, OMOpenAgeingOut,
    OMAvgClosureTimeOut, OMClosedAnalysisOut,
)

router = APIRouter(prefix="/api/om", tags=["O&M KPIs"])


def _get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def _apply_om_filters(query, model, params: dict):
    col_map = {
        "discom": model.discom,
        "zone": model.zone,
        "circle": model.circle,
        "division": model.division,
        "subdivision": model.subdivision,
        "substation": model.substation,
        "om_category": model.om_category,
    }
    if hasattr(model, "project"):
        col_map["project"] = model.project
    for key, col in col_map.items():
        val = params.get(key)
        if val is not None:
            query = query.filter(col.ilike(val))
    # Date filtering heuristics
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    period = params.get("period")
    
    date_col = None
    if hasattr(model, "period_value"):
        date_col = model.period_value
        # Normalize filter dates if we are comparing against period_value
        if period:
            period = period.lower()
            from datetime import datetime
            if period == "weekly" and start_date:
                try: start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-W%U")
                except: pass
            if period == "weekly" and end_date:
                try: end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y-W%U")
                except: pass
            if period == "monthly" and start_date:
                start_date = start_date[:7]
            if period == "monthly" and end_date:
                end_date = end_date[:7]
    elif hasattr(model, "closed_month"):
        date_col = model.closed_month
    elif hasattr(model, "created_date"):
        date_col = model.created_date
    elif hasattr(model, "period_value_created"):
        date_col = model.period_value_created

    if start_date and date_col is not None:
        query = query.filter(date_col >= start_date)
    if end_date and date_col is not None:
        query = query.filter(date_col <= end_date)
        
    return query


# ── KPI 1 : Productivity per team ───────────────────────────────────────

@router.get("/productivity-team", response_model=list[OMProductivityTeamOut])
def get_productivity_team(
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    substation: Optional[str] = None,
    om_category: Optional[str] = None,
    period: Optional[str] = Query(None, description="daily | weekly | monthly"),
    limit: int = Query(1000, le=50000),
    offset: int = Query(0, ge=0),
    project: Optional[str] = None,
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),

    db: Session = Depends(_get_db),
):
    q = db.query(OMProductivityTeam)
    q = _apply_om_filters(q, OMProductivityTeam, locals())
    if period:
        q = q.filter(OMProductivityTeam.period_type == period)
    return q.offset(offset).limit(limit).all()


# ── KPI 2 : Productivity trend ──────────────────────────────────────────

@router.get("/productivity-trend", response_model=list[OMProductivityTrendOut])
def get_productivity_trend(
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    substation: Optional[str] = None,
    om_category: Optional[str] = None,
    limit: int = Query(1000, le=50000),
    offset: int = Query(0, ge=0),
    project: Optional[str] = None,
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),

    db: Session = Depends(_get_db),
):
    q = db.query(OMProductivityTrend)
    q = _apply_om_filters(q, OMProductivityTrend, locals())
    return q.offset(offset).limit(limit).all()


# ── KPI 3 : Open ticket ageing ──────────────────────────────────────────

@router.get("/open-ageing", response_model=list[OMOpenAgeingOut])
def get_open_ageing(
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    substation: Optional[str] = None,
    om_category: Optional[str] = None,
    limit: int = Query(1000, le=50000),
    offset: int = Query(0, ge=0),
    project: Optional[str] = None,
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),

    db: Session = Depends(_get_db),
):
    q = db.query(OMOpenAgeing)
    q = _apply_om_filters(q, OMOpenAgeing, locals())
    return q.offset(offset).limit(limit).all()


# ── KPI 4 : Avg closure time ────────────────────────────────────────────

@router.get("/avg-closure-time", response_model=list[OMAvgClosureTimeOut])
def get_avg_closure_time(
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    substation: Optional[str] = None,
    om_category: Optional[str] = None,
    period: Optional[str] = Query(None, description="daily | weekly | monthly"),
    limit: int = Query(1000, le=50000),
    offset: int = Query(0, ge=0),
    project: Optional[str] = None,
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),

    db: Session = Depends(_get_db),
):
    q = db.query(OMAvgClosureTime)
    q = _apply_om_filters(q, OMAvgClosureTime, locals())
    if period:
        q = q.filter(OMAvgClosureTime.period_type == period)
    return q.offset(offset).limit(limit).all()


# ── KPI 5 : Closed analysis ─────────────────────────────────────────────

@router.get("/closed-analysis", response_model=list[OMClosedAnalysisOut])
def get_closed_analysis(
    discom: Optional[str] = None,
    zone: Optional[str] = None,
    circle: Optional[str] = None,
    division: Optional[str] = None,
    subdivision: Optional[str] = None,
    substation: Optional[str] = None,
    om_category: Optional[str] = None,
    period: Optional[str] = Query(None, description="daily | weekly | monthly"),
    limit: int = Query(1000, le=50000),
    offset: int = Query(0, ge=0),
    project: Optional[str] = None,
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),

    db: Session = Depends(_get_db),
):
    q = db.query(OMClosedAnalysis)
    q = _apply_om_filters(q, OMClosedAnalysis, locals())
    if period:
        q = q.filter(OMClosedAnalysis.period_type == period)
    return q.offset(offset).limit(limit).all()
