from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .entities import (
    MIProgressEntity,
    OMOpenAgeingEntity,
    OMAvgClosureTimeEntity, OMClosedAnalysisEntity, ETLRunLogEntity,
)

class IMIRepository(ABC):
    @abstractmethod
    def save_mi_progress(self, items: List[MIProgressEntity]): pass

    @abstractmethod
    def get_mi_progress_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]: pass

    @abstractmethod
    def get_productivity_team_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]: pass

    @abstractmethod
    def get_productivity_trend_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]: pass

    @abstractmethod
    def get_inventory_utilization_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]: pass

    @abstractmethod
    def get_pace_vs_stock_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]: pass

    @abstractmethod
    def get_mi_vs_sat_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]: pass

    @abstractmethod
    def get_stock_ageing_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]: pass

    @abstractmethod
    def get_non_sat_ageing_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]: pass

    @abstractmethod
    def get_meter_journey_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]: pass

    @abstractmethod
    def get_meter_stage_dashboard(self, filters: Dict[str, Any], limit: int, offset: int) -> Dict[str, Any]: pass

    @abstractmethod
    def get_command_center_dashboard(self, project: str) -> Dict[str, Any]: pass

    @abstractmethod
    def get_sat_dash_sat_blue_data(self) -> Dict[str, Any]: pass

    @abstractmethod
    def get_sat_dash_region_monthly(self, region: str) -> List[Dict[str, Any]]: pass

class IOMRepository(ABC):
    @abstractmethod
    def get_productivity_team_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]: pass

    @abstractmethod
    def get_productivity_trend_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]: pass

    @abstractmethod
    def get_open_ageing(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]: pass

    @abstractmethod
    def get_open_ageing_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]: pass

    @abstractmethod
    def get_avg_closure_time(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]: pass

    @abstractmethod
    def get_avg_closure_time_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]: pass

    @abstractmethod
    def get_closed_analysis_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]: pass


class IETLRepository(ABC):
    @abstractmethod
    def log_run(self, log: ETLRunLogEntity) -> int: pass

    @abstractmethod
    def update_run(self, run_id: int, status: str, error: Optional[str] = None): pass
