from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, text, case
from domain.interfaces import IMIRepository
from domain.entities import MIProgressEntity, InventoryUtilizationEntity
from .models import (
    MIProgress, MIProductivity, MonthlyProductivity,
    InventoryUtilization, StockAgeing, MIvsSAT, NonSATAgeing,
    MeterJourneyAvgTime, MeterCurrentStage,
    MIvsSATvsInvoice, RevenueRealized, RevenueAgeing,
    DefectiveMeters,
    DashboardCommandCenter, DashboardCommandCenterTrend, DashboardCommandCenterMilestone
)
from infrastructure.config.settings import MI_SOURCE_TABLE

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

    def _format_nested_breakdown(self, rows, value_keys):
        """
        Helper to transform flat 2 or 3-way group rows into nested structure.
        2 levels: { Key: { total: {v}, Metertype: {v} } }
        3 levels: { Key: { total: {v}, Category: { total: {v}, Metertype: {v} } } }
        """
        res = {}
        for r in rows:
            num_vals = len(value_keys)
            num_groups = len(r) - num_vals
            
            # Extract grouping labels, ensuring strings
            keys = [str(x) if x is not None else "Unknown" for x in r[:num_groups]]
            vals = [int(v or 0) for v in r[num_groups:]]
            
            if num_groups == 2:
                # Category -> MeterType
                c, m = keys[0], keys[1]
                if c not in res:
                    res[c] = {"total": {k: 0 for k in value_keys}}
                if m not in res[c]:
                    res[c][m] = {k: 0 for k in value_keys}
                
                for j, vk in enumerate(value_keys):
                    val = vals[j]
                    res[c][m][vk] += val
                    res[c]["total"][vk] += val

            elif num_groups == 3:
                # Period -> Category -> MeterType
                p, c, m = keys[0], keys[1], keys[2]
                if p not in res:
                    res[p] = {"total": {k: 0 for k in value_keys}}
                if c not in res[p]:
                    res[p][c] = {"total": {k: 0 for k in value_keys}}
                if m not in res[p][c]:
                    res[p][c][m] = {k: 0 for k in value_keys}
                
                for j, vk in enumerate(value_keys):
                    val = vals[j]
                    res[p][c][m][vk] += val
                    res[p][c]["total"][vk] += val
                    res[p]["total"][vk] += val
        return res

    def get_mi_progress_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        q = self.session.query(MIProgress)
        q = self._apply_filters(q, MIProgress, filters)
        
        period = filters.get("period") or "daily"
        q = q.filter(MIProgress.period_type == period.lower())
        
        # 1. Main Total
        total = q.with_entities(func.sum(MIProgress.total_mi_progress)).scalar() or 0
        
        # 2. Nested Category Breakdown (No period)
        cat_rows = q.with_entities(
            MIProgress.meter_category, 
            MIProgress.new_meter_type, 
            func.sum(MIProgress.total_mi_progress)
        ).group_by(MIProgress.meter_category, MIProgress.new_meter_type).all()
        category_breakdown = self._format_nested_breakdown(cat_rows, ["count"])
        
        # 3. Nested Period Breakdown
        per_rows = q.with_entities(
            MIProgress.period_value, 
            MIProgress.meter_category, 
            MIProgress.new_meter_type, 
            func.sum(MIProgress.total_mi_progress)
        ).group_by(MIProgress.period_value, MIProgress.meter_category, MIProgress.new_meter_type).order_by(MIProgress.period_value).all()
        period_breakdown = self._format_nested_breakdown(per_rows, ["progress"])
        
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
        
        # 1. Total
        total = q.with_entities(func.sum(MonthlyProductivity.location_monthly_installations)).scalar() or 0
        
        # 2. Nested Category Breakdown (No period)
        cat_rows = q.with_entities(
            MonthlyProductivity.meter_category,
            MonthlyProductivity.new_meter_type,
            func.sum(MonthlyProductivity.location_monthly_installations)
        ).group_by(MonthlyProductivity.meter_category, MonthlyProductivity.new_meter_type).all()
        category_breakdown = self._format_nested_breakdown(cat_rows, ["installations"])
        
        # 3. Nested Period Breakdown
        per_rows = q.with_entities(
            MonthlyProductivity.period_value,
            MonthlyProductivity.meter_category,
            MonthlyProductivity.new_meter_type,
            func.sum(MonthlyProductivity.location_monthly_installations)
        ).group_by(MonthlyProductivity.period_value, MonthlyProductivity.meter_category, MonthlyProductivity.new_meter_type).order_by(MonthlyProductivity.period_value).all()
        period_breakdown = self._format_nested_breakdown(per_rows, ["installations"])

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
        # Refactored to use pre-calculated tables and include nested breakdowns
        q = self.session.query(InventoryUtilization)
        q = self._apply_filters(q, InventoryUtilization, filters)
        
        # We must filter by a single period_type to avoid double-counting
        q = q.filter(InventoryUtilization.period_type == 'daily')
        
        # 1. Aggregate the main totals
        res = q.with_entities(
            func.sum(InventoryUtilization.total_inventory),
            func.sum(InventoryUtilization.total_installed),
            func.sum(InventoryUtilization.remaining_stock)
        ).first()
        
        total_inv = int(res[0] or 0)
        total_inst = int(res[1] or 0)
        rem_stock = int(res[2] or 0)
        util_rate = (total_inst / total_inv * 100) if total_inv > 0 else 0
        
        # 2. Nested Category Breakdown (No period)
        cat_rows = q.with_entities(
            InventoryUtilization.meter_category,
            InventoryUtilization.new_meter_type,
            func.sum(InventoryUtilization.total_inventory),
            func.sum(InventoryUtilization.total_installed)
        ).group_by(InventoryUtilization.meter_category, InventoryUtilization.new_meter_type).all()
        category_breakdown = self._format_nested_breakdown(cat_rows, ["inventory", "installed"])
        
        # 3. Nested Period Breakdown
        per_rows = q.with_entities(
            InventoryUtilization.period_value,
            InventoryUtilization.meter_category,
            InventoryUtilization.new_meter_type,
            func.sum(InventoryUtilization.total_installed)
        ).group_by(InventoryUtilization.period_value, InventoryUtilization.meter_category, InventoryUtilization.new_meter_type).order_by(InventoryUtilization.period_value).all()
        period_breakdown = self._format_nested_breakdown(per_rows, ["installed"])

        return {
            "total_inventory": total_inv,
            "total_installed": total_inst,
            "utilization_rate_pct": round(float(util_rate), 2),
            "remaining_stock": rem_stock,
            "category_breakdown": category_breakdown, 
            "period_breakdown": period_breakdown
        }



    def get_mi_vs_sat(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        q = self.session.query(MIvsSAT)
        q = self._apply_filters(q, MIvsSAT, filters)
        return q.offset(offset).limit(limit).all()

    def get_mi_vs_sat_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        q = self.session.query(MIvsSAT)
        q = self._apply_filters(q, MIvsSAT, filters)

        # 1. Aggregate main totals
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
            func.sum(MIvsSAT.sat_8),
            func.sum(MIvsSAT.sat_9),
        ).first()

        t_mi = int(res[0] or 0)
        t_sat = int(res[1] or 0)
        pct = (t_sat / t_mi * 100) if t_mi > 0 else 0

        # 2. Nested Category Breakdown (No period)
        sat_keys = ["total_mi", "total_sat", "s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9"]
        cat_rows = q.with_entities(
            MIvsSAT.meter_category,
            MIvsSAT.new_meter_type,
            func.sum(MIvsSAT.total_mi),
            func.sum(MIvsSAT.total_sat),
            func.sum(MIvsSAT.sat_1),
            func.sum(MIvsSAT.sat_2),
            func.sum(MIvsSAT.sat_3),
            func.sum(MIvsSAT.sat_4),
            func.sum(MIvsSAT.sat_5),
            func.sum(MIvsSAT.sat_6),
            func.sum(MIvsSAT.sat_7),
            func.sum(MIvsSAT.sat_8),
            func.sum(MIvsSAT.sat_9)
        ).group_by(MIvsSAT.meter_category, MIvsSAT.new_meter_type).all()
        category_breakdown = self._format_nested_breakdown(cat_rows, sat_keys)
        
        # 3. Nested Period Breakdown (Trend)
        per_rows = q.with_entities(
            MIvsSAT.period_value,
            MIvsSAT.meter_category,
            MIvsSAT.new_meter_type,
            func.sum(MIvsSAT.total_sat)
        ).group_by(MIvsSAT.period_value, MIvsSAT.meter_category, MIvsSAT.new_meter_type).order_by(MIvsSAT.period_value).all()
        period_breakdown = self._format_nested_breakdown(per_rows, ["total_sat"])

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
            "sat_8": int(res[9] or 0),
            "sat_9": int(res[10] or 0),
            "category_breakdown": category_breakdown,
            "period_breakdown": period_breakdown
        }


    def get_stock_ageing(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        q = self.session.query(StockAgeing)
        q = self._apply_filters(q, StockAgeing, filters)
        return q.offset(offset).limit(limit).all()

    def get_stock_ageing_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """KPI 6: Stock Ageing summary."""
        q = self.session.query(StockAgeing)
        q = self._apply_filters(q, StockAgeing, filters)
        
        # Period Breakdown
        p_rows = q.with_entities(
            StockAgeing.period_value,
            StockAgeing.meter_category,
            StockAgeing.new_meter_type,
            func.sum(StockAgeing.age_0_30),
            func.sum(StockAgeing.age_31_60),
            func.sum(StockAgeing.age_61_90),
            func.sum(StockAgeing.age_90_plus)
        ).group_by(StockAgeing.period_value, StockAgeing.meter_category, StockAgeing.new_meter_type).all()
        
        # Category Breakdown
        c_rows = q.with_entities(
            StockAgeing.meter_category,
            StockAgeing.new_meter_type,
            func.sum(StockAgeing.age_0_30),
            func.sum(StockAgeing.age_31_60),
            func.sum(StockAgeing.age_61_90),
            func.sum(StockAgeing.age_90_plus)
        ).group_by(StockAgeing.meter_category, StockAgeing.new_meter_type).all()
        
        vals = ["age_0_30", "age_31_60", "age_61_90", "age_90_plus"]
        return {
            "period_breakdown": self._format_nested_breakdown(p_rows, vals),
            "category_breakdown": self._format_nested_breakdown(c_rows, vals)
        }

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
                "stage": "SAT-9" if project.upper() == "AGRA" else "SAT-8", 
                "installedBase": int((snapshot.sat_9_eligibility if project.upper() == "AGRA" else snapshot.sat_8_eligibility) or 0),
                "cumulativeSat": int((snapshot.sat_9_achievement if project.upper() == "AGRA" else snapshot.sat_8_achievement) or 0),
                "efficiencyPct": float((snapshot.sat_9_throughput_pct if project.upper() == "AGRA" else snapshot.sat_8_throughput_pct) or 0),
                "startSAT": sat_milestones.get("s9" if project.upper() == "AGRA" else "s8", {}).get("start")
            }
        ]

        # 2. Structure RAW
        raw = []
        for row in trends:
            # Use the correct SAT stage key per region
            sat_stage_key = "s9" if project.upper() == "AGRA" else "s8"
            sat_stage_value = int((row.s9_added if project.upper() == "AGRA" else row.s8_added) or 0)
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
                    sat_stage_key: sat_stage_value
                }
            })

        return {
            "inventory": int(snapshot.inventory or 0),
            "installed": int(snapshot.installed or 0),
            "total_sat": int(snapshot.total_sat or 0),
            "total_invoice": int(snapshot.total_invoice or 0),
            "region": project.upper(),
            "satBlueData": satBlueData,
            "raw": raw,
            "sat_milestones": sat_milestones
        }


    def get_mi_sat_invoice_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """KPI 11: MI vs SAT vs Invoice funnel summary."""
        q = self.session.query(MIvsSATvsInvoice)
        q = self._apply_filters(q, MIvsSATvsInvoice, filters)
        
        # Period Breakdown
        p_rows = q.with_entities(
            MIvsSATvsInvoice.period_value,
            MIvsSATvsInvoice.meter_category,
            MIvsSATvsInvoice.new_meter_type,
            func.sum(MIvsSATvsInvoice.total_mi),
            func.sum(MIvsSATvsInvoice.total_sat),
            func.sum(MIvsSATvsInvoice.total_invoice)
        ).group_by(MIvsSATvsInvoice.period_value, MIvsSATvsInvoice.meter_category, MIvsSATvsInvoice.new_meter_type).all()
        
        # Category Breakdown
        c_rows = q.with_entities(
            MIvsSATvsInvoice.meter_category,
            MIvsSATvsInvoice.new_meter_type,
            func.sum(MIvsSATvsInvoice.total_mi),
            func.sum(MIvsSATvsInvoice.total_sat),
            func.sum(MIvsSATvsInvoice.total_invoice)
        ).group_by(MIvsSATvsInvoice.meter_category, MIvsSATvsInvoice.new_meter_type).all()
        
        vals = ["mi", "sat", "invoice"]
        return {
            "total_mi": int(sum(r[2] for r in c_rows) or 0),
            "total_sat": int(sum(r[3] for r in c_rows) or 0),
            "total_invoice": int(sum(r[4] for r in c_rows) or 0),
            "period_breakdown": self._format_nested_breakdown(p_rows, vals),
            "category_breakdown": self._format_nested_breakdown(c_rows, vals)
        }


    def get_revenue_realized_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """KPI 12: Revenue Realized summary."""
        q = self.session.query(RevenueRealized)
        q = self._apply_filters(q, RevenueRealized, filters)
        
        p_rows = q.with_entities(
            RevenueRealized.period_value,
            RevenueRealized.meter_category,
            RevenueRealized.new_meter_type,
            func.sum(RevenueRealized.total_realized)
        ).group_by(RevenueRealized.period_value, RevenueRealized.meter_category, RevenueRealized.new_meter_type).all()
        
        c_rows = q.with_entities(
            RevenueRealized.meter_category,
            RevenueRealized.new_meter_type,
            func.sum(RevenueRealized.total_realized)
        ).group_by(RevenueRealized.meter_category, RevenueRealized.new_meter_type).all()
        
        return {
            "total_realized": int(sum(r[2] for r in c_rows) or 0),
            "period_breakdown": self._format_nested_breakdown(p_rows, ["realized"]),
            "category_breakdown": self._format_nested_breakdown(c_rows, ["realized"])
        }


    def get_revenue_ageing_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """KPI 13: Revenue Ageing summary."""
        q = self.session.query(RevenueAgeing)
        q = self._apply_filters(q, RevenueAgeing, filters)
        
        p_rows = q.with_entities(
            RevenueAgeing.period_value,
            RevenueAgeing.meter_category,
            RevenueAgeing.new_meter_type,
            func.sum(RevenueAgeing.age_0_30),
            func.sum(RevenueAgeing.age_31_60),
            func.sum(RevenueAgeing.age_61_90),
            func.sum(RevenueAgeing.age_90_plus)
        ).group_by(RevenueAgeing.period_value, RevenueAgeing.meter_category, RevenueAgeing.new_meter_type).all()
        
        c_rows = q.with_entities(
            RevenueAgeing.meter_category,
            RevenueAgeing.new_meter_type,
            func.sum(RevenueAgeing.age_0_30),
            func.sum(RevenueAgeing.age_31_60),
            func.sum(RevenueAgeing.age_61_90),
            func.sum(RevenueAgeing.age_90_plus)
        ).group_by(RevenueAgeing.meter_category, RevenueAgeing.new_meter_type).all()
        
        vals = ["age_0_30", "age_31_60", "age_61_90", "age_90_plus"]
        return {
            "period_breakdown": self._format_nested_breakdown(p_rows, vals),
            "category_breakdown": self._format_nested_breakdown(c_rows, vals)
        }

    def get_defective_meters_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """KPI 14: Defective Meters summary."""
        q = self.session.query(DefectiveMeters)
        q = self._apply_filters(q, DefectiveMeters, filters)
        
        # We need to sum meter_count for each defective_type
        # Categories: Meter Burnt, Meter Faulty, Others
        entities = [
            DefectiveMeters.meter_category,
            DefectiveMeters.new_meter_type,
            func.sum(case((DefectiveMeters.defective_type == 'Meter Burnt', DefectiveMeters.meter_count), else_=0)),
            func.sum(case((DefectiveMeters.defective_type == 'Meter Faulty', DefectiveMeters.meter_count), else_=0)),
            func.sum(case((DefectiveMeters.defective_type == 'Others', DefectiveMeters.meter_count), else_=0))
        ]
        
        c_rows = q.with_entities(*entities).group_by(DefectiveMeters.meter_category, DefectiveMeters.new_meter_type).all()
        
        p_entities = [DefectiveMeters.period_value] + entities
        p_rows = q.with_entities(*p_entities).group_by(DefectiveMeters.period_value, DefectiveMeters.meter_category, DefectiveMeters.new_meter_type).all()
        
        val_keys = ["meter_burnt", "meter_faulty", "others"]
        
        return {
            "total_defective": int(sum(r[2]+r[3]+r[4] for r in c_rows) or 0),
            "total_burnt": int(sum(r[2] for r in c_rows) or 0),
            "total_faulty": int(sum(r[3] for r in c_rows) or 0),
            "category_breakdown": self._format_nested_breakdown(c_rows, val_keys),
            "period_breakdown": self._format_nested_breakdown(p_rows, val_keys)
        }


