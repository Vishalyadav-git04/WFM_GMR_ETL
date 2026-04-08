from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from domain.interfaces import IMIRepository
from domain.entities import MIProgressEntity, InventoryUtilizationEntity
from .models import (
    MIProgress, MIProductivity, MonthlyProductivity,
    InventoryUtilization, StockAgeing, MIvsSAT, NonSATAgeing,
    MeterJourneyAvgTime, MeterCurrentStage,
    DashboardCommandCenter, DashboardCommandCenterTrend, DashboardCommandCenterMilestone
)
from infrastructure.config.settings import INSTALL_TABLE, INVENTORY_TABLE

class SQLAlchemyMIRepository(IMIRepository):
    def __init__(self, session: Session):
        self.session = session

    def _apply_filters(self, query, model, params: dict):
        """Standard filtering logic moved from routes to repository."""
        fields = [
            "discom", "zone", "circle", "division", "subdivision",
            "substation", "feeder", "dtr", "meter_category", "project"
        ]
        for field in fields:
            val = params.get(field)
            if val and hasattr(model, field):
                query = query.filter(getattr(model, field).ilike(val))
        
        start_date = params.get("start_date")
        end_date = params.get("end_date")
        if start_date and hasattr(model, "period_value"):
            query = query.filter(model.period_value >= start_date)
        if end_date and hasattr(model, "period_value"):
            query = query.filter(model.period_value <= end_date)
            
        return query

    def get_mi_progress_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        q = self.session.query(MIProgress)
        q = self._apply_filters(q, MIProgress, filters)
        
        period = filters.get("period") or "daily"
        q = q.filter(MIProgress.period_type == period.lower())
        
        total = q.with_entities(func.sum(MIProgress.total_mi_progress)).scalar() or 0
        
        cat_q = q.with_entities(MIProgress.meter_category, func.sum(MIProgress.total_mi_progress)).group_by(MIProgress.meter_category).all()
        category_breakdown = {k or "Unknown": int(v) for k, v in cat_q}
        
        per_q = q.with_entities(MIProgress.period_value, func.sum(MIProgress.total_mi_progress)).group_by(MIProgress.period_value).order_by(MIProgress.period_value).all()
        period_breakdown = [{"period_value": k, "progress": int(v)} for k, v in per_q]
        
        return {
            "total_progress": int(total),
            "category_breakdown": category_breakdown,
            "period_breakdown": period_breakdown
        }

    def get_mi_progress(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        q = self.session.query(MIProgress)
        q = self._apply_filters(q, MIProgress, filters)
        period = filters.get("period") or "daily"
        q = q.filter(MIProgress.period_type == period.lower())
        return q.offset(offset).limit(limit).all()

    def get_mi_productivity(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        q = self.session.query(MIProductivity)
        q = self._apply_filters(q, MIProductivity, filters)
        period = filters.get("period") or "daily"
        q = q.filter(MIProductivity.period_type == period.lower())
        technician = filters.get("technician")
        if technician:
            q = q.filter(MIProductivity.technician == technician)
        return q.offset(offset).limit(limit).all()

    def get_monthly_productivity(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        q = self.session.query(MonthlyProductivity)
        q = self._apply_filters(q, MonthlyProductivity, filters)
        period_value = filters.get("period_value")
        if period_value:
            q = q.filter(MonthlyProductivity.period_value == period_value)
        return q.offset(offset).limit(limit).all()

    def get_monthly_productivity_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        q = self.session.query(MonthlyProductivity)
        period_value = filters.get("period_value")
        if period_value:
            q = q.filter(MonthlyProductivity.period_value == period_value)
        q = self._apply_filters(q, MonthlyProductivity, filters)
        
        total = q.with_entities(func.sum(MonthlyProductivity.location_monthly_installations)).scalar() or 0
        cat_q = q.with_entities(MonthlyProductivity.meter_category, func.sum(MonthlyProductivity.location_monthly_installations)).group_by(MonthlyProductivity.meter_category).all()
        category_breakdown = [{"category": k or "Unknown", "installations": int(v)} for k, v in cat_q]
        per_q = q.with_entities(MonthlyProductivity.period_value, func.sum(MonthlyProductivity.location_monthly_installations)).group_by(MonthlyProductivity.period_value).order_by(MonthlyProductivity.period_value).all()
        period_breakdown = [{"period_value": k, "installations": int(v)} for k, v in per_q]

        return {
            "total_installations": int(total),
            "period_value": period_value,
            "category_breakdown": category_breakdown,
            "period_breakdown": period_breakdown
        }

    def get_pace_vs_stock(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        # Implementation depends on specific requirement, 
        # using InventoryUtilization as proxy if specific pace table not yet defined
        q = self.session.query(InventoryUtilization)
        q = self._apply_filters(q, InventoryUtilization, filters)
        return q.offset(offset).limit(limit).all()

    def get_pace_vs_stock_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.get_inventory_utilization_summary(filters)

    def get_inventory_utilization(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        q = self.session.query(InventoryUtilization)
        q = self._apply_filters(q, InventoryUtilization, filters)
        period = filters.get("period") or "daily"
        q = q.filter(InventoryUtilization.period_type == period.lower())
        return q.offset(offset).limit(limit).all()

    def get_inventory_utilization_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        # Complex logic using text() SQL for raw counts from source tables
        project = filters.get("project")
        meter_category = filters.get("meter_category")
        
        # 1. Total Inventory
        inv_sql = f'SELECT count(*) FROM {INVENTORY_TABLE}'
        inv_params = {}
        if project:
            inv_sql += ' WHERE project ILIKE :project'
            inv_params["project"] = project
        total_inv = self.session.execute(text(inv_sql), inv_params).scalar() or 0
        
        # 2. Total Installed
        inst_sql = f'SELECT count(*) FROM {INSTALL_TABLE}'
        inst_params = {}
        if project:
            inst_sql += ' WHERE "Project" ILIKE :project'
            inst_params["project"] = project
        total_inst = self.session.execute(text(inst_sql), inst_params).scalar() or 0
        
        rem_stock = total_inv - total_inst
        util_rate = (total_inst / total_inv * 100) if total_inv > 0 else 0
        
        return {
            "total_inventory": int(total_inv),
            "total_installed": int(total_inst),
            "utilization_rate_pct": round(float(util_rate), 2),
            "remaining_stock": int(rem_stock),
            "category_breakdown": [], # Simplified for now
            "period_breakdown": []
        }

    def get_mi_vs_sat(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        q = self.session.query(MIvsSAT)
        q = self._apply_filters(q, MIvsSAT, filters)
        return q.offset(offset).limit(limit).all()

    def get_mi_vs_sat_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        q = self.session.query(MIvsSAT)
        q = self._apply_filters(q, MIvsSAT, filters)

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

        return {
            "total_mi": t_mi,
            "total_sat": t_sat,
            "sat_progress_pct": round(float(pct), 2),
            "sat_1": int(res[2] or 0),
            "sat_2": int(res[3] or 0),
            "sat_3": int(res[4] or 0),
            "sat_4": int(res[5] or 0),
            "sat_5": int(res[6] or 0),
            "sat_6": int(res[7] or 0),
            "sat_7": int(res[8] or 0),
            "category_breakdown": [],
            "period_breakdown": []
        }

    def get_stock_ageing(self, limit: int, offset: int) -> List[Any]:
        # Stock ageing is a snapshot, docs say no dimension/date filtering
        return self.session.query(StockAgeing).offset(offset).limit(limit).all()

    def get_non_sat_ageing(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        q = self.session.query(NonSATAgeing)
        q = self._apply_filters(q, NonSATAgeing, filters)
        return q.offset(offset).limit(limit).all()

    def get_meter_journey(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        q = self.session.query(MeterJourneyAvgTime)
        q = self._apply_filters(q, MeterJourneyAvgTime, filters)
        return q.offset(offset).limit(limit).all()

    def get_meter_stage(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        q = self.session.query(MeterCurrentStage)
        q = self._apply_filters(q, MeterCurrentStage, filters)
        return q.offset(offset).limit(limit).all()

    def save_mi_progress(self, entities: List[MIProgressEntity]):
        models = [
            MIProgress(
                project=e.project, discom=e.discom, zone=e.zone, circle=e.circle,
                division=e.division, subdivision=e.subdivision, substation=e.substation,
                feeder=e.feeder, dtr=e.dtr, new_meter_type=e.new_meter_type,
                meter_category=e.meter_category, period_type=e.period_type,
                period_value=e.period_value, total_mi_progress=e.total_mi_progress
            ) for e in entities
        ]
        self.session.add_all(models)
        self.session.commit()

    def save_inventory_utilization(self, entities: List[InventoryUtilizationEntity]):
        pass # To be implemented

    def get_command_center_dashboard(self, project: str) -> Dict[str, Any]:
        snapshot = self.session.query(DashboardCommandCenter).filter(
            DashboardCommandCenter.project.ilike(project)
        ).first()

        trends = self.session.query(DashboardCommandCenterTrend).filter(
            DashboardCommandCenterTrend.project.ilike(project),
            DashboardCommandCenterTrend.period_type == 'monthly'
        ).order_by(DashboardCommandCenterTrend.period_value.asc()).all()

        milestones_db = self.session.query(DashboardCommandCenterMilestone).filter(
            DashboardCommandCenterMilestone.project.ilike(project)
        ).all()

        if not snapshot:
            return {}

        # 1. Structure satBlueData
        def get_fmt_date(d):
            return d.strftime('%m/%d/%Y') if d else None
            
        sat_milestones = {}
        for m in milestones_db:
            sat_milestones[m.stage] = {
                "start": get_fmt_date(m.start_date),
                "lumpsumInv": get_fmt_date(m.lumpsum_inv_date),
                "pmpInv": get_fmt_date(m.pmpm_inv_date),
                "lumpsumCol": get_fmt_date(m.lumpsum_col_date),
                "scCol": get_fmt_date(m.pmpm_col_date)
            }

        satBlueData = [
            {
                "stage": "SAT-1", 
                "installedBase": int(snapshot.sat_1_eligibility or 0),
                "cumulativeSat": int(snapshot.sat_1_achievement or 0),
                "efficiencyPct": float(snapshot.sat_1_throughput_pct or 0),
                "startSAT": sat_milestones.get("s1", {}).get("start")
            },
            {
                "stage": "SAT-2", 
                "installedBase": int(snapshot.sat_2_eligibility or 0),
                "cumulativeSat": int(snapshot.sat_2_achievement or 0),
                "efficiencyPct": float(snapshot.sat_2_throughput_pct or 0),
                "startSAT": sat_milestones.get("s2", {}).get("start")
            },
            {
                "stage": "SAT-3", 
                "installedBase": int(snapshot.sat_3_eligibility or 0),
                "cumulativeSat": int(snapshot.sat_3_achievement or 0),
                "efficiencyPct": float(snapshot.sat_3_throughput_pct or 0),
                "startSAT": sat_milestones.get("s3", {}).get("start")
            },
            {
                "stage": "SAT-4", 
                "installedBase": int(snapshot.sat_4_eligibility or 0),
                "cumulativeSat": int(snapshot.sat_4_achievement or 0),
                "efficiencyPct": float(snapshot.sat_4_throughput_pct or 0),
                "startSAT": sat_milestones.get("s4", {}).get("start")
            },
            {
                "stage": "SAT-5", 
                "installedBase": int(snapshot.sat_5_eligibility or 0),
                "cumulativeSat": int(snapshot.sat_5_achievement or 0),
                "efficiencyPct": float(snapshot.sat_5_throughput_pct or 0),
                "startSAT": sat_milestones.get("s5", {}).get("start")
            },
            {
                "stage": "SAT-6", 
                "installedBase": int(snapshot.sat_6_eligibility or 0),
                "cumulativeSat": int(snapshot.sat_6_achievement or 0),
                "efficiencyPct": float(snapshot.sat_6_throughput_pct or 0),
                "startSAT": sat_milestones.get("s6", {}).get("start")
            },
            {
                "stage": "SAT-7", 
                "installedBase": int(snapshot.sat_7_eligibility or 0),
                "cumulativeSat": int(snapshot.sat_7_achievement or 0),
                "efficiencyPct": float(snapshot.sat_7_throughput_pct or 0),
                "startSAT": sat_milestones.get("s7", {}).get("start")
            },
            {
                "stage": "SAT-8", 
                "installedBase": int(snapshot.sat_8_eligibility or 0),
                "cumulativeSat": int(snapshot.sat_8_achievement or 0),
                "efficiencyPct": float(snapshot.sat_8_throughput_pct or 0),
                "startSAT": sat_milestones.get("s8", {}).get("start")
            }
        ]

        # 2. Structure RAW
        raw = []
        for row in trends:
            raw.append({
                "month": row.period_value,
                "received": int(row.inventory_added or 0),
                "installed": int(row.installed_added or 0),
                "sat": {
                    "s1": int(row.s1_added or 0),
                    "s2": int(row.s2_added or 0),
                    "s3": int(row.s3_added or 0),
                    "s4": int(row.s4_added or 0),
                    "s5": int(row.s5_added or 0),
                    "s6": int(row.s6_added or 0),
                    "s7": int(row.s7_added or 0),
                    "s8": int(row.s8_added or 0)
                }
            })

        return {
            "satBlueData": satBlueData,
            "raw": raw,
            "sat_milestones": sat_milestones
        }

