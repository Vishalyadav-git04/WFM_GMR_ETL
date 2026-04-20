from typing import List, Dict, Any, Optional
from domain.interfaces import IMIRepository
from infrastructure.config.settings import MI_DIMENSIONS

class MIUseCase:
    def __init__(self, mi_repo: IMIRepository):
        self.mi_repo = mi_repo



    def get_progress_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.mi_repo.get_mi_progress_dashboard(filters)

    def get_mi_productivity(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        return self.mi_repo.get_mi_productivity(filters, limit, offset)

    def get_monthly_productivity(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        return self.mi_repo.get_monthly_productivity(filters, limit, offset)

    def get_monthly_productivity_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.mi_repo.get_monthly_productivity_summary(filters)

    def get_inventory_utilization(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        return self.mi_repo.get_inventory_utilization(filters, limit, offset)

    def get_inventory_utilization_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.mi_repo.get_inventory_utilization_summary(filters)

    def get_pace_vs_stock(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        return self.mi_repo.get_pace_vs_stock(filters, limit, offset)

    def get_pace_vs_stock_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.mi_repo.get_pace_vs_stock_summary(filters)

    def get_mi_vs_sat(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        return self.mi_repo.get_mi_vs_sat(filters, limit, offset)

    def get_mi_vs_sat_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.mi_repo.get_mi_vs_sat_summary(filters)

    def get_stock_ageing(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        return self.mi_repo.get_stock_ageing(filters, limit, offset)

    def get_stock_ageing_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.mi_repo.get_stock_ageing_summary(filters)

    def get_stock_ageing_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.mi_repo.get_stock_ageing_dashboard(filters)

    def get_non_sat_ageing(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        return self.mi_repo.get_non_sat_ageing(filters, limit, offset)

    def get_non_sat_ageing_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.mi_repo.get_non_sat_ageing_dashboard(filters)

    def get_meter_journey(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        return self.mi_repo.get_meter_journey(filters, limit, offset)

    def get_meter_journey_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.mi_repo.get_meter_journey_dashboard(filters)

    def get_meter_stage_dashboard(self, filters: Dict[str, Any], limit: int, offset: int) -> Dict[str, Any]:
        return self.mi_repo.get_meter_stage_dashboard(filters, limit, offset)

    def get_command_center_dashboard(self, project: str) -> Dict[str, Any]:
        return self.mi_repo.get_command_center_dashboard(project)

    def get_mi_sat_invoice_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.mi_repo.get_mi_sat_invoice_summary(filters)

    def get_revenue_realized_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.mi_repo.get_revenue_realized_summary(filters)

    def get_revenue_ageing_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.mi_repo.get_revenue_ageing_summary(filters)

    def get_defective_meters_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.mi_repo.get_defective_meters_summary(filters)
