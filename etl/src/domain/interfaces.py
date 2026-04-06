from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .entities import (
    MIProgressEntity, MIProductivityEntity, MonthlyProductivityEntity,
    InventoryUtilizationEntity, StockAgeingEntity, MIvsSATEntity, NonSATAgeingEntity,
    OMProductivityTeamEntity, OMProductivityTrendEntity, OMOpenAgeingEntity,
    OMAvgClosureTimeEntity, OMClosedAnalysisEntity, ComplaintEntity, ETLRunLogEntity
)

class IMIRepository(ABC):
    @abstractmethod
    def save_mi_progress(self, items: List[MIProgressEntity]): pass
    
    @abstractmethod
    def get_mi_progress(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]: pass

    @abstractmethod
    def get_mi_progress_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]: pass
    
    @abstractmethod
    def get_mi_productivity(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]: pass

    @abstractmethod
    def get_monthly_productivity_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]: pass

    @abstractmethod
    def get_inventory_utilization_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]: pass

    @abstractmethod
    def get_mi_vs_sat_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]: pass

    @abstractmethod
    def save_inventory_utilization(self, items: List[InventoryUtilizationEntity]): pass

class IOMRepository(ABC):
    @abstractmethod
    def save_productivity_team(self, items: List[OMProductivityTeamEntity]): pass
    
    @abstractmethod
    def get_productivity_team(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]: pass

    @abstractmethod
    def get_productivity_trend(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]: pass

    @abstractmethod
    def get_open_ageing(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]: pass

    @abstractmethod
    def get_avg_closure_time(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]: pass

    @abstractmethod
    def get_closed_analysis(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]: pass

    @abstractmethod
    def get_open_complaints_count(self, filters: Dict[str, Any]) -> int: pass
    
    @abstractmethod
    def get_avg_closure_time_metric(self, filters: Dict[str, Any]) -> float: pass

class IETLRepository(ABC):
    @abstractmethod
    def log_run(self, log: ETLRunLogEntity) -> int: pass
    
    @abstractmethod
    def update_run(self, run_id: int, status: str, error: Optional[str] = None): pass
