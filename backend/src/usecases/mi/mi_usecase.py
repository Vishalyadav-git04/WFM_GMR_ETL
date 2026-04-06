from typing import List, Dict, Any, Optional
import polars as pl
from domain.interfaces import IMIRepository
from domain.entities import MIProgressEntity
from infrastructure.config.settings import MI_DIMENSIONS

class MIUseCase:
    def __init__(self, mi_repo: IMIRepository):
        self.mi_repo = mi_repo

    def get_mi_progress(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        return self.mi_repo.get_mi_progress(filters, limit, offset)

    def get_progress_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.mi_repo.get_mi_progress_summary(filters)

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

    def get_stock_ageing(self, limit: int, offset: int) -> List[Any]:
        return self.mi_repo.get_stock_ageing(limit, offset)

    def get_non_sat_ageing(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        return self.mi_repo.get_non_sat_ageing(filters, limit, offset)

    def run_mi_etl(self, df_install: pl.LazyFrame):
        """Orchestrates the MI transform and save process."""
        # Business logic for transformation (extracted from transform.py)
        # For brevity, I'll call the existing logic for now, but in full CA,
        # this would be native to the UseCase.
        from modules.mi.transform import kpi_1_mi_progress
        
        results = kpi_1_mi_progress(df_install)
        
        # Convert Polars result to Entities and Save via Repo
        for period, df in results.items():
            records = df.collect().to_dicts()
            entities = [
                MIProgressEntity(
                    project=r.get("Project"),
                    discom=r.get("Discom"),
                    zone=r.get("Zone"),
                    circle=r.get("Circle"),
                    division=r.get("Division"),
                    subdivision=r.get("SubDivision"),
                    substation=r.get("SubStation"),
                    feeder=r.get("Feeder"),
                    dtr=r.get("DTR"),
                    new_meter_type=r.get("newMeterType"),
                    meter_category=r.get("MeterCategory"),
                    period_type=period,
                    period_value=r.get(f"Install_{period.capitalize()}"),
                    total_mi_progress=r.get("Total_MI_Progress")
                ) for r in records
            ]
            self.mi_repo.save_mi_progress(entities)
