from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from load.database import get_session
from load.models import (
    MIProgress, InventoryUtilization, 
    OMOpenAgeing, OMAvgClosureTime
)
from api.dashboard_schemas import DashboardOverviewOut, KPISummary
from api.routes.mi import _apply_mi_filters
from api.routes.om import _apply_om_filters

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard Unified API"])

def _get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()

@router.get("/overview", response_model=DashboardOverviewOut)
def get_dashboard_overview(
    period: Optional[str] = Query(None, description="daily, weekly, or monthly"),
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
    db: Session = Depends(_get_db)
):
    """
    Returns a unified high-level summary combining metrics from multiple KPI tables.
    Supports filtering by dimensions (discom, zone, etc.) and period type.
    """
    
    # Pack MI dimension filters
    mi_params = {
        "project": project,
        "discom": discom, "zone": zone, "circle": circle, 
        "division": division, "subdivision": subdivision, 
        "substation": substation, "feeder": feeder, "dtr": dtr,
        "new_meter_type": new_meter_type, "meter_category": meter_category
    }
    
    # Pack OM dimension filters (they share some common geography)
    om_params = {
        "project": project,
        "discom": discom, "zone": zone, "circle": circle, 
        "division": division, "subdivision": subdivision, 
        "substation": substation
    }

    # 1. Total Meters Installed (KPI 1 - MI Progress)
    q_mi = db.query(func.sum(MIProgress.total_mi_progress))
    q_mi = _apply_mi_filters(q_mi, MIProgress, mi_params)
    
    # Handle period filtering for MI
    if period:
        q_mi = q_mi.filter(MIProgress.period_type == period.lower())
    else:
        # Default to daily sum if no period is specified to avoid double counting
        q_mi = q_mi.filter(MIProgress.period_type == "daily")
        
    total_installed = q_mi.scalar() or 0

    # 2. Total Inventory and Utilization (KPI 4/5)
    q_inv_total = db.query(func.sum(InventoryUtilization.total_inventory))
    q_inv_total = _apply_mi_filters(q_inv_total, InventoryUtilization, mi_params)
    
    q_inv_inst = db.query(func.sum(InventoryUtilization.total_installed))
    q_inv_inst = _apply_mi_filters(q_inv_inst, InventoryUtilization, mi_params)

    # Prevent double-counting in inventory by defaulting to daily if no period is selected
    if period:
        q_inv_total = q_inv_total.filter(InventoryUtilization.period_type == period.lower())
        q_inv_inst = q_inv_inst.filter(InventoryUtilization.period_type == period.lower())
    else:
        q_inv_total = q_inv_total.filter(InventoryUtilization.period_type == "daily")
        q_inv_inst = q_inv_inst.filter(InventoryUtilization.period_type == "daily")

    total_inv = q_inv_total.scalar() or 0
    total_inv_installed = q_inv_inst.scalar() or 0
    
    overall_utilization = 0.0
    if total_inv > 0:
        overall_utilization = round((total_inv_installed / total_inv) * 100, 2)

    # 3. Total Open Complaints (OM Open Ageing)
    q_open = db.query(func.count(OMOpenAgeing.id))
    q_open = _apply_om_filters(q_open, OMOpenAgeing, om_params)
    total_open = q_open.scalar() or 0

    # 4. Average Closure Time (OM Avg Closure Time)
    q_avg_closure = db.query(func.avg(OMAvgClosureTime.avg_resolution_days))
    q_avg_closure = _apply_om_filters(q_avg_closure, OMAvgClosureTime, om_params)
    
    # OM handles periods differently (period_type for resolving timeframe), 
    # but for an overall dashboard metric, we usually just average whatever matches geography.
    avg_closure = q_avg_closure.scalar() or 0.0

    return DashboardOverviewOut(
        total_meters_installed=int(total_installed),
        total_inventory=int(total_inv),
        overall_utilization_pct=float(overall_utilization),
        total_open_complaints=int(total_open),
        avg_closure_time_days=round(float(avg_closure), 2),
        kpi_breakdowns=[
            KPISummary(kpi_name="Total MI Progress", value=int(total_installed)),
            KPISummary(kpi_name="Total Inventory", value=int(total_inv)),
            KPISummary(kpi_name="Overall Utilization %", value=float(overall_utilization)),
            KPISummary(kpi_name="Open O&M Tickets", value=int(total_open)),
            KPISummary(kpi_name="Avg Resolution Timeline (Days)", value=round(float(avg_closure), 2))
        ]
    )
