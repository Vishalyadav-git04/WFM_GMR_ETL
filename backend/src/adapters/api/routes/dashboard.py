from fastapi import APIRouter, Depends, Query
from typing import Optional, Dict, Any

from infrastructure.database.setup import get_session
from adapters.repository.sqlalchemy_mi_repo import SQLAlchemyMIRepository
from adapters.repository.sqlalchemy_om_repo import SQLAlchemyOMRepository
from usecases.mi.mi_usecase import MIUseCase
from usecases.om.om_usecase import OMUseCase
from adapters.api.dashboard_schemas import DashboardOverviewOut, KPISummary

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard Unified API"])

def get_mi_usecase():
    session = get_session()
    try:
        repo = SQLAlchemyMIRepository(session)
        yield MIUseCase(repo)
    finally:
        session.close()

def get_om_usecase():
    session = get_session()
    try:
        repo = SQLAlchemyOMRepository(session)
        yield OMUseCase(repo)
    finally:
        session.close()

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
    mi_usecase: MIUseCase = Depends(get_mi_usecase),
    om_usecase: OMUseCase = Depends(get_om_usecase),
):
    filters = locals()
    filters.pop("mi_usecase")
    filters.pop("om_usecase")
    
    # 1. MI Metrics
    mi_summary = mi_usecase.get_progress_summary(filters)
    inv_summary = mi_usecase.get_inventory_utilization_summary(filters)
    
    total_installed = mi_summary.get("total_progress", 0)
    total_inv = inv_summary.get("total_inventory", 0)
    utilization = inv_summary.get("utilization_rate_pct", 0.0)
    
    # 2. OM Metrics
    om_summary = om_usecase.get_dashboard_metrics(filters)
    total_open = om_summary.get("total_open_complaints", 0)
    avg_closure = om_summary.get("avg_closure_time_days", 0.0)

    return DashboardOverviewOut(
        total_meters_installed=int(total_installed),
        total_inventory=int(total_inv),
        overall_utilization_pct=float(utilization),
        total_open_complaints=int(total_open),
        avg_closure_time_days=float(avg_closure),
        kpi_breakdowns=[
            KPISummary(kpi_name="Total MI Progress", value=int(total_installed)),
            KPISummary(kpi_name="Total Inventory", value=int(total_inv)),
            KPISummary(kpi_name="Overall Utilization %", value=float(utilization)),
            KPISummary(kpi_name="Open O&M Tickets", value=int(total_open)),
            KPISummary(kpi_name="Avg Resolution Timeline (Days)", value=float(avg_closure))
        ]
    )
