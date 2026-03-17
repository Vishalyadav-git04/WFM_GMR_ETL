"""
MI (Meter Installation) KPI API routes.
All endpoints support optional query-param filtering by dimension columns.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from load.database import get_session
from load.models import (
    MIProgress, MIProductivity, MonthlyProductivity,
    InventoryUtilization, StockAgeing, MIvsSAT,
)
from api.schemas import (
    MIProgressOut, MIProgressSummaryOut, MIProductivityOut, 
    MonthlyProductivityOut, MonthlyProductivitySummaryOut,
    InventoryUtilizationOut, InventoryUtilizationSummaryOut,
    StockAgeingOut, MIvsSATOut, MIvsSATSummaryOut,
)

router = APIRouter(prefix="/api/mi", tags=["MI KPIs"])


def _get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def _apply_mi_filters(query, model, params: dict):
    """Apply optional dimension filters to an ORM query."""
    col_map = {
        "discom": model.discom,
        "zone": model.zone,
        "circle": model.circle,
        "division": model.division,
        "subdivision": model.subdivision,
        "substation": model.substation,
        "feeder": model.feeder,
        "dtr": model.dtr,
        "new_meter_type": model.new_meter_type,
        "meter_category": model.meter_category,
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
        # Normalize filter dates if we are comparing against period_value (which is YYYY-WXX or YYYY-MM)
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
    elif hasattr(model, "di_date"):
        date_col = model.di_date

    if start_date and date_col is not None:
        query = query.filter(date_col >= start_date)
    if end_date and date_col is not None:
        query = query.filter(date_col <= end_date)
        
    return query


# ── KPI 1 : MI Progress ─────────────────────────────────────────────────

@router.get("/progress", response_model=list[MIProgressOut], summary="Get MI Progress Trend")
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

    db: Session = Depends(_get_db),
):
    q = db.query(MIProgress)
    q = _apply_mi_filters(q, MIProgress, locals())
    if period:
        q = q.filter(MIProgress.period_type == period.lower())
    else:
        # Default to daily to avoid returning a mix of daily, weekly and monthly rows
        q = q.filter(MIProgress.period_type == "daily")
    return q.offset(offset).limit(limit).all()

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

    db: Session = Depends(_get_db),
):
    """
    Returns aggregated summary for MI Progress based on applied filters.
    Includes overall total, category breakdown, and period-wise trend.
    """
    from sqlalchemy import func
    
    # Base query for filtering
    q = db.query(MIProgress)
    q = _apply_mi_filters(q, MIProgress, locals())
    
    if period:
        q = q.filter(MIProgress.period_type == period.lower())
    else:
        # Default to daily to avoid summing across daily, weekly, and monthly rows
        q = q.filter(MIProgress.period_type == "daily")
        
    # 1. Total Progress
    total = q.with_entities(func.sum(MIProgress.total_mi_progress)).scalar() or 0
    
    # 2. Category Breakdown
    cat_q = q.with_entities(MIProgress.meter_category, func.sum(MIProgress.total_mi_progress)).group_by(MIProgress.meter_category).all()
    category_breakdown = {k or "Unknown": int(v) for k, v in cat_q}
    
    # 3. Period Breakdown
    per_q = q.with_entities(MIProgress.period_value, func.sum(MIProgress.total_mi_progress)).group_by(MIProgress.period_value).order_by(MIProgress.period_value).all()
    period_breakdown = [{"period_value": k, "progress": int(v)} for k, v in per_q]
    
    return MIProgressSummaryOut(
        total_progress=int(total),
        category_breakdown=category_breakdown,
        period_breakdown=period_breakdown
    )


# ── KPI 2 : MI Productivity ─────────────────────────────────────────────

@router.get("/productivity", response_model=list[MIProductivityOut], summary="Get MI Productivity (Per Technician)")
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

    db: Session = Depends(_get_db),
):
    q = db.query(MIProductivity)
    q = _apply_mi_filters(q, MIProductivity, locals())
    if period:
        q = q.filter(MIProductivity.period_type == period.lower())
    else:
        # Default to daily to avoid returning a mix of daily, weekly and monthly rows
        q = q.filter(MIProductivity.period_type == "daily")
    if technician:
        q = q.filter(MIProductivity.technician == technician)
    return q.offset(offset).limit(limit).all()


# ── KPI 3 : Monthly Productivity ────────────────────────────────────────

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
    period_value: str = Query(..., description="Month in YYYY-MM format"),
    project: Optional[str] = None,
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),

    db: Session = Depends(_get_db),
):
    """Returns the total sum of installations for the filtered criteria."""
    from sqlalchemy import func
    
    q = db.query(MonthlyProductivity).filter(MonthlyProductivity.period_value == period_value)
    q = _apply_mi_filters(q, MonthlyProductivity, locals())
    
    total = q.with_entities(func.sum(MonthlyProductivity.location_monthly_installations)).scalar() or 0
    
    return MonthlyProductivitySummaryOut(
        total_installations=int(total),
        period_value=period_value
    )

@router.get("/monthly-productivity", response_model=list[MonthlyProductivityOut], summary="Get Monthly Productivity Detail")
def get_monthly_productivity(
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
    period_value: Optional[str] = None,
    limit: int = Query(1000, le=50000),
    offset: int = Query(0, ge=0),
    project: Optional[str] = None,
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),

    db: Session = Depends(_get_db),
):
    q = db.query(MonthlyProductivity)
    q = _apply_mi_filters(q, MonthlyProductivity, locals())
    if period:
        q = q.filter(MonthlyProductivity.period_type == period.lower())
    else:
        # KPI 3 only contains monthly data
        q = q.filter(MonthlyProductivity.period_type == "monthly")
    if period_value:
        q = q.filter(MonthlyProductivity.period_value == period_value)
    return q.offset(offset).limit(limit).all()


# ── KPI 4 & 5 : Inventory Utilization ───────────────────────────────────

@router.get("/inventory-utilization", response_model=list[InventoryUtilizationOut], summary="Get Inventory Utilization Detail")
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

    db: Session = Depends(_get_db),
):
    q = db.query(InventoryUtilization)
    q = _apply_mi_filters(q, InventoryUtilization, locals())
    if period:
        q = q.filter(InventoryUtilization.period_type == period.lower())
    else:
        # Default to daily to avoid returning a mix of daily, weekly and monthly rows
        q = q.filter(InventoryUtilization.period_type == "daily")
    return q.offset(offset).limit(limit).all()


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

    db: Session = Depends(_get_db),
):
    """Returns aggregated summary for Inventory Utilization."""
    from sqlalchemy import func
    q = db.query(InventoryUtilization)
    q = _apply_mi_filters(q, InventoryUtilization, locals())
    if period:
        q = q.filter(InventoryUtilization.period_type == period.lower())
    else:
        # Default to daily to avoid summing across daily, weekly, and monthly rows
        q = q.filter(InventoryUtilization.period_type == "daily")

    res = q.with_entities(
        func.sum(InventoryUtilization.total_inventory),
        func.sum(InventoryUtilization.total_installed),
        func.sum(InventoryUtilization.remaining_stock)
    ).first()
    
    total_inv = int(res[0] or 0)
    total_inst = int(res[1] or 0)
    rem_stock = int(res[2] or 0)
    util_rate = (total_inst / total_inv * 100) if total_inv > 0 else 0
    
    return InventoryUtilizationSummaryOut(
        total_inventory=total_inv,
        total_installed=total_inst,
        utilization_rate_pct=round(util_rate, 2),
        remaining_stock=rem_stock
    )


# ── KPI 5 : MI Pace vs Stock Availability ──────────────────────────────

@router.get("/pace-vs-stock", response_model=list[InventoryUtilizationOut], summary="Get MI Pace Detail")
def get_pace_vs_stock(
    period: Optional[str] = Query("daily", description="Filter by period: daily, weekly, or monthly"),
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

    db: Session = Depends(_get_db),
):
    """
    Dedicated endpoint for KPI 5 (MI Pace vs Stock Availability).
    Uses the same underlying model as Inventory Utilization but defaults to daily.
    """
    return get_inventory_utilization(
        period=period, discom=discom, zone=zone, circle=circle,
        division=division, subdivision=subdivision, substation=substation,
        feeder=feeder, dtr=dtr, new_meter_type=new_meter_type,
        meter_category=meter_category, limit=limit, offset=offset,
        project=project, start_date=start_date, end_date=end_date,
        db=db
    )

@router.get("/pace-vs-stock/summary", response_model=InventoryUtilizationSummaryOut, summary="Get MI Pace Aggregated Summary")
def get_pace_vs_stock_summary(
    period: Optional[str] = Query("daily", description="Filter by period: daily, weekly, or monthly"),
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

    db: Session = Depends(_get_db),
):
    return get_inventory_utilization_summary(
        period=period, discom=discom, zone=zone, circle=circle,
        division=division, subdivision=subdivision, substation=substation,
        feeder=feeder, dtr=dtr, new_meter_type=new_meter_type,
        meter_category=meter_category, project=project,
        start_date=start_date, end_date=end_date,
        db=db
    )
# ── KPI 6 : Stock Ageing ────────────────────────────────────────────────

@router.get("/stock-ageing", response_model=list[StockAgeingOut], summary="Get Unutilized Stock Ageing")
def get_stock_ageing(
    limit: int = Query(1000, le=50000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(_get_db),
):
    q = db.query(StockAgeing)
    return q.offset(offset).limit(limit).all()



# ── KPI 7 : MI vs SAT ───────────────────────────────────────────────────

@router.get("/mi-vs-sat", response_model=list[MIvsSATOut], summary="Get MI vs SAT Progress Detail")
def get_mi_vs_sat(
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

    db: Session = Depends(_get_db),
):
    q = db.query(MIvsSAT)
    q = _apply_mi_filters(q, MIvsSAT, locals())
    return q.offset(offset).limit(limit).all()


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

    db: Session = Depends(_get_db),
):
    """Returns aggregated summary for MI vs SAT including stage breakdown."""
    from sqlalchemy import func
    q = db.query(MIvsSAT)
    q = _apply_mi_filters(q, MIvsSAT, locals())

    res = q.with_entities(
        func.sum(MIvsSAT.total_mi),
        func.sum(MIvsSAT.total_sat),
        func.sum(MIvsSAT.sat_1),
        func.sum(MIvsSAT.sat_2),
        func.sum(MIvsSAT.sat_3),
        func.sum(MIvsSAT.sat_4),
        func.sum(MIvsSAT.sat_5),
        func.sum(MIvsSAT.sat_6),
        func.sum(MIvsSAT.sat_7),
    ).first()

    t_mi = int(res[0] or 0)
    t_sat = int(res[1] or 0)
    pct = (t_sat / t_mi * 100) if t_mi > 0 else 0

    return MIvsSATSummaryOut(
        total_mi=t_mi,
        total_sat=t_sat,
        sat_1=int(res[2] or 0),
        sat_2=int(res[3] or 0),
        sat_3=int(res[4] or 0),
        sat_4=int(res[5] or 0),
        sat_5=int(res[6] or 0),
        sat_6=int(res[7] or 0),
        sat_7=int(res[8] or 0),
        sat_progress_pct=round(pct, 2)
    )
