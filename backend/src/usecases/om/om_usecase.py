from typing import List, Dict, Any, Optional
from domain.interfaces import IOMRepository
from domain.entities import OMOpenAgeingEntity

class OMUseCase:
    def __init__(self, om_repo: IOMRepository):
        self.om_repo = om_repo

    def get_productivity_team(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        return self.om_repo.get_productivity_team(filters, limit, offset)

    def get_productivity_trend(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        return self.om_repo.get_productivity_trend(filters, limit, offset)

    def get_open_ageing(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        return self.om_repo.get_open_ageing(filters, limit, offset)

    def get_avg_closure_time(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        return self.om_repo.get_avg_closure_time(filters, limit, offset)

    def get_closed_analysis(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        return self.om_repo.get_closed_analysis(filters, limit, offset)

    def get_dashboard_metrics(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Gets high-level O&M metrics for the dashboard."""
        open_tickets = self.om_repo.get_open_complaints_count(filters)
        avg_closure = self.om_repo.get_avg_closure_time_metric(filters)
        return {
            "total_open_complaints": open_tickets,
            "avg_closure_time_days": round(avg_closure, 2)
        }

    def run_om_etl(self, df_complaints: Any):
        """Orchestrates O&M ETL."""
        # Process and save productivity team, trend, etc.
        pass
