import math
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, case
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
class SQLAlchemyMIRepository(IMIRepository):
    def __init__(self, session: Session):
        self.session = session

    def _apply_filters(self, query, model, params: dict):
        """Standard filtering logic moved from routes to repository."""
        fields = [
            "discom", "zone", "circle", "division", "subdivision",
            "substation", "feeder", "dtr", "meter_category", "new_meter_type", "project",
            "period_type", "period_value",
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

    def _period_value_as_date(self, model, period_type: str):
        """
        Convert string period_value into a DATE for reliable filtering/ordering.
        - daily/weekly: typically 'DD-MM-YY'
        - monthly: may be 'DD-MM-YY' (month start) or 'YYYY-MM' depending on pipeline version
        """
        period_type = (period_type or "").lower()
        if period_type == "monthly":
            return case(
                (func.length(model.period_value) == 7, func.to_date(func.concat(model.period_value, "-01"), "YYYY-MM-DD")),
                else_=func.to_date(model.period_value, "DD-MM-YY"),
            )
        # as_on, daily, weekly, and other DD-MM-YY buckets
        return func.to_date(model.period_value, "DD-MM-YY")

    def get_mi_progress_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dashboard-optimized MI Progress response:
        - cumulative totals + meter_type breakdown
        - trend series (per period)
        - comparison bars (clustered by selected level)
        """
        duration = (filters.get("duration") or filters.get("period") or "daily").lower()
        level = (filters.get("level") or "discom").lower()
        project = (filters.get("project") or "all").lower()
        category = (filters.get("category") or "total").lower()

        category_map = {"consumer": "CONSUMER", "feeder": "FEEDER", "dt": "DT"}
        meter_category = category_map.get(category)  # None for "total"

        # Build base query (avoid legacy string-based period filtering)
        base_filters = dict(filters)
        start_date = base_filters.pop("start_date", None)
        end_date = base_filters.pop("end_date", None)
        base_filters.pop("duration", None)
        base_filters.pop("period", None)
        base_filters.pop("level", None)
        base_filters.pop("category", None)
        # Handled with custom logic below (project=all / scoped projects)
        base_filters.pop("project", None)

        q = self.session.query(MIProgress)
        q = self._apply_filters(q, MIProgress, base_filters)
        q = q.filter(MIProgress.period_type == duration)

        # Project scope
        default_projects = ["AGRA", "KASHI", "TRIVENI"]
        if project == "all" or not project:
            q = q.filter(func.upper(func.trim(MIProgress.project)).in_(default_projects))
        else:
            q = q.filter(func.upper(func.trim(MIProgress.project)) == project.upper())

        # Category scope
        if meter_category:
            q = q.filter(func.upper(func.trim(MIProgress.meter_category)) == meter_category)
        else:
            q = q.filter(func.upper(func.trim(MIProgress.meter_category)).in_(list(category_map.values())))

        # Strict date filtering (period_value -> date)
        pv_date = self._period_value_as_date(MIProgress, duration)
        if start_date:
            q = q.filter(pv_date >= func.to_date(start_date, "YYYY-MM-DD"))
        if end_date:
            q = q.filter(pv_date <= func.to_date(end_date, "YYYY-MM-DD"))

        # 1) Cumulative total + meter_type breakdown
        total = q.with_entities(func.sum(MIProgress.total_mi_progress)).scalar() or 0

        breakdown_rows = q.with_entities(
            MIProgress.meter_category,
            MIProgress.new_meter_type,
            func.sum(MIProgress.total_mi_progress),
        ).group_by(MIProgress.meter_category, MIProgress.new_meter_type).all()
        category_breakdown = self._format_nested_breakdown(breakdown_rows, ["count"])

        # 2) Trend (period -> category totals)
        trend_rows = q.with_entities(
            MIProgress.period_value,
            MIProgress.meter_category,
            func.sum(MIProgress.total_mi_progress),
        ).group_by(MIProgress.period_value, MIProgress.meter_category).order_by(pv_date.asc()).all()

        trend_map: Dict[str, Dict[str, int]] = {}
        for period_value, cat, cnt in trend_rows:
            pv = str(period_value)
            c = str(cat) if cat is not None else "Unknown"
            trend_map.setdefault(pv, {"CONSUMER": 0, "FEEDER": 0, "DT": 0})
            if c in trend_map[pv]:
                trend_map[pv][c] += int(cnt or 0)

        trend = [{"period_value": pv, **vals} for pv, vals in trend_map.items()]

        # 3) Comparison bars - with category breakdown (CONSUMER, FEEDER, DT)
        # Build a map: label -> {CONSUMER: int, FEEDER: int, DT: int}
        comparison_map: Dict[str, Dict[str, int]] = {}

        # Determine grouping columns based on level and project
        if level == "discom" and project == "all":
            # Special case: compare the 3 projects - group by project only
            group_expr = func.upper(func.trim(MIProgress.project))
        else:
            if not hasattr(MIProgress, level):
                level = "discom"
            level_col = getattr(MIProgress, level)
            if project == "all" and level != "discom":
                # Composite label: "PROJECT | LevelName"
                group_expr = func.concat(func.upper(func.trim(MIProgress.project)), " | ", func.coalesce(level_col, "Unknown"))
            else:
                # Single-level grouping
                group_expr = func.coalesce(level_col, "Unknown")

        # Query including meter_category to get breakdown by category
        q_comp = q.with_entities(
            group_expr.label("label"),
            MIProgress.meter_category,
            func.sum(MIProgress.total_mi_progress).label("count"),
        ).group_by(group_expr, MIProgress.meter_category).order_by("label")

        cmp_rows = q_comp.all()

        # Build pivot structure: label -> {CONSUMER: 0, FEEDER: 0, DT: 0}
        for row in cmp_rows:
            label = row[0]
            category = row[1]  # "CONSUMER", "FEEDER", or "DT"
            cnt = int(row[2] or 0)

            if label not in comparison_map:
                comparison_map[label] = {"CONSUMER": 0, "FEEDER": 0, "DT": 0}

            # Only count known categories; others are ignored
            if category in comparison_map[label]:
                comparison_map[label][category] += cnt

        # Convert map to list of comparison items, with total count
        comparison = [
            {
                "label": label,
                "CONSUMER": vals["CONSUMER"],
                "FEEDER": vals["FEEDER"],
                "DT": vals["DT"],
                "count": vals["CONSUMER"] + vals["FEEDER"] + vals["DT"],
            }
            for label, vals in sorted(comparison_map.items())
        ]

        return {
            "total_progress": int(total),
            "category_breakdown": category_breakdown,
            "trend": trend,
            "comparison": comparison,
        }

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

    def _format_funnel_breakdown(self, rows, value_keys: list):
        """
        Transform flat rows (category, meter_type, v1, v2, ...) into nested dict:
        { category: { meter_type: {key: value}, ... }, total: {key: sum} }
        """
        res = {}
        for r in rows:
            num_vals = len(value_keys)
            num_groups = len(r) - num_vals  # should be 2: category, meter_type
            keys = [str(x) if x is not None else "Unknown" for x in r[:num_groups]]
            vals = [int(v or 0) for v in r[num_groups:]]
            cat, met = keys[0], keys[1]
            if cat not in res:
                res[cat] = {"total": {k: 0 for k in value_keys}}
            if met not in res[cat]:
                res[cat][met] = {k: 0 for k in value_keys}
            for j, vk in enumerate(value_keys):
                val = vals[j]
                res[cat][met][vk] += val
                res[cat]["total"][vk] += val
        return res


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
        from datetime import datetime
        
        # Extract special parameters
        level = (filters.pop("level", None) or "discom").lower()
        project = (filters.pop("project", None) or "all").lower()
        duration = (filters.get("duration") or filters.get("period") or "daily").lower()
        category_param = (filters.pop("category", None) or filters.pop("meter_category", None) or "total").lower()
        category_map = {"consumer": "CONSUMER", "feeder": "FEEDER", "dt": "DT"}
        meter_category = category_map.get(category_param)
        start_date = filters.pop("start_date", None)
        end_date = filters.pop("end_date", None)
        is_pace_vs_stock = filters.pop("is_pace_vs_stock", False)

        q = self.session.query(InventoryUtilization)
        q = self._apply_filters(q, InventoryUtilization, filters)
        
        # We must filter by a single period_type to avoid double-counting
        valid_duration = duration if duration in ["daily", "weekly", "monthly"] else "daily"
        q = q.filter(InventoryUtilization.period_type == valid_duration)

        # Apply project scope
        default_projects = ["AGRA", "KASHI", "TRIVENI"]
        if project == "all":
            q = q.filter(func.upper(func.trim(InventoryUtilization.project)).in_(default_projects))
        else:
            q = q.filter(func.upper(func.trim(InventoryUtilization.project)) == project.upper())

        # Apply category scope
        if meter_category is not None:
            q = q.filter(func.upper(func.trim(InventoryUtilization.meter_category)) == meter_category)

        # Date filtering using period_value -> date conversion
        pv_date = self._period_value_as_date(InventoryUtilization, valid_duration)
        if start_date:
            q = q.filter(pv_date >= func.to_date(start_date, "YYYY-MM-DD"))
        if end_date:
            q = q.filter(pv_date <= func.to_date(end_date, "YYYY-MM-DD"))

        # 1. Aggregate the main totals
        res = q.with_entities(
            func.sum(InventoryUtilization.total_inventory),
            func.sum(InventoryUtilization.total_installed),
            func.sum(InventoryUtilization.remaining_stock)
        ).first()
        
        total_inv = int(res[0] or 0)
        total_inst = int(res[1] or 0)
        rem_stock = int(res[2] or 0)
        util_rate = (total_inst / total_inv * 100) if total_inv > 0 else 0.0
        
        # Define fields to extract for breakdowns based on whether it is pace_vs_stock or not
        breakdown_keys = ["total_inventory", "total_installed", "remaining_stock" if is_pace_vs_stock else "utilization_rate_pct"]
        
        # Helper to compute utilization_rate_pct for dicts
        def add_computed_fields(tree):
            if isinstance(tree, dict):
                if "total_inventory" in tree and "total_installed" in tree:
                    inv = tree["total_inventory"]
                    inst = tree["total_installed"]
                    if not is_pace_vs_stock:
                        tree["utilization_rate_pct"] = round(float(inst / inv * 100), 2) if inv > 0 else 0.0
                    else:
                        tree["remaining_stock"] = max(0, inv - inst)
                for k, v in tree.items():
                    if isinstance(v, dict):
                        add_computed_fields(v)

        # 2. Nested Category Breakdown (No period)
        cat_rows = q.with_entities(
            InventoryUtilization.meter_category,
            InventoryUtilization.new_meter_type,
            func.sum(InventoryUtilization.total_inventory),
            func.sum(InventoryUtilization.total_installed)
        ).group_by(InventoryUtilization.meter_category, InventoryUtilization.new_meter_type).all()
        
        category_breakdown = self._format_nested_breakdown(cat_rows, ["total_inventory", "total_installed"])
        add_computed_fields(category_breakdown)
        
        # 3. Nested Period Breakdown (Trend)
        per_rows = q.with_entities(
            InventoryUtilization.period_value,
            InventoryUtilization.meter_category,
            InventoryUtilization.new_meter_type,
            func.sum(InventoryUtilization.total_inventory),
            func.sum(InventoryUtilization.total_installed)
        ).group_by(InventoryUtilization.period_value, InventoryUtilization.meter_category, InventoryUtilization.new_meter_type).all()
        
        # Sort periods chronologically in Python just like MIvsSAT
        def period_sort_key(row):
            label = row[0]
            try:
                if valid_duration == "monthly" and len(str(label)) == 7:
                    return datetime.strptime(str(label), "%Y-%m").date()
                elif len(str(label)) == 8: # DD-MM-YY
                    return datetime.strptime(str(label), "%d-%m-%y").date()
                elif len(str(label)) == 10: # YYYY-MM-DD
                    return datetime.strptime(str(label), "%Y-%m-%d").date()
                return datetime.strptime(str(label), "%d-%m-%y").date()
            except Exception:
                return datetime.min.date()
                
        per_rows = sorted(per_rows, key=period_sort_key)
        period_breakdown = self._format_nested_breakdown(per_rows, ["total_inventory", "total_installed"])
        add_computed_fields(period_breakdown)

        # 4. Comparison Array
        comparison: List[Dict[str, Any]] = []
        comparison_map: Dict[str, Dict[str, Dict[str, int]]] = {}

        if level == "discom" and project == "all":
            group_expr = func.upper(func.trim(InventoryUtilization.project))
        else:
            if not hasattr(InventoryUtilization, level):
                group_expr = func.upper(func.trim(InventoryUtilization.project))
            else:
                level_col = getattr(InventoryUtilization, level)
                if project == "all" and level != "discom":
                    group_expr = func.concat(func.upper(func.trim(InventoryUtilization.project)), " | ", func.coalesce(level_col, "Unknown"))
                else:
                    group_expr = func.coalesce(level_col, "Unknown")
                    
        comp_rows = q.with_entities(
            group_expr.label("label"),
            InventoryUtilization.meter_category,
            func.sum(InventoryUtilization.total_inventory),
            func.sum(InventoryUtilization.total_installed),
        ).group_by(group_expr, InventoryUtilization.meter_category).order_by("label").all()

        for row in comp_rows:
            label = row[0]
            category = str(row[1]).upper() if row[1] else "UNKNOWN"
            inv_val = int(row[2] or 0)
            inst_val = int(row[3] or 0)

            if label not in comparison_map:
                comparison_map[label] = {
                    "CONSUMER": {"inv": 0, "inst": 0},
                    "FEEDER": {"inv": 0, "inst": 0},
                    "DT": {"inv": 0, "inst": 0},
                }

            if category in comparison_map[label]:
                comparison_map[label][category]["inv"] += inv_val
                comparison_map[label][category]["inst"] += inst_val

        for label, cats in sorted(comparison_map.items()):
            c_inv = cats["CONSUMER"]["inv"] + cats["FEEDER"]["inv"] + cats["DT"]["inv"]
            c_inst = cats["CONSUMER"]["inst"] + cats["FEEDER"]["inst"] + cats["DT"]["inst"]
            
            comp_item = {
                "label": label,
                "total_inventory": c_inv,
                "total_installed": c_inst,
                "CONSUMER": cats["CONSUMER"]["inst"],
                "FEEDER": cats["FEEDER"]["inst"],
                "DT": cats["DT"]["inst"],
            }
            if is_pace_vs_stock:
                comp_item["remaining_stock"] = max(0, c_inv - c_inst)
            else:
                comp_item["utilization_rate_pct"] = round(float(c_inst / c_inv * 100), 2) if c_inv > 0 else 0.0
            comparison.append(comp_item)

        return {
            "total_inventory": total_inv,
            "total_installed": total_inst,
            "utilization_rate_pct": round(float(util_rate), 2),
            "remaining_stock": rem_stock,
            "category_breakdown": category_breakdown, 
            "period_breakdown": period_breakdown,
            "comparison": comparison
        }



    def get_mi_vs_sat(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        q = self.session.query(MIvsSAT)
        q = self._apply_filters(q, MIvsSAT, filters)
        return q.offset(offset).limit(limit).all()

    def get_mi_vs_sat_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        from sqlalchemy import func
        from datetime import datetime

        # Extract special parameters (same pattern as get_mi_progress_dashboard)
        level = (filters.pop("level", None) or "discom").lower()
        project = (filters.pop("project", None) or "all").lower()
        duration = (filters.get("duration") or filters.get("period") or "daily").lower()
        # Category handling: support both 'category' and 'meter_category' keys
        category_param = (filters.pop("category", None) or filters.pop("meter_category", None) or "total").lower()
        category_map = {"consumer": "CONSUMER", "feeder": "FEEDER", "dt": "DT"}
        meter_category = category_map.get(category_param)  # None for "total" or unknown
        start_date = filters.pop("start_date", None)
        end_date = filters.pop("end_date", None)

        # Build base query with remaining geo/dim filters
        q = self.session.query(MIvsSAT)
        q = self._apply_filters(q, MIvsSAT, filters)
        # Note: MIvsSAT table only stores daily period_type; duration is used only for aggregation grouping

        # Project scope
        default_projects = ["AGRA", "KASHI", "TRIVENI"]
        if project == "all":
            q = q.filter(func.upper(func.trim(MIvsSAT.project)).in_(default_projects))
        else:
            q = q.filter(func.upper(func.trim(MIvsSAT.project)) == project.upper())

        # Category filter
        if meter_category is not None:
            q = q.filter(func.upper(func.trim(MIvsSAT.meter_category)) == meter_category)

        # Date filtering using period_value -> date conversion
        pv_date = self._period_value_as_date(MIvsSAT, duration)
        if start_date:
            q = q.filter(pv_date >= func.to_date(start_date, "YYYY-MM-DD"))
        if end_date:
            q = q.filter(pv_date <= func.to_date(end_date, "YYYY-MM-DD"))

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
        pct = round((t_sat / t_mi * 100), 2) if t_mi > 0 else 0.0

        # 2. Nested Category Breakdown (include all SAT stages)
        sat_keys = ["total_mi", "total_sat", "sat_1", "sat_2", "sat_3", "sat_4", "sat_5", "sat_6", "sat_7", "sat_8", "sat_9"]
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

        # 3. Nested Period Breakdown (Trend) - aggregate by duration
        period_keys = ["total_sat", "sat_1", "sat_2", "sat_3", "sat_4", "sat_5", "sat_6", "sat_7", "sat_8", "sat_9"]

        # Determine period grouping expression based on duration
        # All durations use DD-MM-YY format for period_value (start of period)
        if duration == "monthly":
            period_label_expr = func.to_char(func.date_trunc('month', pv_date), 'DD-MM-YY')
        elif duration == "weekly":
            period_label_expr = func.to_char(func.date_trunc('week', pv_date), 'DD-MM-YY')
        else:  # daily
            period_label_expr = MIvsSAT.period_value

        per_rows = q.with_entities(
            period_label_expr.label("period_label"),
            MIvsSAT.meter_category,
            MIvsSAT.new_meter_type,
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
        ).group_by(period_label_expr, MIvsSAT.meter_category, MIvsSAT.new_meter_type).all()

        # Sort periods chronologically in Python (all duration formats now use DD-MM-YY)
        def period_sort_key(row):
            label = row[0]
            try:
                return datetime.strptime(label, "%d-%m-%y").date()
            except Exception:
                return datetime.min.date()

        per_rows = sorted(per_rows, key=period_sort_key)
        per_rows_transformed = [(row[0], row[1], row[2]) + row[3:] for row in per_rows]
        period_breakdown = self._format_nested_breakdown(per_rows_transformed, period_keys)

        # 4. Build Comparison array (grouped by level/project, with category splits)
        comparison: List[Dict[str, Any]] = []
        comparison_map: Dict[str, Dict[str, Dict[str, int]]] = {}

        # Determine grouping
        if level == "discom" and project == "all":
            group_expr = func.upper(func.trim(MIvsSAT.project))
        else:
            if not hasattr(MIvsSAT, level):
                group_expr = func.upper(func.trim(MIvsSAT.project))
            else:
                level_col = getattr(MIvsSAT, level)
                if project == "all" and level != "discom":
                    group_expr = func.concat(func.upper(func.trim(MIvsSAT.project)), " | ", func.coalesce(level_col, "Unknown"))
                else:
                    group_expr = func.coalesce(level_col, "Unknown")

        comp_rows = q.with_entities(
            group_expr.label("label"),
            MIvsSAT.meter_category,
            func.sum(MIvsSAT.total_mi).label("total_mi"),
            func.sum(MIvsSAT.total_sat).label("total_sat"),
        ).group_by(group_expr, MIvsSAT.meter_category).order_by("label").all()

        # Build pivot
        for row in comp_rows:
            label = row[0]
            category = row[1]
            mi_val = int(row[2] or 0)
            sat_val = int(row[3] or 0)

            if label not in comparison_map:
                comparison_map[label] = {
                    "CONSUMER": {"mi": 0, "sat": 0},
                    "FEEDER": {"mi": 0, "sat": 0},
                    "DT": {"mi": 0, "sat": 0},
                }

            if category in comparison_map[label]:
                comparison_map[label][category]["mi"] += mi_val
                comparison_map[label][category]["sat"] += sat_val

        # Convert to list
        for label, cats in sorted(comparison_map.items()):
            total_mi = cats["CONSUMER"]["mi"] + cats["FEEDER"]["mi"] + cats["DT"]["mi"]
            total_sat = cats["CONSUMER"]["sat"] + cats["FEEDER"]["sat"] + cats["DT"]["sat"]
            pct_val = round((total_sat / total_mi * 100), 2) if total_mi > 0 else 0.0

            comparison.append({
                "label": label,
                "CONSUMER": cats["CONSUMER"]["mi"],
                "FEEDER": cats["FEEDER"]["mi"],
                "DT": cats["DT"]["mi"],
                "total_mi": total_mi,
                "total_sat": total_sat,
                "sat_progress_pct": pct_val,
            })

        return {
            "total_mi": t_mi,
            "total_sat": t_sat,
            "sat_progress_pct": pct,
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
            "period_breakdown": period_breakdown,
            "comparison": comparison,
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

    def get_stock_ageing_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        duration = (filters.get("duration") or "monthly").lower()
        level = (filters.get("level") or "discom").lower()
        project = (filters.get("project") or "all").lower()
        
        base_filters = dict(filters)
        start_date = base_filters.pop("start_date", None)
        end_date = base_filters.pop("end_date", None)
        base_filters.pop("duration", None)
        base_filters.pop("level", None)
        base_filters.pop("project", None)
        
        q = self.session.query(StockAgeing)
        q = self._apply_filters(q, StockAgeing, base_filters)
        
        valid_duration = duration if duration in ["daily", "weekly", "monthly"] else "monthly"
        q = q.filter(StockAgeing.period_type == valid_duration)

        default_projects = ["AGRA", "KASHI", "TRIVENI"]
        if project == "all":
            q = q.filter(func.upper(func.trim(StockAgeing.project)).in_(default_projects))
        else:
            q = q.filter(func.upper(func.trim(StockAgeing.project)) == project.upper())

        pv_date = self._period_value_as_date(StockAgeing, valid_duration)
        if start_date:
            q = q.filter(pv_date >= func.to_date(start_date, "YYYY-MM-DD"))
        if end_date:
            q = q.filter(pv_date <= func.to_date(end_date, "YYYY-MM-DD"))

        # 1. Total
        res = q.with_entities(
            func.sum(StockAgeing.age_0_30),
            func.sum(StockAgeing.age_31_60),
            func.sum(StockAgeing.age_61_90),
            func.sum(StockAgeing.age_90_plus)
        ).first()

        s0 = int(res[0] or 0)
        s31 = int(res[1] or 0)
        s61 = int(res[2] or 0)
        s90 = int(res[3] or 0)
        total_stock = s0 + s31 + s61 + s90

        # 2. Category Breakdown
        c_rows = q.with_entities(
            StockAgeing.meter_category,
            StockAgeing.new_meter_type,
            func.sum(StockAgeing.age_0_30),
            func.sum(StockAgeing.age_31_60),
            func.sum(StockAgeing.age_61_90),
            func.sum(StockAgeing.age_90_plus)
        ).group_by(StockAgeing.meter_category, StockAgeing.new_meter_type).all()
        
        vals = ["age_0_30", "age_31_60", "age_61_90", "age_90_plus"]
        category_breakdown = self._format_nested_breakdown(c_rows, vals)

        def add_total(node):
            if isinstance(node, dict):
                if 'age_0_30' in node:
                    node['total'] = node.get('age_0_30', 0) + node.get('age_31_60', 0) + node.get('age_61_90', 0) + node.get('age_90_plus', 0)
                for v in node.values():
                    if isinstance(v, dict):
                        add_total(v)
        add_total(category_breakdown)

        # 3. Period Breakdown (Trend)
        p_rows = q.with_entities(
            StockAgeing.period_value,
            func.sum(StockAgeing.age_0_30),
            func.sum(StockAgeing.age_31_60),
            func.sum(StockAgeing.age_61_90),
            func.sum(StockAgeing.age_90_plus)
        ).group_by(StockAgeing.period_value).all()
        
        from datetime import datetime
        def period_sort_key(row):
            label = row[0]
            try:
                if valid_duration == "monthly" and len(str(label)) == 7:
                    return datetime.strptime(str(label), "%Y-%m").date()
                elif len(str(label)) == 8: # DD-MM-YY
                    return datetime.strptime(str(label), "%d-%m-%y").date()
                elif len(str(label)) == 10: # YYYY-MM-DD
                    return datetime.strptime(str(label), "%Y-%m-%d").date()
                return datetime.strptime(str(label), "%d-%m-%y").date()
            except Exception:
                return datetime.min.date()
                
        p_rows = sorted(p_rows, key=period_sort_key)
        period_breakdown = []
        for r in p_rows:
            a0, a31, a61, a90 = int(r[1] or 0), int(r[2] or 0), int(r[3] or 0), int(r[4] or 0)
            period_breakdown.append({
                "period_value": str(r[0]),
                "age_0_30": a0, "age_31_60": a31, "age_61_90": a61, "age_90_plus": a90,
                "total_stock": a0 + a31 + a61 + a90
            })

        # 4. Comparison
        if level == "discom" and project == "all":
            group_expr = func.upper(func.trim(StockAgeing.project))
        else:
            if not hasattr(StockAgeing, level):
                group_expr = func.upper(func.trim(StockAgeing.project))
            else:
                level_col = getattr(StockAgeing, level)
                if project == "all" and level != "discom":
                    group_expr = func.concat(func.upper(func.trim(StockAgeing.project)), " | ", func.coalesce(level_col, "Unknown"))
                else:
                    group_expr = func.coalesce(level_col, "Unknown")
                    
        comp_rows = q.with_entities(
            group_expr.label("label"),
            func.sum(StockAgeing.age_0_30),
            func.sum(StockAgeing.age_31_60),
            func.sum(StockAgeing.age_61_90),
            func.sum(StockAgeing.age_90_plus)
        ).group_by(group_expr).order_by("label").all()

        comparison = []
        for r in comp_rows:
            a0, a31, a61, a90 = int(r[1] or 0), int(r[2] or 0), int(r[3] or 0), int(r[4] or 0)
            comparison.append({
                "label": str(r[0]),
                "age_0_30": a0, "age_31_60": a31, "age_61_90": a61, "age_90_plus": a90,
                "total_stock": a0 + a31 + a61 + a90
            })

        return {
            "total_stock": total_stock,
            "category_breakdown": category_breakdown,
            "period_breakdown": period_breakdown,
            "comparison": comparison
        }

    def get_non_sat_ageing(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        q = self.session.query(NonSATAgeing)
        q = self._apply_filters(q, NonSATAgeing, filters)
        return q.offset(offset).limit(limit).all()

    def get_non_sat_ageing_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        duration = (filters.get("duration") or "daily").lower()
        level = (filters.get("level") or "discom").lower()
        project = (filters.get("project") or "all").lower()
        
        base_filters = dict(filters)
        start_date = base_filters.pop("start_date", None)
        end_date = base_filters.pop("end_date", None)
        base_filters.pop("duration", None)
        base_filters.pop("category", None)
        base_filters.pop("level", None)
        base_filters.pop("project", None)
        
        category_param = (filters.get("category") or filters.get("meter_category") or "total").lower()
        category_map = {"consumer": "CONSUMER", "feeder": "FEEDER", "dt": "DT"}
        meter_category = category_map.get(category_param)
        
        q = self.session.query(NonSATAgeing)
        q = self._apply_filters(q, NonSATAgeing, base_filters)

        default_projects = ["AGRA", "KASHI", "TRIVENI"]
        if project == "all":
            q = q.filter(func.upper(func.trim(NonSATAgeing.project)).in_(default_projects))
        else:
            q = q.filter(func.upper(func.trim(NonSATAgeing.project)) == project.upper())

        if meter_category:
            q = q.filter(func.upper(func.trim(NonSATAgeing.meter_category)) == meter_category)

        if start_date:
            q = q.filter(NonSATAgeing.installation_date >= func.to_date(start_date, "YYYY-MM-DD"))
        if end_date:
            q = q.filter(NonSATAgeing.installation_date <= func.to_date(end_date, "YYYY-MM-DD"))

        total_non_sat = q.count()

        # Category Breakdown
        c_rows = q.with_entities(
            NonSATAgeing.meter_category,
            func.count(NonSATAgeing.meter_serial_number)
        ).group_by(NonSATAgeing.meter_category).all()
        
        category_breakdown = {"CONSUMER": 0, "FEEDER": 0, "DT": 0}
        for r in c_rows:
            cat = str(r[0]).upper() if r[0] else "UNKNOWN"
            cnt = int(r[1] or 0)
            if cat in category_breakdown:
                category_breakdown[cat] += cnt

        # Period Breakdown
        if duration == "monthly":
            p_expr = func.to_char(func.date_trunc('month', NonSATAgeing.installation_date), 'DD-MM-YY')
        elif duration == "weekly":
            p_expr = func.to_char(func.date_trunc('week', NonSATAgeing.installation_date), 'DD-MM-YY')
        else:
            p_expr = func.to_char(NonSATAgeing.installation_date, 'DD-MM-YY')

        p_rows = q.with_entities(
            p_expr.label("period_value"),
            func.sum(case((NonSATAgeing.ageing_days <= 30, 1), else_=0)),
            func.sum(case(((NonSATAgeing.ageing_days > 30) & (NonSATAgeing.ageing_days <= 60), 1), else_=0)),
            func.sum(case(((NonSATAgeing.ageing_days > 60) & (NonSATAgeing.ageing_days <= 90), 1), else_=0)),
            func.sum(case(((NonSATAgeing.ageing_days > 90) & (NonSATAgeing.ageing_days <= 120), 1), else_=0)),
            func.sum(case((NonSATAgeing.ageing_days > 120, 1), else_=0)),
            func.count(NonSATAgeing.meter_serial_number)
        ).group_by(p_expr).all()

        from datetime import datetime
        def period_sort_key_non_sat(row):
            label = row[0]
            try:
                return datetime.strptime(str(label), "%d-%m-%y").date()
            except Exception:
                return datetime.min.date()
                
        p_rows = sorted(p_rows, key=period_sort_key_non_sat)
        period_breakdown = []
        for r in p_rows:
            period_breakdown.append({
                "period_value": str(r[0]),
                "age_0_30": int(r[1] or 0),
                "age_31_60": int(r[2] or 0),
                "age_61_90": int(r[3] or 0),
                "age_91_120": int(r[4] or 0),
                "age_120_plus": int(r[5] or 0),
                "total_non_sat": int(r[6] or 0)
            })

        # Summary calculation
        s_res = q.with_entities(
            func.sum(case((NonSATAgeing.ageing_days <= 30, 1), else_=0)),
            func.sum(case(((NonSATAgeing.ageing_days > 30) & (NonSATAgeing.ageing_days <= 60), 1), else_=0)),
            func.sum(case(((NonSATAgeing.ageing_days > 60) & (NonSATAgeing.ageing_days <= 90), 1), else_=0)),
            func.sum(case(((NonSATAgeing.ageing_days > 90) & (NonSATAgeing.ageing_days <= 120), 1), else_=0)),
            func.sum(case((NonSATAgeing.ageing_days > 120, 1), else_=0)),
            func.count(NonSATAgeing.meter_serial_number)
        ).first()

        summary = {
            "age_0_30": int(s_res[0] or 0),
            "age_31_60": int(s_res[1] or 0),
            "age_61_90": int(s_res[2] or 0),
            "age_91_120": int(s_res[3] or 0),
            "age_120_plus": int(s_res[4] or 0),
            "total_non_sat": int(s_res[5] or 0)
        }

        # Comparison
        if level == "discom" and project == "all":
            group_expr = func.upper(func.trim(NonSATAgeing.project))
        else:
            if not hasattr(NonSATAgeing, level):
                group_expr = func.upper(func.trim(NonSATAgeing.project))
            else:
                level_col = getattr(NonSATAgeing, level)
                if project == "all" and level != "discom":
                    group_expr = func.concat(func.upper(func.trim(NonSATAgeing.project)), " | ", func.coalesce(level_col, "Unknown"))
                else:
                    group_expr = func.coalesce(level_col, "Unknown")
                    
        comp_rows = q.with_entities(
            group_expr.label("label"),
            NonSATAgeing.meter_category,
            func.sum(case((NonSATAgeing.ageing_days <= 30, 1), else_=0)),
            func.sum(case(((NonSATAgeing.ageing_days > 30) & (NonSATAgeing.ageing_days <= 60), 1), else_=0)),
            func.sum(case(((NonSATAgeing.ageing_days > 60) & (NonSATAgeing.ageing_days <= 90), 1), else_=0)),
            func.sum(case(((NonSATAgeing.ageing_days > 90) & (NonSATAgeing.ageing_days <= 120), 1), else_=0)),
            func.sum(case((NonSATAgeing.ageing_days > 120, 1), else_=0)),
            func.count(NonSATAgeing.meter_serial_number)
        ).group_by(group_expr, NonSATAgeing.meter_category).order_by("label").all()

        comparison_map = {}
        for r in comp_rows:
            label = str(r[0])
            cat = str(r[1]).upper() if r[1] else "UNKNOWN"
            a0_30 = int(r[2] or 0)
            a31_60 = int(r[3] or 0)
            a61_90 = int(r[4] or 0)
            a91_120 = int(r[5] or 0)
            a120_p = int(r[6] or 0)
            cnt = int(r[7] or 0)

            if label not in comparison_map:
                comparison_map[label] = {
                    "CONSUMER": 0, "FEEDER": 0, "DT": 0,
                    "age_0_30": 0, "age_31_60": 0, "age_61_90": 0, "age_91_120": 0, "age_120_plus": 0, "total_non_sat": 0
                }
            
            if cat in ("CONSUMER", "FEEDER", "DT"):
                comparison_map[label][cat] += cnt
            
            comparison_map[label]["age_0_30"] += a0_30
            comparison_map[label]["age_31_60"] += a31_60
            comparison_map[label]["age_61_90"] += a61_90
            comparison_map[label]["age_91_120"] += a91_120
            comparison_map[label]["age_120_plus"] += a120_p
            comparison_map[label]["total_non_sat"] += cnt
                
        comparison = []
        for label, data in sorted(comparison_map.items()):
            comparison.append({
                "label": label,
                "CONSUMER": data["CONSUMER"],
                "FEEDER": data["FEEDER"],
                "DT": data["DT"],
                "count": data["total_non_sat"],
                "age_0_30": data["age_0_30"],
                "age_31_60": data["age_31_60"],
                "age_61_90": data["age_61_90"],
                "age_91_120": data["age_91_120"],
                "age_120_plus": data["age_120_plus"],
                "total_non_sat": data["total_non_sat"]
            })

        return {
            "total_non_sat": total_non_sat,
            "category_breakdown": category_breakdown,
            "summary": summary,
            "period_breakdown": period_breakdown,
            "comparison": comparison
        }

    def get_meter_journey(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        q = self.session.query(MeterJourneyAvgTime)
        q = self._apply_filters(q, MeterJourneyAvgTime, filters)
        return q.offset(offset).limit(limit).all()

    def _mj_whole_days(self, v) -> Optional[int]:
        """Journey day metrics: always round up partial days (``int(math.ceil(float(v)))``)."""
        if v is None:
            return None
        try:
            return int(math.ceil(float(v)))
        except (TypeError, ValueError):
            return None

    def _mj_weighted_stage(self, col, weight_col, label: str):
        """Combine fine-grained pre-aggregates: sum(avg_i * n_i) / sum(n_i) over rows where avg_i is not null."""
        num = func.sum(case((col.isnot(None), col * weight_col), else_=0))
        den = func.sum(case((col.isnot(None), weight_col), else_=0))
        return (num / func.nullif(den, 0)).label(label)

    def _mj_dashboard_duration(self, filters: Dict[str, Any]) -> str:
        raw = (filters.get("duration") or filters.get("period") or "daily").lower()
        if "as_on" in raw or "latest_sat" in raw:
            return "daily"
        if raw in ("daily", "weekly", "monthly"):
            return raw
        return "daily"

    def _mj_dashboard_base_query(self, filters: Dict[str, Any]) -> Tuple[Any, str]:
        """
        Filter ``sql_meter_journey_avg_time`` for one ``period_type`` (daily/weekly/monthly),
        plus project/category/geo and optional ``start_date``/``end_date`` on ``period_value``.
        """
        M = MeterJourneyAvgTime
        duration = self._mj_dashboard_duration(filters)
        skip = {
            "duration", "period", "level", "category", "project",
            "start_date", "end_date", "mi_usecase", "limit", "offset",
        }
        fd = {k: v for k, v in filters.items() if k not in skip}
        q = self.session.query(M)
        q = self._apply_filters(q, M, fd)
        q = q.filter(M.period_type == duration)

        project = str(filters.get("project") or "all").lower()
        if project == "all" or not project:
            q = q.filter(func.upper(func.trim(M.project)).in_(["AGRA", "KASHI", "TRIVENI"]))
        else:
            q = q.filter(func.upper(func.trim(M.project)) == project.upper())

        category = str(filters.get("category") or "total").lower()
        category_map = {"consumer": "CONSUMER", "feeder": "FEEDER", "dt": "DT"}
        meter_category = category_map.get(category)
        if meter_category:
            q = q.filter(func.upper(func.trim(M.meter_category)) == meter_category)
        else:
            q = q.filter(func.upper(func.trim(M.meter_category)).in_(list(category_map.values())))

        start_date = filters.get("start_date")
        end_date = filters.get("end_date")
        pv_date = self._period_value_as_date(M, duration)
        if start_date:
            q = q.filter(pv_date >= func.to_date(str(start_date), "YYYY-MM-DD"))
        if end_date:
            q = q.filter(pv_date <= func.to_date(str(end_date), "YYYY-MM-DD"))
        return q, duration

    def _mj_comparison_group_expr(self, M, level: str, project: str):
        """Label expression for comparison bars (matches MI progress dashboard grouping)."""
        level = (level or "discom").lower()
        project = str(project or "all").lower()
        allowed = {"discom", "zone", "circle", "division", "subdivision", "substation", "feeder", "dtr"}
        if level not in allowed:
            level = "discom"
        proj_upper = func.upper(func.trim(M.project))
        if level == "discom" and project == "all":
            return proj_upper
        level_col = getattr(M, level)
        if project == "all" and level != "discom":
            return func.concat(proj_upper, " | ", func.coalesce(level_col, "Unknown"))
        return func.coalesce(level_col, "Unknown")

    def get_meter_journey_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Meter journey dashboard from **pre-aggregated** ``sql_meter_journey_avg_time`` (with ``period_type`` /
        ``period_value`` buckets from ETL).

        **Summary** and **comparison**: weighted stage means over all matching fine-grained rows in the
        selected ``duration`` and optional date range.

        **Trend**: one row per ``period_value`` in that range (same weighting within each period).
        """
        M = MeterJourneyAvgTime
        w = M.meter_count

        q_sum, duration = self._mj_dashboard_base_query(filters)
        summary_row = q_sum.with_entities(
            self._mj_weighted_stage(M.inventory_to_store, w, "inventory_to_store"),
            self._mj_weighted_stage(M.store_to_agency, w, "store_to_agency"),
            self._mj_weighted_stage(M.agency_to_meter_installation, w, "agency_to_meter_installation"),
            self._mj_weighted_stage(M.meter_installation_to_sat, w, "meter_installation_to_sat"),
            self._mj_weighted_stage(M.sat_to_invoice, w, "sat_to_invoice"),
            self._mj_weighted_stage(M.invoice_to_revenue, w, "invoice_to_revenue"),
            self._mj_weighted_stage(M.total_journey, w, "total_journey"),
            func.coalesce(func.sum(w), 0).label("meter_count"),
        ).one()
        summary = self._mj_format_summary_row(summary_row._mapping)

        level = (filters.get("level") or "discom").lower()
        project = str(filters.get("project") or "all").lower()
        grp = self._mj_comparison_group_expr(M, level, project)
        q_cmp, _ = self._mj_dashboard_base_query(filters)
        cmp_rows = q_cmp.with_entities(
            grp.label("label"),
            self._mj_weighted_stage(M.inventory_to_store, w, "inventory_to_store"),
            self._mj_weighted_stage(M.store_to_agency, w, "store_to_agency"),
            self._mj_weighted_stage(M.agency_to_meter_installation, w, "agency_to_meter_installation"),
            self._mj_weighted_stage(M.meter_installation_to_sat, w, "meter_installation_to_sat"),
            self._mj_weighted_stage(M.sat_to_invoice, w, "sat_to_invoice"),
            self._mj_weighted_stage(M.invoice_to_revenue, w, "invoice_to_revenue"),
            self._mj_weighted_stage(M.total_journey, w, "total_journey"),
            func.coalesce(func.sum(w), 0).label("meter_count"),
        ).group_by(grp).order_by(grp).all()
        comparison = [self._mj_format_comparison_row(r._mapping) for r in cmp_rows]

        q_tr, _ = self._mj_dashboard_base_query(filters)
        pv = M.period_value
        trend_rows = q_tr.with_entities(
            pv.label("period_value"),
            self._mj_weighted_stage(M.inventory_to_store, w, "inventory_to_store"),
            self._mj_weighted_stage(M.store_to_agency, w, "store_to_agency"),
            self._mj_weighted_stage(M.agency_to_meter_installation, w, "agency_to_meter_installation"),
            self._mj_weighted_stage(M.meter_installation_to_sat, w, "meter_installation_to_sat"),
            self._mj_weighted_stage(M.sat_to_invoice, w, "sat_to_invoice"),
            self._mj_weighted_stage(M.invoice_to_revenue, w, "invoice_to_revenue"),
            self._mj_weighted_stage(M.total_journey, w, "total_journey"),
            func.coalesce(func.sum(w), 0).label("meter_count"),
        ).group_by(pv).order_by(self._period_value_as_date(M, duration).asc()).all()
        trend = [self._mj_format_trend_row(r._mapping) for r in trend_rows]

        return {"summary": summary, "trend": trend, "comparison": comparison}

    def _mj_format_summary_row(self, row) -> Dict[str, Any]:
        if not row:
            return {
                "inventory_to_store": None,
                "store_to_agency": None,
                "agency_to_meter_installation": None,
                "meter_installation_to_sat": None,
                "sat_to_invoice": None,
                "invoice_to_revenue": None,
                "total_journey": None,
                "meter_count": 0,
            }
        return {
            "inventory_to_store": self._mj_whole_days(row["inventory_to_store"]),
            "store_to_agency": self._mj_whole_days(row["store_to_agency"]),
            "agency_to_meter_installation": self._mj_whole_days(row["agency_to_meter_installation"]),
            "meter_installation_to_sat": self._mj_whole_days(row["meter_installation_to_sat"]),
            "sat_to_invoice": self._mj_whole_days(row["sat_to_invoice"]),
            "invoice_to_revenue": self._mj_whole_days(row["invoice_to_revenue"]),
            "total_journey": self._mj_whole_days(row["total_journey"]),
            "meter_count": int(row["meter_count"] or 0),
        }

    def _mj_format_trend_row(self, row) -> Dict[str, Any]:
        return {
            "period_value": str(row["period_value"] or ""),
            "inventory_to_store": self._mj_whole_days(row["inventory_to_store"]),
            "store_to_agency": self._mj_whole_days(row["store_to_agency"]),
            "agency_to_meter_installation": self._mj_whole_days(row["agency_to_meter_installation"]),
            "meter_installation_to_sat": self._mj_whole_days(row["meter_installation_to_sat"]),
            "sat_to_invoice": self._mj_whole_days(row["sat_to_invoice"]),
            "invoice_to_revenue": self._mj_whole_days(row["invoice_to_revenue"]),
            "total_journey": self._mj_whole_days(row["total_journey"]),
            "meter_count": int(row["meter_count"] or 0),
        }

    def _mj_format_comparison_row(self, row) -> Dict[str, Any]:
        label = row["label"]
        if label is not None:
            label = str(label).strip()
        else:
            label = "Unknown"
        return {
            "label": label,
            "inventory_to_store": self._mj_whole_days(row["inventory_to_store"]),
            "store_to_agency": self._mj_whole_days(row["store_to_agency"]),
            "agency_to_meter_installation": self._mj_whole_days(row["agency_to_meter_installation"]),
            "meter_installation_to_sat": self._mj_whole_days(row["meter_installation_to_sat"]),
            "sat_to_invoice": self._mj_whole_days(row["sat_to_invoice"]),
            "invoice_to_revenue": self._mj_whole_days(row["invoice_to_revenue"]),
            "total_journey": self._mj_whole_days(row["total_journey"]),
            "meter_count": int(row["meter_count"] or 0),
        }

    def _meter_stage_base_query(self, filters: Dict[str, Any]):
        """Filter ``sql_meter_current_stage`` for project/category/geo (no period columns on this table)."""
        M = MeterCurrentStage
        skip = {
            "duration", "period", "level", "category", "project",
            "start_date", "end_date", "mi_usecase", "limit", "offset",
        }
        fd = {k: v for k, v in filters.items() if k not in skip}
        q = self.session.query(M)
        q = self._apply_filters(q, M, fd)

        project = str(filters.get("project") or "all").lower()
        if project == "all" or not project:
            q = q.filter(func.upper(func.trim(M.project)).in_(["AGRA", "KASHI", "TRIVENI"]))
        else:
            q = q.filter(func.upper(func.trim(M.project)) == project.upper())

        category = str(filters.get("category") or "total").lower()
        category_map = {"consumer": "CONSUMER", "feeder": "FEEDER", "dt": "DT"}
        meter_category = category_map.get(category)
        if meter_category:
            q = q.filter(func.upper(func.trim(M.meter_category)) == meter_category)
        else:
            q = q.filter(func.upper(func.trim(M.meter_category)).in_(list(category_map.values())))
        return q

    def get_meter_stage_dashboard(self, filters: Dict[str, Any], limit: int, offset: int) -> Dict[str, Any]:
        """
        Returns pre-aggregated funnel metrics from sql_meter_current_stage.
        Data is at summary grain (one row per geo×type×category), so distribution is all rows.
        """
        M = MeterCurrentStage
        q = self._meter_stage_base_query(filters)

        # Totals across all filtered rows
        totals = q.with_entities(
            func.sum(M.inventory),
            func.sum(M.installed),
            func.sum(M.sat_done),
            func.sum(M.revenue_collected),
        ).first()
        total_inv, total_inst, total_sat, total_rev = [int(x or 0) for x in totals] if totals else [0, 0, 0, 0]

        # Category Breakdown (nested by meter_category → new_meter_type)
        cat_rows = q.with_entities(
            M.meter_category,
            M.new_meter_type,
            func.sum(M.inventory),
            func.sum(M.installed),
            func.sum(M.sat_done),
            func.sum(M.revenue_collected),
        ).group_by(M.meter_category, M.new_meter_type).all()
        category_breakdown = self._format_funnel_breakdown(cat_rows, ["inventory", "installed", "sat_done", "revenue_collected"])

        # Comparison by level (discom/zone/circle/etc.)
        project = str(filters.get("project") or "all").lower()
        level = (filters.get("level") or "discom").lower()
        grp = self._mj_comparison_group_expr(M, level, project)

        # Comparison by level (discom/zone/circle/etc.) — aggregated across all categories
        project = str(filters.get("project") or "all").lower()
        level = (filters.get("level") or "discom").lower()
        grp = self._mj_comparison_group_expr(M, level, project)

        comp_rows = q.with_entities(
            grp.label("label"),
            func.sum(M.inventory).label("inventory"),
            func.sum(M.installed).label("installed"),
            func.sum(M.sat_done).label("sat_done"),
            func.sum(M.revenue_collected).label("revenue_collected"),
        ).group_by("label").order_by("label").all()

        comparison = [
            {
                "label": str(row.label or "Unknown").strip(),
                "inventory": int(row.inventory or 0),
                "installed": int(row.installed or 0),
                "sat_done": int(row.sat_done or 0),
                "revenue_collected": int(row.revenue_collected or 0),
            }
            for row in comp_rows
        ]

        return {
            "inventory": total_inv,
            "installed": total_inst,
            "sat_done": total_sat,
            "revenue_collected": total_rev,
            "category_breakdown": category_breakdown,
            "comparison": comparison,
        }

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
        
        project = str(filters.get("project") or "all").lower()
        level = (filters.get("level") or "discom").lower()
        duration = (filters.get("duration") or filters.get("period") or "monthly").lower()

        base_filters = dict(filters)
        start_date = base_filters.pop("start_date", None)
        end_date = base_filters.pop("end_date", None)
        base_filters.pop("duration", None)
        base_filters.pop("period", None)
        base_filters.pop("level", None)
        base_filters.pop("project", None)
        
        # Handle category alias
        if "category" in base_filters:
            if not base_filters.get("meter_category"):
                base_filters["meter_category"] = base_filters.pop("category")
            else:
                base_filters.pop("category")
        
        q = self._apply_filters(q, MIvsSATvsInvoice, base_filters)

        if project == "all" or not project:
            q = q.filter(func.upper(func.trim(MIvsSATvsInvoice.project)).in_(["AGRA", "KASHI", "TRIVENI"]))
        else:
            q = q.filter(func.upper(func.trim(MIvsSATvsInvoice.project)) == project.upper())

        if start_date:
            q = q.filter(func.to_date(MIvsSATvsInvoice.period_value, "DD-MM-YY") >= func.to_date(str(start_date), "YYYY-MM-DD"))
        if end_date:
            q = q.filter(func.to_date(MIvsSATvsInvoice.period_value, "DD-MM-YY") <= func.to_date(str(end_date), "YYYY-MM-DD"))
            
        p_rows = q.with_entities(
            MIvsSATvsInvoice.period_value,
            MIvsSATvsInvoice.meter_category,
            MIvsSATvsInvoice.new_meter_type,
            func.sum(MIvsSATvsInvoice.total_mi),
            func.sum(MIvsSATvsInvoice.total_sat),
            func.sum(MIvsSATvsInvoice.total_lumpsum_invoice),
            func.sum(MIvsSATvsInvoice.total_pmpm_invoice)
        ).group_by(MIvsSATvsInvoice.period_value, MIvsSATvsInvoice.meter_category, MIvsSATvsInvoice.new_meter_type).all()
        
        c_rows = q.with_entities(
            MIvsSATvsInvoice.meter_category,
            MIvsSATvsInvoice.new_meter_type,
            func.sum(MIvsSATvsInvoice.total_mi),
            func.sum(MIvsSATvsInvoice.total_sat),
            func.sum(MIvsSATvsInvoice.total_lumpsum_invoice),
            func.sum(MIvsSATvsInvoice.total_pmpm_invoice)
        ).group_by(MIvsSATvsInvoice.meter_category, MIvsSATvsInvoice.new_meter_type).all()
        
        # ── Comparison logic ──
        if level == "discom" and project == "all":
            group_expr = func.upper(func.trim(MIvsSATvsInvoice.project))
        else:
            if not hasattr(MIvsSATvsInvoice, level):
                level = "discom"
            level_col = getattr(MIvsSATvsInvoice, level)
            if project == "all" and level != "discom":
                group_expr = func.concat(
                    func.upper(func.trim(MIvsSATvsInvoice.project)),
                    " | ",
                    func.coalesce(level_col, "Unknown")
                )
            else:
                group_expr = func.coalesce(level_col, "Unknown")
        
        cmp_rows = q.with_entities(
            group_expr.label("label"),
            func.sum(MIvsSATvsInvoice.total_mi),
            func.sum(MIvsSATvsInvoice.total_sat),
            func.sum(MIvsSATvsInvoice.total_lumpsum_invoice),
            func.sum(MIvsSATvsInvoice.total_pmpm_invoice)
        ).group_by(group_expr).order_by("label").all()
        
        comparison = []
        for r in cmp_rows:
            comparison.append({
                "label": str(r[0] or "Unknown").strip(),
                "total_mi": int(r[1] or 0),
                "total_sat": int(r[2] or 0),
                "total_lumpsum_invoice": int(r[3] or 0),
                "total_pmpm_invoice": int(r[4] or 0)
            })
            
        vals = ["mi", "sat", "lumpsum_invoice", "pmpm_invoice"]
        
        from datetime import datetime
        def normalize_pb(pb):
            out = {}
            for k, v in pb.items():
                try:
                    dt = datetime.strptime(k, "%d-%m-%y")
                    norm_k = dt.strftime("%Y-%m-%d")
                except:
                    norm_k = k
                out[norm_k] = v
            return out

        pb_raw = self._format_nested_breakdown(p_rows, vals)
        pb = normalize_pb(pb_raw)

        return {
            "total_mi": int(sum(r[2] for r in c_rows) or 0),
            "total_sat": int(sum(r[3] for r in c_rows) or 0),
            "total_lumpsum_invoice": int(sum(r[4] for r in c_rows) or 0),
            "total_pmpm_invoice": int(sum(r[5] for r in c_rows) or 0),
            "period_breakdown": pb,
            "category_breakdown": self._format_nested_breakdown(c_rows, vals),
            "comparison": comparison
        }


    def get_revenue_realized_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """KPI 12: Revenue Realized summary."""
        q = self.session.query(RevenueRealized)

        # Extract special filter params
        project = str(filters.get("project") or "all").lower()
        duration = (filters.get("duration") or filters.get("period") or "all").lower()
        level = (filters.get("level") or "discom").lower()

        # Base filters exclude special keys
        base_filters = {k: v for k, v in filters.items() if k not in ("project", "start_date", "end_date", "duration", "level", "period", "period_type")}
        q = self._apply_filters(q, RevenueRealized, base_filters)

        # Project filter
        default_projects = ["AGRA", "KASHI", "TRIVENI"]
        if project == "all" or not project:
            q = q.filter(func.upper(func.trim(RevenueRealized.project)).in_(default_projects))
        else:
            q = q.filter(func.upper(func.trim(RevenueRealized.project)) == project.upper())

        # Duration (period_type) filter
        if duration != "all":
            q = q.filter(RevenueRealized.period_type == duration)

        # Value keys for breakdowns
        VALUE_KEYS = ['lumpsum_invoice', 'pmpm_invoice', 'lumpsum_collection', 'pmpm_collection']

        # Period breakdown query
        p_rows = q.with_entities(
            RevenueRealized.period_value,
            RevenueRealized.meter_category,
            RevenueRealized.new_meter_type,
            func.sum(RevenueRealized.total_lumpsum_invoice).label('lumpsum_invoice'),
            func.sum(RevenueRealized.total_pmpm_invoice).label('pmpm_invoice'),
            func.sum(RevenueRealized.total_lumpsum_collection).label('lumpsum_collection'),
            func.sum(RevenueRealized.total_pmpm_collection).label('pmpm_collection'),
        ).group_by(
            RevenueRealized.period_value,
            RevenueRealized.meter_category,
            RevenueRealized.new_meter_type
        ).all()

        # Category breakdown query
        c_rows = q.with_entities(
            RevenueRealized.meter_category,
            RevenueRealized.new_meter_type,
            func.sum(RevenueRealized.total_lumpsum_invoice).label('lumpsum_invoice'),
            func.sum(RevenueRealized.total_pmpm_invoice).label('pmpm_invoice'),
            func.sum(RevenueRealized.total_lumpsum_collection).label('lumpsum_collection'),
            func.sum(RevenueRealized.total_pmpm_collection).label('pmpm_collection'),
        ).group_by(
            RevenueRealized.meter_category,
            RevenueRealized.new_meter_type
        ).all()

        # Compute totals from category rows
        total_lumpsum_invoice = sum(r.lumpsum_invoice or 0 for r in c_rows)
        total_pmpm_invoice = sum(r.pmpm_invoice or 0 for r in c_rows)
        total_lumpsum_collection = sum(r.lumpsum_collection or 0 for r in c_rows)
        total_pmpm_collection = sum(r.pmpm_collection or 0 for r in c_rows)

        # Build comparison grouped by level
        if level == "discom" and project == "all":
            group_expr = func.upper(func.trim(RevenueRealized.project))
        else:
            if not hasattr(RevenueRealized, level):
                level = "discom"
            level_col = getattr(RevenueRealized, level)
            if project == "all" and level != "discom":
                group_expr = func.concat(
                    func.upper(func.trim(RevenueRealized.project)),
                    " | ",
                    func.coalesce(level_col, "Unknown"),
                )
            else:
                group_expr = func.coalesce(level_col, "Unknown")

        cmp_rows = (
            q.with_entities(
                group_expr.label("label"),
                func.sum(RevenueRealized.total_lumpsum_invoice).label('lumpsum_invoice'),
                func.sum(RevenueRealized.total_pmpm_invoice).label('pmpm_invoice'),
                func.sum(RevenueRealized.total_lumpsum_collection).label('lumpsum_collection'),
                func.sum(RevenueRealized.total_pmpm_collection).label('pmpm_collection'),
            )
            .group_by(group_expr)
            .order_by("label")
            .all()
        )

        comparison = []
        for r in cmp_rows:
            comparison.append({
                "label": str(r.label) if r.label is not None else "Unknown",
                "count": {
                    "lumpsum_invoice": int(r.lumpsum_invoice or 0),
                    "pmpm_invoice": int(r.pmpm_invoice or 0),
                    "lumpsum_collection": int(r.lumpsum_collection or 0),
                    "pmpm_collection": int(r.pmpm_collection or 0),
                }
            })

        return {
            "total_lumpsum_invoice": int(total_lumpsum_invoice),
            "total_pmpm_invoice": int(total_pmpm_invoice),
            "total_lumpsum_collection": int(total_lumpsum_collection),
            "total_pmpm_collection": int(total_pmpm_collection),
            "category_breakdown": self._format_nested_breakdown(c_rows, VALUE_KEYS),
            "period_breakdown": self._format_nested_breakdown(p_rows, VALUE_KEYS),
            "comparison": comparison,
        }


    def get_revenue_ageing_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """KPI 13: Revenue Ageing summary (category + period breakdown + comparison by cluster)."""
        duration = (filters.get("duration") or filters.get("period") or "as_on").lower()
        if duration in ("as", "ason", "snapshot"):
            duration = "as_on"
        level = (filters.get("level") or "discom").lower()
        project = (filters.get("project") or "all").lower()

        category_map = {"consumer": "CONSUMER", "feeder": "FEEDER", "dt": "DT", "dtr": "DT"}
        cat_raw = (filters.get("category") or "").strip().lower()
        meter_cat_mapped = category_map.get(cat_raw) if cat_raw else None

        base_filters = dict(filters)
        start_date = base_filters.pop("start_date", None)
        end_date = base_filters.pop("end_date", None)
        base_filters.pop("duration", None)
        base_filters.pop("period", None)
        base_filters.pop("level", None)
        base_filters.pop("category", None)
        base_filters.pop("project", None)
        meter_category_param = base_filters.pop("meter_category", None)

        q = self.session.query(RevenueAgeing)
        q = self._apply_filters(q, RevenueAgeing, base_filters)
        q = q.filter(RevenueAgeing.period_type == duration)

        default_projects = ["AGRA", "KASHI", "TRIVENI"]
        if project == "all" or not project:
            q = q.filter(func.upper(func.trim(RevenueAgeing.project)).in_(default_projects))
        else:
            q = q.filter(func.upper(func.trim(RevenueAgeing.project)) == project.upper())

        if meter_cat_mapped:
            q = q.filter(func.upper(func.trim(RevenueAgeing.meter_category)) == meter_cat_mapped)
        elif meter_category_param:
            key = str(meter_category_param).strip().lower()
            mapped = category_map.get(key) or str(meter_category_param).strip().upper()
            q = q.filter(func.upper(func.trim(RevenueAgeing.meter_category)) == mapped)
        # Else: no meter_category filter — do not restrict to CONSUMER/FEEDER/DT only (excludes NULL/DTR/etc.)

        pv_date = self._period_value_as_date(RevenueAgeing, duration)
        if start_date:
            q = q.filter(pv_date >= func.to_date(start_date, "YYYY-MM-DD"))
        if end_date:
            q = q.filter(pv_date <= func.to_date(end_date, "YYYY-MM-DD"))

        p_rows = q.with_entities(
            RevenueAgeing.period_value,
            RevenueAgeing.meter_category,
            RevenueAgeing.new_meter_type,
            func.sum(RevenueAgeing.age_0_30),
            func.sum(RevenueAgeing.age_31_60),
            func.sum(RevenueAgeing.age_61_90),
            func.sum(RevenueAgeing.age_90_plus),
        ).group_by(
            RevenueAgeing.period_value,
            RevenueAgeing.meter_category,
            RevenueAgeing.new_meter_type,
        ).all()

        c_rows = q.with_entities(
            RevenueAgeing.meter_category,
            RevenueAgeing.new_meter_type,
            func.sum(RevenueAgeing.age_0_30),
            func.sum(RevenueAgeing.age_31_60),
            func.sum(RevenueAgeing.age_61_90),
            func.sum(RevenueAgeing.age_90_plus),
        ).group_by(RevenueAgeing.meter_category, RevenueAgeing.new_meter_type).all()

        vals = ["age_0_30", "age_31_60", "age_61_90", "age_90_plus"]
        category_breakdown = self._format_nested_breakdown(c_rows, vals)
        period_breakdown = self._format_nested_breakdown(p_rows, vals)

        if level == "discom" and project == "all":
            group_expr = func.upper(func.trim(RevenueAgeing.project))
        else:
            if not hasattr(RevenueAgeing, level):
                level = "discom"
            level_col = getattr(RevenueAgeing, level)
            if project == "all" and level != "discom":
                group_expr = func.concat(
                    func.upper(func.trim(RevenueAgeing.project)),
                    " | ",
                    func.coalesce(level_col, "Unknown"),
                )
            else:
                group_expr = func.coalesce(level_col, "Unknown")

        cmp_rows = (
            q.with_entities(
                group_expr.label("label"),
                func.sum(RevenueAgeing.age_0_30).label("a0"),
                func.sum(RevenueAgeing.age_31_60).label("a1"),
                func.sum(RevenueAgeing.age_61_90).label("a2"),
                func.sum(RevenueAgeing.age_90_plus).label("a3"),
            )
            .group_by(group_expr)
            .order_by("label")
            .all()
        )

        comparison = []
        for r in cmp_rows:
            a0 = int(r.a0 or 0)
            a1 = int(r.a1 or 0)
            a2 = int(r.a2 or 0)
            a3 = int(r.a3 or 0)
            comparison.append(
                {
                    "label": str(r.label) if r.label is not None else "Unknown",
                    "age_0_30": a0,
                    "age_31_60": a1,
                    "age_61_90": a2,
                    "age_90_plus": a3,
                    "total_pending": a0 + a1 + a2 + a3,
                }
            )

        return {
            "category_breakdown": category_breakdown,
            "period_breakdown": period_breakdown,
            "comparison": comparison,
        }

    def get_defective_meters_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """KPI 14: Defective Meters summary."""
        q = self.session.query(DefectiveMeters)
        
        duration = (filters.get("duration") or filters.get("period") or "monthly").lower()
        level = (filters.get("level") or "discom").lower()
        project = (filters.get("project") or "all").lower()

        base_filters = dict(filters)
        start_date = base_filters.pop("start_date", None)
        end_date = base_filters.pop("end_date", None)
        base_filters.pop("duration", None)
        base_filters.pop("period", None)
        base_filters.pop("level", None)
        base_filters.pop("project", None)
        
        q = self._apply_filters(q, DefectiveMeters, base_filters)
        
        if project == "all" or not project:
            q = q.filter(func.upper(func.trim(DefectiveMeters.project)).in_(["AGRA", "KASHI", "TRIVENI"]))
        else:
            q = q.filter(func.upper(func.trim(DefectiveMeters.project)) == project.upper())

        if start_date:
            q = q.filter(func.to_date(DefectiveMeters.period_value, "DD-MM-YY") >= func.to_date(str(start_date), "YYYY-MM-DD"))
        if end_date:
            q = q.filter(func.to_date(DefectiveMeters.period_value, "DD-MM-YY") <= func.to_date(str(end_date), "YYYY-MM-DD"))
        
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
        category_breakdown = self._format_nested_breakdown(c_rows, val_keys)
        
        from datetime import datetime
        trend_map = {}
        for r in p_rows:
            pv = str(r[0] or "")
            cat = str(r[1] or 'UNKNOWN').upper()
            burnt = int(r[3] or 0)
            faulty = int(r[4] or 0)
            others = int(r[5] or 0)
            total = burnt + faulty + others
            
            if pv not in trend_map:
                try:
                    dt = datetime.strptime(pv, "%d-%m-%y")
                    pv_norm = dt.strftime("%Y-%m-%d")
                    sort_date = dt.date()
                except Exception:
                    pv_norm = pv
                    sort_date = datetime.min.date()
                    
                trend_map[pv] = {
                    "period_value": pv_norm, 
                    "sort_date": sort_date,
                    "CONSUMER": 0, "FEEDER": 0, "DT": 0, 
                    "burnt": 0, "faulty": 0, "others": 0
                }
            
            if cat in trend_map[pv]:
                trend_map[pv][cat] += total
            
            trend_map[pv]["burnt"] += burnt
            trend_map[pv]["faulty"] += faulty
            trend_map[pv]["others"] += others
            
        trend = sorted(list(trend_map.values()), key=lambda x: x.pop("sort_date"))
        
        if level == "discom" and project == "all":
            group_expr = func.upper(func.trim(DefectiveMeters.project))
        else:
            if not hasattr(DefectiveMeters, level):
                level = "discom"
            level_col = getattr(DefectiveMeters, level)
            if project == "all" and level != "discom":
                group_expr = func.concat(
                    func.upper(func.trim(DefectiveMeters.project)),
                    " | ",
                    func.coalesce(level_col, "Unknown")
                )
            else:
                group_expr = func.coalesce(level_col, "Unknown")
                
        cmp_rows = q.with_entities(
            group_expr.label("label"),
            DefectiveMeters.meter_category,
            func.sum(case((DefectiveMeters.defective_type == 'Meter Burnt', DefectiveMeters.meter_count), else_=0)),
            func.sum(case((DefectiveMeters.defective_type == 'Meter Faulty', DefectiveMeters.meter_count), else_=0)),
            func.sum(case((DefectiveMeters.defective_type == 'Others', DefectiveMeters.meter_count), else_=0))
        ).group_by(group_expr, DefectiveMeters.meter_category).order_by("label").all()
        
        comp_map = {}
        for r in cmp_rows:
            label = str(r[0] or "Unknown").strip()
            cat = str(r[1] or "UNKNOWN").upper()
            burnt = int(r[2] or 0)
            faulty = int(r[3] or 0)
            others = int(r[4] or 0)
            total_cat = burnt + faulty + others
            
            if label not in comp_map:
                comp_map[label] = {
                    "label": label,
                    "CONSUMER": 0, "FEEDER": 0, "DT": 0,
                    "burnt": 0, "faulty": 0, "others": 0,
                    "total_defective": 0
                }
            
            if cat in comp_map[label]:
                comp_map[label][cat] += total_cat
                
            comp_map[label]["burnt"] += burnt
            comp_map[label]["faulty"] += faulty
            comp_map[label]["others"] += others
            comp_map[label]["total_defective"] += total_cat
            
        comparison = list(comp_map.values())

        return {
            "total_defective": int(sum(r[2]+r[3]+r[4] for r in c_rows) or 0),
            "total_burnt": int(sum(r[2] for r in c_rows) or 0),
            "total_faulty": int(sum(r[3] for r in c_rows) or 0),
            "total_others": int(sum(r[4] for r in c_rows) or 0),
            "category_breakdown": category_breakdown,
            "trend": trend,
            "comparison": comparison
        }


