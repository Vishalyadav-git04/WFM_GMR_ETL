from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class KPISummary(BaseModel):
    kpi_name: str
    value: Any

class DashboardOverviewOut(BaseModel):
    total_meters_installed: int
    total_inventory: int
    overall_utilization_pct: float
    total_open_complaints: int
    avg_closure_time_days: float
    kpi_breakdowns: List[KPISummary]
    
    class Config:
        from_attributes = True
