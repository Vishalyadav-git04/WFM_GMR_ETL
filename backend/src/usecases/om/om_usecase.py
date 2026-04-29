from typing import List, Dict, Any, Optional
from domain.interfaces import IOMRepository

class OMUseCase:
    def __init__(self, om_repo: IOMRepository):
        self.om_repo = om_repo

    def get_productivity_team_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.om_repo.get_productivity_team_dashboard(filters)

    def get_productivity_trend_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.om_repo.get_productivity_trend_dashboard(filters)

    def get_open_ageing(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        return self.om_repo.get_open_ageing(filters, limit, offset)

    def get_open_ageing_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.om_repo.get_open_ageing_dashboard(filters)

    def get_avg_closure_time(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        return self.om_repo.get_avg_closure_time(filters, limit, offset)

    def get_avg_closure_time_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.om_repo.get_avg_closure_time_dashboard(filters)

    def get_closed_analysis(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        return self.om_repo.get_closed_analysis(filters, limit, offset)

    def get_closed_analysis_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.om_repo.get_closed_analysis_dashboard(filters)
