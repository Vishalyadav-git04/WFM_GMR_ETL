import math
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from domain.interfaces import IMIRepository
from domain.entities import MIProgressEntity, InventoryUtilizationEntity
from .models import (
    MIProgress,
    InventoryUtilization, StockAgeing, MIvsSAT, NonSATAgeing,
    MeterJourneyAvgTime, MeterCurrentStage,
    MIvsSATvsInvoice, RevenueRealized, RevenueAgeing,
    DefectiveMeters,
    MITechnicianProductivityDashboard,
    DashboardCommandCenter, DashboardCommandCenterTrend, DashboardCommandCenterMilestone
)


# Shared constants for nested-by-meter-type / nested-by-category responses
# (used by KPI 9 — Meter Journey, KPI 10 — Meter Funnel, KPI 13 — Revenue Ageing, etc.).
CONSUMER_SUBCATEGORY_MAP = {
    "1PH-STSM": "1PH-Consumer_meter",
    "NBSM-1PH": "1PH-Consumer_meter",
    "NSM1-PH":  "1PH-Consumer_meter",
    "3PH-STSM": "3PH-Consumer_meter",
    "3PNBLTSM": "3PH-Consumer_meter",
    "NBSM-3PH": "3PH-Consumer_meter",
    "NSM3-PH":  "3PH-Consumer_meter",
    "3LTTOUSM": "3PH-Consumer_meter",
    "HTNBTOUS": "3PH-Consumer_meter",
    "HT-TOUSM": "3PH-Consumer_meter",
    "LT-NBTOUS": "3PH-Consumer_meter",
    "3PLTCTSM": "LTCT-Consumer_meter",
    "HTCTPTSM": "HTCT-Consumer_meter",
}
CONSUMER_SUB_KEYS = [
    "1PH-Consumer_meter",
    "3PH-Consumer_meter",
    "LTCT-Consumer_meter",
    "HTCT-Consumer_meter",
]
CATEGORY_KEYS = ["CONSUMER", "FEEDER", "DT"]

# SAT dashboard split endpoints (`/api/mi/sat-dash/*`) — canonical region keys (lowercase).
SAT_DASH_REGION_KEYS = ("kashi", "agra", "triveni")


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
        CONSUMER_SUBCATEGORY_MAP = {
            "1PH-STSM": "1PH-Consumer_meter",
            "NBSM-1PH": "1PH-Consumer_meter",
            "NSM1-PH": "1PH-Consumer_meter",
            "3PH-STSM": "3PH-Consumer_meter",
            "3PNBLTSM": "3PH-Consumer_meter",
            "NBSM-3PH": "3PH-Consumer_meter",
            "NSM3-PH": "3PH-Consumer_meter",
            "3LTTOUSM": "3PH-Consumer_meter",
            "HTNBTOUS": "3PH-Consumer_meter",
            "HT-TOUSM": "3PH-Consumer_meter",
            "LT-NBTOUS": "3PH-Consumer_meter",
            "3PLTCTSM": "LTCT-Consumer_meter",
            "HTCTPTSM": "HTCT-Consumer_meter",
        }

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
        total_val = q.with_entities(func.sum(MIProgress.total_mi_progress)).scalar() or 0
        total = int(total_val)

        # 2) Trend (period -> category totals)
        trend_rows = q.with_entities(
            MIProgress.period_value,
            MIProgress.meter_category,
            MIProgress.new_meter_type,
            func.sum(MIProgress.total_mi_progress),
        ).group_by(MIProgress.period_value, MIProgress.meter_category, MIProgress.new_meter_type).order_by(pv_date.asc()).all()

        trend_map = {}
        for period_value, cat, meter_type, cnt in trend_rows:
            pv = str(period_value)
            c = str(cat) if cat is not None else "Unknown"
            cnt = int(cnt or 0)
            
            if pv not in trend_map:
                if category == "total":
                    trend_map[pv] = {"period_value": pv, "CONSUMER": 0, "FEEDER": 0, "DT": 0, "total": 0}
                elif category == "consumer":
                    trend_map[pv] = {
                        "period_value": pv, 
                        "total": 0, 
                        "1PH-Consumer_meter": 0,
                        "3PH-Consumer_meter": 0,
                        "LTCT-Consumer_meter": 0,
                        "HTCT-Consumer_meter": 0
                    }
                else: # feeder or dt
                    trend_map[pv] = {"period_value": pv, meter_category: 0}

            if category == "total":
                if c in trend_map[pv] and c != "total" and c != "period_value":
                    trend_map[pv][c] += cnt
                    trend_map[pv]["total"] += cnt
            elif category == "consumer":
                trend_map[pv]["total"] += cnt
            else:
                trend_map[pv][meter_category] += cnt

            if category == "consumer" and c == "CONSUMER":
                sub_cat = CONSUMER_SUBCATEGORY_MAP.get(meter_type)
                if sub_cat in trend_map[pv]:
                    trend_map[pv][sub_cat] += cnt

        trend = list(trend_map.values())

        # 3) Comparison bars - with category breakdown (CONSUMER, FEEDER, DT)
        comparison_map = {}

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
            MIProgress.new_meter_type,
            func.sum(MIProgress.total_mi_progress).label("count"),
        ).group_by(group_expr, MIProgress.meter_category, MIProgress.new_meter_type).order_by("label")

        cmp_rows = q_comp.all()

        # Build pivot structure
        for row in cmp_rows:
            label = row[0]
            cat = row[1]
            meter_type = row[2]
            cnt = int(row[3] or 0)
            c = str(cat) if cat is not None else "Unknown"

            if label not in comparison_map:
                if category == "total":
                    comparison_map[label] = {"label": label, "CONSUMER": 0, "FEEDER": 0, "DT": 0, "total": 0}
                elif category == "consumer":
                    comparison_map[label] = {
                        "label": label, 
                        "total": 0, 
                        "1PH-Consumer_meter": 0,
                        "3PH-Consumer_meter": 0,
                        "LTCT-Consumer_meter": 0,
                        "HTCT-Consumer_meter": 0
                    }
                else: # feeder or dt
                    comparison_map[label] = {"label": label, meter_category: 0}

            if category == "total":
                if c in comparison_map[label] and c != "total" and c != "label":
                    comparison_map[label][c] += cnt
                    comparison_map[label]["total"] += cnt
            elif category == "consumer":
                comparison_map[label]["total"] += cnt
            else:
                comparison_map[label][meter_category] += cnt

            if category == "consumer" and c == "CONSUMER":
                sub_cat = CONSUMER_SUBCATEGORY_MAP.get(meter_type)
                if sub_cat in comparison_map[label]:
                    comparison_map[label][sub_cat] += cnt

        comparison = sorted(list(comparison_map.values()), key=lambda x: x["label"])

        return {
            "total_progress": total,
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

    def get_productivity_team_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        MI Technician Productivity Dashboard (repurposed KPI 2.5 route).
        Mirrors O&M-1 math: compute per-day productivity and average across days
        within each requested bucket/group.
        """
        from sqlalchemy import cast, Float

        duration = (filters.get("duration") or "daily").lower()
        level = (filters.get("level") or "discom").lower()
        project = (filters.get("project") or "all").lower()
        category_param = (filters.get("category") or "total").lower()

        q = self.session.query(MITechnicianProductivityDashboard)

        # Filters (dimensions)
        default_projects = ["AGRA", "KASHI", "TRIVENI"]
        if project and project != "all":
            q = q.filter(func.upper(func.trim(MITechnicianProductivityDashboard.project)) == project.upper())
        else:
            q = q.filter(func.upper(func.trim(MITechnicianProductivityDashboard.project)).in_(default_projects))

        category_map = {"consumer": "CONSUMER", "feeder": "FEEDER", "dt": "DT"}
        meter_category = category_map.get(category_param)
        if meter_category:
            q = q.filter(func.upper(func.trim(MITechnicianProductivityDashboard.meter_category)) == meter_category)

        for field in ["discom", "zone", "circle", "division", "subdivision", "substation", "feeder", "dtr", "new_meter_type"]:
            val = filters.get(field)
            if val:
                q = q.filter(getattr(MITechnicianProductivityDashboard, field).ilike(val))

        start_date = filters.get("start_date")
        end_date = filters.get("end_date")
        if start_date:
            q = q.filter(MITechnicianProductivityDashboard.installation_date >= func.to_date(start_date, "YYYY-MM-DD"))
        if end_date:
            q = q.filter(MITechnicianProductivityDashboard.installation_date <= func.to_date(end_date, "YYYY-MM-DD"))

        # -- Summary (avg of per-day productivity across the filtered range) --
        daily_stats_sq = q.with_entities(
            MITechnicianProductivityDashboard.installation_date.label("installation_date"),
            func.sum(MITechnicianProductivityDashboard.total_installations).label("total_installations"),
            (
                cast(func.sum(MITechnicianProductivityDashboard.total_installations), Float)
                / func.count(func.distinct(MITechnicianProductivityDashboard.technician))
            ).label("daily_prod"),
        ).group_by(MITechnicianProductivityDashboard.installation_date).subquery()

        summary_row = self.session.query(
            func.sum(daily_stats_sq.c.total_installations),
            func.avg(daily_stats_sq.c.daily_prod),
            func.count(daily_stats_sq.c.installation_date),
        ).first()

        total_active_techs = q.with_entities(func.count(func.distinct(MITechnicianProductivityDashboard.technician))).scalar() or 0

        summary = {
            "total_installations": int(summary_row[0] or 0) if summary_row else 0,
            "total_active_technicians": int(total_active_techs),
            "total_active_days": int(summary_row[2] or 0) if summary_row else 0,
            "productivity_per_technician_per_day": round(float(summary_row[1] or 0), 2) if summary_row else 0.0,
        }

        # -- Trend --
        if duration == "daily":
            bucket_expr = func.to_char(MITechnicianProductivityDashboard.installation_date, "YYYY-MM-DD")
        elif duration == "weekly":
            bucket_expr = func.to_char(func.date_trunc("week", MITechnicianProductivityDashboard.installation_date), "YYYY-MM-DD")
        elif duration == "monthly":
            bucket_expr = func.to_char(MITechnicianProductivityDashboard.installation_date, "YYYY-MM")
        else:
            bucket_expr = func.to_char(MITechnicianProductivityDashboard.installation_date, "YYYY-MM-DD")

        bucket_stats = q.with_entities(
            bucket_expr.label("period_label"),
            func.sum(MITechnicianProductivityDashboard.total_installations).label("total_installations"),
            func.count(func.distinct(MITechnicianProductivityDashboard.technician)).label("active_technicians"),
        ).group_by(bucket_expr).all()

        daily_bucket_sq = q.with_entities(
            bucket_expr.label("period_label"),
            MITechnicianProductivityDashboard.installation_date.label("installation_date"),
            (
                cast(func.sum(MITechnicianProductivityDashboard.total_installations), Float)
                / func.count(func.distinct(MITechnicianProductivityDashboard.technician))
            ).label("daily_prod"),
        ).group_by(bucket_expr, MITechnicianProductivityDashboard.installation_date).subquery()

        daily_bucket_avg = self.session.query(
            daily_bucket_sq.c.period_label,
            func.avg(daily_bucket_sq.c.daily_prod),
        ).group_by(daily_bucket_sq.c.period_label).all()
        daily_bucket_avg_dict = {r[0]: r[1] for r in daily_bucket_avg}

        trend = [
            {
                "date": str(r[0]),
                "total_installations": int(r[1] or 0),
                "active_technicians": int(r[2] or 0),
                "productivity_per_technician_per_day": round(float(daily_bucket_avg_dict.get(r[0], 0) or 0), 2),
            }
            for r in bucket_stats
        ]
        trend = sorted(trend, key=lambda x: x["date"])

        # -- Comparison --
        if level in ("divison",):
            level = "division"
        if level in ("subdivison",):
            level = "subdivision"

        valid_levels = {"project", "discom", "zone", "circle", "division", "subdivision"}
        if level not in valid_levels:
            level = "discom"

        if project == "all" and level in ("project", "discom"):
            label_expr = func.upper(func.trim(MITechnicianProductivityDashboard.project))
        else:
            if level == "project":
                level_col = func.upper(func.trim(MITechnicianProductivityDashboard.project))
            else:
                level_col = getattr(MITechnicianProductivityDashboard, level)
            if project == "all" and level not in ("project", "discom"):
                label_expr = func.concat(func.upper(func.trim(MITechnicianProductivityDashboard.project)), " | ", func.coalesce(level_col, "Unknown"))
            else:
                label_expr = func.coalesce(level_col, "Unknown")

        comp_stats = q.with_entities(
            label_expr.label("label"),
            func.sum(MITechnicianProductivityDashboard.total_installations).label("total_installations"),
            func.count(func.distinct(MITechnicianProductivityDashboard.technician)).label("active_technicians"),
        ).group_by(label_expr).all()

        daily_comp_sq = q.with_entities(
            label_expr.label("label"),
            MITechnicianProductivityDashboard.installation_date.label("installation_date"),
            (
                cast(func.sum(MITechnicianProductivityDashboard.total_installations), Float)
                / func.count(func.distinct(MITechnicianProductivityDashboard.technician))
            ).label("daily_prod"),
        ).group_by(label_expr, MITechnicianProductivityDashboard.installation_date).subquery()

        daily_comp_avg = self.session.query(
            daily_comp_sq.c.label,
            func.avg(daily_comp_sq.c.daily_prod),
        ).group_by(daily_comp_sq.c.label).all()
        daily_comp_avg_dict = {r[0]: r[1] for r in daily_comp_avg}

        comparison = [
            {
                "label": str(r[0]) if r[0] is not None else "Unknown",
                "total_installations": int(r[1] or 0),
                "active_technicians": int(r[2] or 0),
                "productivity_per_technician_per_day": round(float(daily_comp_avg_dict.get(r[0], 0) or 0), 2),
            }
            for r in comp_stats
        ]

        # -- Category Breakdown --
        cat_stats = q.with_entities(
            MITechnicianProductivityDashboard.meter_category.label("meter_category"),
            func.sum(MITechnicianProductivityDashboard.total_installations).label("total_installations"),
            func.count(func.distinct(MITechnicianProductivityDashboard.technician)).label("active_technicians"),
        ).group_by(MITechnicianProductivityDashboard.meter_category).all()

        daily_cat_sq = q.with_entities(
            MITechnicianProductivityDashboard.meter_category.label("meter_category"),
            MITechnicianProductivityDashboard.installation_date.label("installation_date"),
            (
                cast(func.sum(MITechnicianProductivityDashboard.total_installations), Float)
                / func.count(func.distinct(MITechnicianProductivityDashboard.technician))
            ).label("daily_prod"),
        ).group_by(MITechnicianProductivityDashboard.meter_category, MITechnicianProductivityDashboard.installation_date).subquery()

        daily_cat_avg = self.session.query(
            daily_cat_sq.c.meter_category,
            func.avg(daily_cat_sq.c.daily_prod),
        ).group_by(daily_cat_sq.c.meter_category).all()
        daily_cat_avg_dict = {r[0]: r[1] for r in daily_cat_avg}

        category_breakdown: Dict[str, Any] = {}
        for r in cat_stats:
            cat = str(r[0]) if r[0] is not None else "Unknown"
            category_breakdown[cat] = {
                "total_installations": int(r[1] or 0),
                "active_technicians": int(r[2] or 0),
                "productivity_per_technician_per_day": round(float(daily_cat_avg_dict.get(r[0], 0) or 0), 2),
            }

        # When category=total, keep the response shape stable for frontend charts
        # by always including the 3 expected categories (even if a category has 0 rows).
        if category_param == "total":
            for expected_cat in ("CONSUMER", "FEEDER", "DT"):
                category_breakdown.setdefault(
                    expected_cat,
                    {
                        "total_installations": 0,
                        "active_technicians": 0,
                        "productivity_per_technician_per_day": 0.0,
                    },
                )

        # -- Insights (top/bottom technicians by avg daily installations) --
        daily_tech_sq = q.with_entities(
            MITechnicianProductivityDashboard.technician.label("technician"),
            MITechnicianProductivityDashboard.installation_date.label("installation_date"),
            func.sum(MITechnicianProductivityDashboard.total_installations).label("daily_installations"),
        ).group_by(MITechnicianProductivityDashboard.technician, MITechnicianProductivityDashboard.installation_date).subquery()

        tech_avg = self.session.query(
            daily_tech_sq.c.technician,
            func.avg(daily_tech_sq.c.daily_installations).label("avg_prod"),
        ).group_by(daily_tech_sq.c.technician).order_by(func.avg(daily_tech_sq.c.daily_installations).desc()).all()

        insights = {"top_performing_technician": {}, "lowest_performing_technician": {}}
        if tech_avg:
            top = tech_avg[0]
            low = tech_avg[-1]
            insights["top_performing_technician"] = {
                "name": top[0],
                "productivity_per_technician_per_day": round(float(top[1] or 0), 2),
            }
            insights["lowest_performing_technician"] = {
                "name": low[0],
                "productivity_per_technician_per_day": round(float(low[1] or 0), 2),
            }

        return {
            "summary": summary,
            "insights": insights,
            "trend": trend,
            "comparison": comparison,
            "category_breakdown": category_breakdown,
        }

    def get_productivity_trend_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        KPI 3.5 — MI Technician Productivity Trend Dashboard.

        Same base logic as KPI 2.5 (avg-of-daily productivity), but rendered in a
        monthly-trend dashboard shape (like O&M-2) and defaults duration=monthly.
        """
        from sqlalchemy import cast, Float

        duration = (filters.get("duration") or "monthly").lower()
        level = (filters.get("level") or "discom").lower()
        project = (filters.get("project") or "all").lower()
        category_param = (filters.get("category") or "total").lower()

        q = self.session.query(MITechnicianProductivityDashboard)

        # Filters (dimensions)
        default_projects = ["AGRA", "KASHI", "TRIVENI"]
        if project and project != "all":
            q = q.filter(func.upper(func.trim(MITechnicianProductivityDashboard.project)) == project.upper())
        else:
            q = q.filter(func.upper(func.trim(MITechnicianProductivityDashboard.project)).in_(default_projects))

        category_map = {"consumer": "CONSUMER", "feeder": "FEEDER", "dt": "DT"}
        meter_category = category_map.get(category_param)
        if meter_category:
            q = q.filter(func.upper(func.trim(MITechnicianProductivityDashboard.meter_category)) == meter_category)

        for field in ["discom", "zone", "circle", "division", "subdivision", "substation", "feeder", "dtr", "new_meter_type"]:
            val = filters.get(field)
            if val:
                q = q.filter(getattr(MITechnicianProductivityDashboard, field).ilike(val))

        start_date = filters.get("start_date")
        end_date = filters.get("end_date")
        if start_date:
            q = q.filter(MITechnicianProductivityDashboard.installation_date >= func.to_date(start_date, "YYYY-MM-DD"))
        if end_date:
            q = q.filter(MITechnicianProductivityDashboard.installation_date <= func.to_date(end_date, "YYYY-MM-DD"))

        # bucket label
        if duration == "daily":
            bucket_expr = func.to_char(MITechnicianProductivityDashboard.installation_date, "YYYY-MM-DD")
        elif duration == "weekly":
            bucket_expr = func.to_char(func.date_trunc("week", MITechnicianProductivityDashboard.installation_date), "YYYY-MM-DD")
        else:
            # monthly default
            bucket_expr = func.to_char(MITechnicianProductivityDashboard.installation_date, "YYYY-MM")

        # daily stats (the KPI 2.5 base)
        daily_sq = q.with_entities(
            bucket_expr.label("bucket"),
            MITechnicianProductivityDashboard.installation_date.label("installation_date"),
            func.sum(MITechnicianProductivityDashboard.total_installations).label("daily_installations"),
            func.count(func.distinct(MITechnicianProductivityDashboard.technician)).label("daily_active_technicians"),
            (
                cast(func.sum(MITechnicianProductivityDashboard.total_installations), Float)
                / func.count(func.distinct(MITechnicianProductivityDashboard.technician))
            ).label("daily_prod"),
        ).group_by(bucket_expr, MITechnicianProductivityDashboard.installation_date).subquery()

        # summary
        summary_row = self.session.query(
            func.sum(daily_sq.c.daily_installations).label("total_installations"),
            func.avg(daily_sq.c.daily_prod).label("avg_daily_prod"),
            func.count(func.distinct(func.to_char(daily_sq.c.installation_date, "YYYY-MM"))).label("active_months"),
        ).first()

        summary = {
            "total_installations": int(summary_row.total_installations or 0) if summary_row else 0,
            "total_active_months": int(summary_row.active_months or 0) if summary_row else 0,
            "productivity_per_technician_per_day": round(float(summary_row.avg_daily_prod or 0), 2) if summary_row else 0.0,
        }

        # trend (one row per bucket)
        trend_rows = self.session.query(
            daily_sq.c.bucket.label("bucket"),
            func.sum(daily_sq.c.daily_installations).label("total_installations"),
            func.count(func.distinct(daily_sq.c.installation_date)).label("active_days"),
            func.avg(daily_sq.c.daily_active_technicians).label("avg_active_technicians"),
            func.avg(daily_sq.c.daily_prod).label("avg_daily_prod"),
        ).group_by(daily_sq.c.bucket).all()

        trend = [
            {
                "month": str(r.bucket),
                "total_installations": int(r.total_installations or 0),
                "active_days": int(r.active_days or 0),
                "avg_active_technicians": round(float(r.avg_active_technicians or 0), 2),
                "productivity_per_technician_per_day": round(float(r.avg_daily_prod or 0), 2),
            }
            for r in trend_rows
        ]
        trend = sorted(trend, key=lambda x: x["month"])

        # comparison label rules (same as KPI 2.5 / KPI 1 conventions)
        if level in ("divison",):
            level = "division"
        if level in ("subdivison",):
            level = "subdivision"

        valid_levels = {"project", "discom", "zone", "circle", "division", "subdivision"}
        if level not in valid_levels:
            level = "discom"

        if project == "all" and level in ("project", "discom"):
            label_expr = func.upper(func.trim(MITechnicianProductivityDashboard.project))
        else:
            if level == "project":
                level_col = func.upper(func.trim(MITechnicianProductivityDashboard.project))
            else:
                level_col = getattr(MITechnicianProductivityDashboard, level)
            if project == "all" and level not in ("project", "discom"):
                label_expr = func.concat(
                    func.upper(func.trim(MITechnicianProductivityDashboard.project)),
                    " | ",
                    func.coalesce(level_col, "Unknown"),
                )
            else:
                label_expr = func.coalesce(level_col, "Unknown")

        daily_comp_sq = q.with_entities(
            label_expr.label("label"),
            MITechnicianProductivityDashboard.installation_date.label("installation_date"),
            func.sum(MITechnicianProductivityDashboard.total_installations).label("daily_installations"),
            func.count(func.distinct(MITechnicianProductivityDashboard.technician)).label("daily_active_technicians"),
            (
                cast(func.sum(MITechnicianProductivityDashboard.total_installations), Float)
                / func.count(func.distinct(MITechnicianProductivityDashboard.technician))
            ).label("daily_prod"),
        ).group_by(label_expr, MITechnicianProductivityDashboard.installation_date).subquery()

        comp_rows = self.session.query(
            daily_comp_sq.c.label,
            func.sum(daily_comp_sq.c.daily_installations).label("total_installations"),
            func.count(func.distinct(daily_comp_sq.c.installation_date)).label("active_days"),
            func.avg(daily_comp_sq.c.daily_active_technicians).label("avg_active_technicians"),
            func.avg(daily_comp_sq.c.daily_prod).label("avg_daily_prod"),
        ).group_by(daily_comp_sq.c.label).all()

        comparison = [
            {
                "label": str(r.label) if r.label is not None else "Unknown",
                "total_installations": int(r.total_installations or 0),
                "active_days": int(r.active_days or 0),
                "avg_active_technicians": round(float(r.avg_active_technicians or 0), 2),
                "productivity_per_technician_per_day": round(float(r.avg_daily_prod or 0), 2),
            }
            for r in comp_rows
        ]

        # category breakdown (optional dashboard slice)
        daily_cat_sq = q.with_entities(
            MITechnicianProductivityDashboard.meter_category.label("meter_category"),
            MITechnicianProductivityDashboard.installation_date.label("installation_date"),
            func.sum(MITechnicianProductivityDashboard.total_installations).label("daily_installations"),
            func.count(func.distinct(MITechnicianProductivityDashboard.technician)).label("daily_active_technicians"),
            (
                cast(func.sum(MITechnicianProductivityDashboard.total_installations), Float)
                / func.count(func.distinct(MITechnicianProductivityDashboard.technician))
            ).label("daily_prod"),
        ).group_by(MITechnicianProductivityDashboard.meter_category, MITechnicianProductivityDashboard.installation_date).subquery()

        cat_rows = self.session.query(
            daily_cat_sq.c.meter_category,
            func.sum(daily_cat_sq.c.daily_installations).label("total_installations"),
            func.count(func.distinct(daily_cat_sq.c.installation_date)).label("active_days"),
            func.avg(daily_cat_sq.c.daily_active_technicians).label("avg_active_technicians"),
            func.avg(daily_cat_sq.c.daily_prod).label("avg_daily_prod"),
        ).group_by(daily_cat_sq.c.meter_category).all()

        category_breakdown: Dict[str, Any] = {
            (str(r.meter_category) if r.meter_category is not None else "Unknown"): {
                "total_installations": int(r.total_installations or 0),
                "active_days": int(r.active_days or 0),
                "avg_active_technicians": round(float(r.avg_active_technicians or 0), 2),
                "productivity_per_technician_per_day": round(float(r.avg_daily_prod or 0), 2),
            }
            for r in cat_rows
        }

        if category_param == "total":
            for expected_cat in ("CONSUMER", "FEEDER", "DT"):
                category_breakdown.setdefault(
                    expected_cat,
                    {
                        "total_installations": 0,
                        "active_days": 0,
                        "avg_active_technicians": 0.0,
                        "productivity_per_technician_per_day": 0.0,
                    },
                )

        return {
            "summary": summary,
            "trend": trend,
            "comparison": comparison,
            "category_breakdown": category_breakdown,
        }

    def get_pace_vs_stock_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self.get_inventory_utilization_summary(filters)

    def get_inventory_utilization_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        from datetime import datetime

        CONSUMER_SUBCATEGORY_MAP = {
            "1PH-STSM": "1PH-Consumer_meter",
            "NBSM-1PH": "1PH-Consumer_meter",
            "NSM1-PH": "1PH-Consumer_meter",
            "3PH-STSM": "3PH-Consumer_meter",
            "3PNBLTSM": "3PH-Consumer_meter",
            "NBSM-3PH": "3PH-Consumer_meter",
            "NSM3-PH": "3PH-Consumer_meter",
            "3LTTOUSM": "3PH-Consumer_meter",
            "HTNBTOUS": "3PH-Consumer_meter",
            "HT-TOUSM": "3PH-Consumer_meter",
            "LT-NBTOUS": "3PH-Consumer_meter",
            "3PLTCTSM": "LTCT-Consumer_meter",
            "HTCTPTSM": "HTCT-Consumer_meter",
        }
        CONSUMER_SUB_KEYS = ["1PH-Consumer_meter", "3PH-Consumer_meter", "LTCT-Consumer_meter", "HTCT-Consumer_meter"]

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

        # Helper: build empty sub-keys dict based on category
        def _empty_sub_keys():
            if category_param == "consumer":
                return {k: {"inventory": 0, "installed": 0} for k in CONSUMER_SUB_KEYS}
            elif category_param == "total":
                return {k: {"inventory": 0, "installed": 0} for k in ("CONSUMER", "FEEDER", "DT")}
            else:
                # feeder or dt — no sub-keys, just use totals
                return {}

        # Helper: get the key name for a given row's meter_category + new_meter_type
        def _category_key(row_cat, row_meter_type):
            cat = str(row_cat).upper() if row_cat else "UNKNOWN"
            if category_param == "consumer" and cat == "CONSUMER":
                return CONSUMER_SUBCATEGORY_MAP.get(row_meter_type)
            elif category_param == "total":
                return cat if cat in ("CONSUMER", "FEEDER", "DT") else None
            else:
                # feeder or dt — no specific sub-key
                return None

        def _nested_bucket_key_order():
            if category_param == "consumer":
                return CONSUMER_SUB_KEYS
            if category_param == "total":
                return ("CONSUMER", "FEEDER", "DT")
            return ()

        def _bucket_output(binv: int, binst: int) -> Dict[str, Any]:
            out: Dict[str, Any] = {"inventory": binv, "installed": binst}
            if is_pace_vs_stock:
                out["remaining_stock"] = max(0, binv - binst)
            else:
                out["utilization_rate_pct"] = (
                    round(float(binst / binv * 100), 2) if binv > 0 else 0.0
                )
            return out

        # 2. Period Breakdown (Flat Array)
        per_rows = q.with_entities(
            InventoryUtilization.period_value,
            InventoryUtilization.meter_category,
            InventoryUtilization.new_meter_type,
            func.sum(InventoryUtilization.total_inventory),
            func.sum(InventoryUtilization.total_installed)
        ).group_by(InventoryUtilization.period_value, InventoryUtilization.meter_category, InventoryUtilization.new_meter_type).all()
        
        # Sort periods chronologically
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

        # Build flat period map
        period_map = {}
        for row in per_rows:
            pv = str(row[0])
            inv_val = int(row[3] or 0)
            inst_val = int(row[4] or 0)

            if pv not in period_map:
                period_map[pv] = {
                    "period_value": pv,
                    "total_inventory": 0,
                    "total_installed": 0,
                    **_empty_sub_keys(),
                }

            period_map[pv]["total_inventory"] += inv_val
            period_map[pv]["total_installed"] += inst_val

            key = _category_key(row[1], row[2])
            if key and key in period_map[pv]:
                period_map[pv][key]["inventory"] += inv_val
                period_map[pv][key]["installed"] += inst_val

        # Reorder and add rate field to each period
        period_breakdown = []
        for pv, item in period_map.items():
            inv = item["total_inventory"]
            inst = item["total_installed"]
            
            ordered_item = {
                "period_value": pv,
                "total_inventory": inv,
                "total_installed": inst,
            }
            
            if is_pace_vs_stock:
                ordered_item["remaining_stock"] = max(0, inv - inst)
            else:
                ordered_item["utilization_rate_pct"] = round(float(inst / inv * 100), 2) if inv > 0 else 0.0

            bucket_keys = _nested_bucket_key_order()
            if bucket_keys:
                for bk in bucket_keys:
                    sub = item[bk]
                    ordered_item[bk] = _bucket_output(sub["inventory"], sub["installed"])
            else:
                for k, v in item.items():
                    if k not in ["period_value", "total_inventory", "total_installed"]:
                        ordered_item[k] = v

            period_breakdown.append(ordered_item)

        # 3. Comparison Array
        if level == "discom" and project == "all":
            group_expr = func.upper(func.trim(InventoryUtilization.project))
        else:
            if not hasattr(InventoryUtilization, level):
                level = "discom"
            level_col = getattr(InventoryUtilization, level)
            if project == "all" and level != "discom":
                group_expr = func.concat(func.upper(func.trim(InventoryUtilization.project)), " | ", func.coalesce(level_col, "Unknown"))
            else:
                group_expr = func.coalesce(level_col, "Unknown")
                    
        comp_rows = q.with_entities(
            group_expr.label("label"),
            InventoryUtilization.meter_category,
            InventoryUtilization.new_meter_type,
            func.sum(InventoryUtilization.total_inventory),
            func.sum(InventoryUtilization.total_installed),
        ).group_by(group_expr, InventoryUtilization.meter_category, InventoryUtilization.new_meter_type).order_by("label").all()

        comparison_map: Dict[str, Dict[str, Any]] = {}
        for row in comp_rows:
            label = row[0]
            inv_val = int(row[3] or 0)
            inst_val = int(row[4] or 0)

            if label not in comparison_map:
                comparison_map[label] = {
                    "label": label,
                    "total_inventory": 0,
                    "total_installed": 0,
                    **_empty_sub_keys(),
                }

            comparison_map[label]["total_inventory"] += inv_val
            comparison_map[label]["total_installed"] += inst_val

            key = _category_key(row[1], row[2])
            if key and key in comparison_map[label]:
                comparison_map[label][key]["inventory"] += inv_val
                comparison_map[label][key]["installed"] += inst_val

        comparison: List[Dict[str, Any]] = []
        for label in sorted(comparison_map.keys()):
            item = comparison_map[label]
            inv = item["total_inventory"]
            inst = item["total_installed"]
            
            ordered_item = {
                "label": label,
                "total_inventory": inv,
                "total_installed": inst,
            }
            
            if is_pace_vs_stock:
                ordered_item["remaining_stock"] = max(0, inv - inst)
            else:
                ordered_item["utilization_rate_pct"] = round(float(inst / inv * 100), 2) if inv > 0 else 0.0

            bucket_keys = _nested_bucket_key_order()
            if bucket_keys:
                for bk in bucket_keys:
                    sub = item[bk]
                    ordered_item[bk] = _bucket_output(sub["inventory"], sub["installed"])
            else:
                for k, v in item.items():
                    if k not in ["label", "total_inventory", "total_installed"]:
                        ordered_item[k] = v

            comparison.append(ordered_item)

        return {
            "total_inventory": total_inv,
            "total_installed": total_inst,
            "utilization_rate_pct": round(float(util_rate), 2),
            "remaining_stock": rem_stock,
            "period_breakdown": period_breakdown,
            "comparison": comparison
        }

    def get_mi_vs_sat_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        from sqlalchemy import func
        from datetime import datetime

        CONSUMER_SUBCATEGORY_MAP = {
            "1PH-STSM": "1PH-Consumer_meter",
            "NBSM-1PH": "1PH-Consumer_meter",
            "NSM1-PH": "1PH-Consumer_meter",
            "3PH-STSM": "3PH-Consumer_meter",
            "3PNBLTSM": "3PH-Consumer_meter",
            "NBSM-3PH": "3PH-Consumer_meter",
            "NSM3-PH": "3PH-Consumer_meter",
            "3LTTOUSM": "3PH-Consumer_meter",
            "HTNBTOUS": "3PH-Consumer_meter",
            "HT-TOUSM": "3PH-Consumer_meter",
            "LT-NBTOUS": "3PH-Consumer_meter",
            "3PLTCTSM": "LTCT-Consumer_meter",
            "HTCTPTSM": "HTCT-Consumer_meter",
        }
        CONSUMER_SUB_KEYS = ["1PH-Consumer_meter", "3PH-Consumer_meter", "LTCT-Consumer_meter", "HTCT-Consumer_meter"]
        SAT_STAGES = ["sat_1", "sat_2", "sat_3", "sat_4", "sat_5", "sat_6", "sat_7", "sat_8", "sat_9"]

        # Extract special parameters
        level = (filters.pop("level", None) or "discom").lower()
        project = (filters.pop("project", None) or "all").lower()
        duration = (filters.get("duration") or filters.get("period") or "daily").lower()
        category_param = (filters.pop("category", None) or filters.pop("meter_category", None) or "total").lower()
        category_map = {"consumer": "CONSUMER", "feeder": "FEEDER", "dt": "DT"}
        meter_category = category_map.get(category_param)
        start_date = filters.pop("start_date", None)
        end_date = filters.pop("end_date", None)

        # Build base query
        q = self.session.query(MIvsSAT)
        q = self._apply_filters(q, MIvsSAT, filters)

        # Project scope
        default_projects = ["AGRA", "KASHI", "TRIVENI"]
        if project == "all":
            q = q.filter(func.upper(func.trim(MIvsSAT.project)).in_(default_projects))
        else:
            q = q.filter(func.upper(func.trim(MIvsSAT.project)) == project.upper())

        # Category filter
        if meter_category is not None:
            q = q.filter(func.upper(func.trim(MIvsSAT.meter_category)) == meter_category)

        # Date filtering
        pv_date = self._period_value_as_date(MIvsSAT, duration)
        if start_date:
            q = q.filter(pv_date >= func.to_date(start_date, "YYYY-MM-DD"))
        if end_date:
            q = q.filter(pv_date <= func.to_date(end_date, "YYYY-MM-DD"))

        # Helper: build empty SAT stage bucket based on category
        def _empty_bucket():
            if category_param == "consumer":
                return {k: 0 for k in CONSUMER_SUB_KEYS + ["total"]}
            elif category_param == "total":
                return {"CONSUMER": 0, "FEEDER": 0, "DT": 0, "total": 0}
            else:
                return 0  # flat integer for feeder/dt

        # Helper: get the sub-key for a given row
        def _category_key(row_cat, row_meter_type):
            cat = str(row_cat).upper() if row_cat else "UNKNOWN"
            if category_param == "consumer" and cat == "CONSUMER":
                return CONSUMER_SUBCATEGORY_MAP.get(row_meter_type)
            elif category_param == "total":
                return cat if cat in ("CONSUMER", "FEEDER", "DT") else None
            else:
                return None

        # 1. Aggregate main totals
        res = q.with_entities(
            func.sum(MIvsSAT.total_mi),
            func.sum(MIvsSAT.total_sat),
        ).first()

        t_mi = int(res[0] or 0)
        t_sat = int(res[1] or 0)
        pct = round((t_sat / t_mi * 100), 2) if t_mi > 0 else 0.0

        # 2. Build Summary — query grouped by meter_category + new_meter_type
        s_rows = q.with_entities(
            MIvsSAT.meter_category,
            MIvsSAT.new_meter_type,
            func.sum(MIvsSAT.sat_1),
            func.sum(MIvsSAT.sat_2),
            func.sum(MIvsSAT.sat_3),
            func.sum(MIvsSAT.sat_4),
            func.sum(MIvsSAT.sat_5),
            func.sum(MIvsSAT.sat_6),
            func.sum(MIvsSAT.sat_7),
            func.sum(MIvsSAT.sat_8),
            func.sum(MIvsSAT.sat_9),
        ).group_by(MIvsSAT.meter_category, MIvsSAT.new_meter_type).all()

        summary: Dict[str, Any] = {stage: _empty_bucket() for stage in SAT_STAGES}

        for r in s_rows:
            stage_vals = [int(r[i] or 0) for i in range(2, 11)]

            if category_param in ("feeder", "dt"):
                for idx, stage in enumerate(SAT_STAGES):
                    summary[stage] += stage_vals[idx]
            else:
                key = _category_key(r[0], r[1])
                if key:
                    for idx, stage in enumerate(SAT_STAGES):
                        if key in summary[stage]:
                            summary[stage][key] += stage_vals[idx]
                        summary[stage]["total"] += stage_vals[idx]

        # 3. Build Comparison — grouped by level, meter_category, new_meter_type
        if level == "discom" and project == "all":
            group_expr = func.upper(func.trim(MIvsSAT.project))
        else:
            if not hasattr(MIvsSAT, level):
                level = "discom"
            level_col = getattr(MIvsSAT, level)
            if project == "all" and level != "discom":
                group_expr = func.concat(func.upper(func.trim(MIvsSAT.project)), " | ", func.coalesce(level_col, "Unknown"))
            else:
                group_expr = func.coalesce(level_col, "Unknown")

        comp_rows = q.with_entities(
            group_expr.label("label"),
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
            func.sum(MIvsSAT.sat_9),
        ).group_by(group_expr, MIvsSAT.meter_category, MIvsSAT.new_meter_type).order_by("label").all()

        comparison_map: Dict[str, Dict[str, Any]] = {}
        for r in comp_rows:
            label = str(r[0])
            mi_val = int(r[3] or 0)
            sat_val = int(r[4] or 0)
            stage_vals = [int(r[i] or 0) for i in range(5, 14)]

            if label not in comparison_map:
                comparison_map[label] = {
                    "label": label,
                    "total_mi": 0,
                    "total_sat": 0,
                    "sat_progress_pct": 0.0,
                    **{stage: _empty_bucket() for stage in SAT_STAGES},
                }

            comparison_map[label]["total_mi"] += mi_val
            comparison_map[label]["total_sat"] += sat_val

            if category_param in ("feeder", "dt"):
                for idx, stage in enumerate(SAT_STAGES):
                    comparison_map[label][stage] += stage_vals[idx]
            else:
                key = _category_key(r[1], r[2])
                if key:
                    for idx, stage in enumerate(SAT_STAGES):
                        if key in comparison_map[label][stage]:
                            comparison_map[label][stage][key] += stage_vals[idx]
                        comparison_map[label][stage]["total"] += stage_vals[idx]

        comparison: List[Dict[str, Any]] = []
        for label in sorted(comparison_map.keys()):
            item = comparison_map[label]
            c_mi = item["total_mi"]
            c_sat = item["total_sat"]
            item["sat_progress_pct"] = round((c_sat / c_mi * 100), 2) if c_mi > 0 else 0.0
            comparison.append(item)

        return {
            "total_mi": t_mi,
            "total_sat": t_sat,
            "sat_progress_pct": pct,
            "summary": summary,
            "comparison": comparison,
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
        
        category_param = (base_filters.pop("category", None) or base_filters.pop("meter_category", None) or "total").lower()
        category_map = {"consumer": "CONSUMER", "feeder": "FEEDER", "dt": "DT"}
        meter_category = category_map.get(category_param)
        
        CONSUMER_SUBCATEGORY_MAP = {
            "1PH-STSM": "1PH-Consumer_meter",
            "NBSM-1PH": "1PH-Consumer_meter",
            "NSM1-PH": "1PH-Consumer_meter",
            "3PH-STSM": "3PH-Consumer_meter",
            "3PNBLTSM": "3PH-Consumer_meter",
            "NBSM-3PH": "3PH-Consumer_meter",
            "NSM3-PH": "3PH-Consumer_meter",
            "3LTTOUSM": "3PH-Consumer_meter",
            "HTNBTOUS": "3PH-Consumer_meter",
            "HT-TOUSM": "3PH-Consumer_meter",
            "LT-NBTOUS": "3PH-Consumer_meter",
            "3PLTCTSM": "LTCT-Consumer_meter",
            "HTCTPTSM": "HTCT-Consumer_meter",
        }
        CONSUMER_SUB_KEYS = ["1PH-Consumer_meter", "3PH-Consumer_meter", "LTCT-Consumer_meter", "HTCT-Consumer_meter"]
        
        q = self.session.query(StockAgeing)
        q = self._apply_filters(q, StockAgeing, base_filters)
        
        valid_duration = duration if duration in ["daily", "weekly", "monthly"] else "monthly"
        q = q.filter(StockAgeing.period_type == valid_duration)

        default_projects = ["AGRA", "KASHI", "TRIVENI"]
        if project == "all":
            q = q.filter(func.upper(func.trim(StockAgeing.project)).in_(default_projects))
        else:
            q = q.filter(func.upper(func.trim(StockAgeing.project)) == project.upper())
            
        if meter_category is not None:
            q = q.filter(func.upper(func.trim(StockAgeing.meter_category)) == meter_category)

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

        def _empty_bucket():
            if category_param == "consumer":
                return {k: 0 for k in CONSUMER_SUB_KEYS + ["total"]}
            elif category_param == "total":
                return {k: 0 for k in ("CONSUMER", "FEEDER", "DT", "total")}
            else:
                return 0 # Flat integer for feeder/dt

        def _category_key(row_cat, row_meter_type):
            cat = str(row_cat).upper() if row_cat else "UNKNOWN"
            if category_param == "consumer" and cat == "CONSUMER":
                return CONSUMER_SUBCATEGORY_MAP.get(row_meter_type)
            elif category_param == "total":
                return cat if cat in ("CONSUMER", "FEEDER", "DT") else None
            else:
                return None

        # 3. Overall Summary (Replaces Period Breakdown)
        s_rows = q.with_entities(
            StockAgeing.meter_category,
            StockAgeing.new_meter_type,
            func.sum(StockAgeing.age_0_30),
            func.sum(StockAgeing.age_31_60),
            func.sum(StockAgeing.age_61_90),
            func.sum(StockAgeing.age_90_plus)
        ).group_by(StockAgeing.meter_category, StockAgeing.new_meter_type).all()
        
        summary = {
            "age_0_30": _empty_bucket(),
            "age_31_60": _empty_bucket(),
            "age_61_90": _empty_bucket(),
            "age_90_plus": _empty_bucket(),
            "total_stock": 0
        }
        
        for r in s_rows:
            a0, a31, a61, a90 = int(r[2] or 0), int(r[3] or 0), int(r[4] or 0), int(r[5] or 0)
            
            summary["total_stock"] += (a0 + a31 + a61 + a90)
            
            if category_param in ("feeder", "dt"):
                summary["age_0_30"] += a0
                summary["age_31_60"] += a31
                summary["age_61_90"] += a61
                summary["age_90_plus"] += a90
            else:
                key = _category_key(r[0], r[1])
                if key:
                    for b_name, b_val in [("age_0_30", a0), ("age_31_60", a31), ("age_61_90", a61), ("age_90_plus", a90)]:
                        if key in summary[b_name]:
                            summary[b_name][key] += b_val
                        summary[b_name]["total"] += b_val

        # 4. Comparison
        if level == "discom" and project == "all":
            group_expr = func.upper(func.trim(StockAgeing.project))
        else:
            if not hasattr(StockAgeing, level):
                level = "discom"
            level_col = getattr(StockAgeing, level)
            if project == "all" and level != "discom":
                group_expr = func.concat(func.upper(func.trim(StockAgeing.project)), " | ", func.coalesce(level_col, "Unknown"))
            else:
                group_expr = func.coalesce(level_col, "Unknown")
                    
        comp_rows = q.with_entities(
            group_expr.label("label"),
            StockAgeing.meter_category,
            StockAgeing.new_meter_type,
            func.sum(StockAgeing.age_0_30),
            func.sum(StockAgeing.age_31_60),
            func.sum(StockAgeing.age_61_90),
            func.sum(StockAgeing.age_90_plus)
        ).group_by(group_expr, StockAgeing.meter_category, StockAgeing.new_meter_type).order_by("label").all()

        comparison_map = {}
        for r in comp_rows:
            label = str(r[0])
            a0, a31, a61, a90 = [int(x or 0) for x in r[3:]]

            if label not in comparison_map:
                comparison_map[label] = {
                    "label": label,
                    "age_0_30": _empty_bucket(),
                    "age_31_60": _empty_bucket(),
                    "age_61_90": _empty_bucket(),
                    "age_90_plus": _empty_bucket(),
                    "total_stock": 0
                }
            
            target = comparison_map[label]
            target["total_stock"] += (a0 + a31 + a61 + a90)
            
            if category_param in ("feeder", "dt"):
                target["age_0_30"] += a0
                target["age_31_60"] += a31
                target["age_61_90"] += a61
                target["age_90_plus"] += a90
            else:
                key = _category_key(r[1], r[2])
                if key:
                    for b_name, b_val in [("age_0_30", a0), ("age_31_60", a31), ("age_61_90", a61), ("age_90_plus", a90)]:
                        if key in target[b_name]:
                            target[b_name][key] += b_val
                        target[b_name]["total"] += b_val

        comparison = list(comparison_map.values())
        comparison.sort(key=lambda x: x["label"])

        return {
            "total_stock": total_stock,
            "summary": summary,
            "comparison": comparison
        }

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
        
        CONSUMER_SUBCATEGORY_MAP = {
            "1PH-STSM": "1PH-Consumer_meter",
            "NBSM-1PH": "1PH-Consumer_meter",
            "NSM1-PH": "1PH-Consumer_meter",
            "3PH-STSM": "3PH-Consumer_meter",
            "3PNBLTSM": "3PH-Consumer_meter",
            "NBSM-3PH": "3PH-Consumer_meter",
            "NSM3-PH": "3PH-Consumer_meter",
            "3LTTOUSM": "3PH-Consumer_meter",
            "HTNBTOUS": "3PH-Consumer_meter",
            "HT-TOUSM": "3PH-Consumer_meter",
            "LT-NBTOUS": "3PH-Consumer_meter",
            "3PLTCTSM": "LTCT-Consumer_meter",
            "HTCTPTSM": "HTCT-Consumer_meter",
        }
        CONSUMER_SUB_KEYS = ["1PH-Consumer_meter", "3PH-Consumer_meter", "LTCT-Consumer_meter", "HTCT-Consumer_meter"]

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

        def _empty_bucket():
            if category_param == "consumer":
                return {k: 0 for k in CONSUMER_SUB_KEYS + ["total"]}
            elif category_param == "total":
                return {k: 0 for k in ("CONSUMER", "FEEDER", "DT", "total")}
            else:
                return 0

        def _category_key(row_cat, row_meter_type):
            cat = str(row_cat).upper() if row_cat else "UNKNOWN"
            if category_param == "consumer" and cat == "CONSUMER":
                return CONSUMER_SUBCATEGORY_MAP.get(row_meter_type)
            elif category_param == "total":
                return cat if cat in ("CONSUMER", "FEEDER", "DT") else None
            else:
                return None

        # Summary calculation - group by category and meter_type to get breakdown per bucket
        s_rows = q.with_entities(
            NonSATAgeing.meter_category,
            NonSATAgeing.new_meter_type,
            func.sum(case((NonSATAgeing.ageing_days <= 30, 1), else_=0)),
            func.sum(case(((NonSATAgeing.ageing_days > 30) & (NonSATAgeing.ageing_days <= 60), 1), else_=0)),
            func.sum(case(((NonSATAgeing.ageing_days > 60) & (NonSATAgeing.ageing_days <= 90), 1), else_=0)),
            func.sum(case(((NonSATAgeing.ageing_days > 90) & (NonSATAgeing.ageing_days <= 120), 1), else_=0)),
            func.sum(case((NonSATAgeing.ageing_days > 120, 1), else_=0)),
            func.count(NonSATAgeing.meter_serial_number)
        ).group_by(NonSATAgeing.meter_category, NonSATAgeing.new_meter_type).all()

        summary = {
            "age_0_30": _empty_bucket(),
            "age_31_60": _empty_bucket(),
            "age_61_90": _empty_bucket(),
            "age_91_120": _empty_bucket(),
            "age_120_plus": _empty_bucket(),
            "total_non_sat": total_non_sat
        }

        for r in s_rows:
            a0, a31, a61, a91, a120 = [int(x or 0) for x in r[2:7]]
            
            if category_param in ("feeder", "dt"):
                summary["age_0_30"] += a0
                summary["age_31_60"] += a31
                summary["age_61_90"] += a61
                summary["age_91_120"] += a91
                summary["age_120_plus"] += a120
            else:
                key = _category_key(r[0], r[1])
                if key:
                    for b_name, b_val in [("age_0_30", a0), ("age_31_60", a31), ("age_61_90", a61), ("age_91_120", a91), ("age_120_plus", a120)]:
                        if key in summary[b_name]:
                            summary[b_name][key] += b_val
                        summary[b_name]["total"] += b_val

        # Comparison
        if level == "discom" and project == "all":
            group_expr = func.upper(func.trim(NonSATAgeing.project))
        else:
            if not hasattr(NonSATAgeing, level):
                level = "discom"
            level_col = getattr(NonSATAgeing, level)
            if project == "all" and level != "discom":
                group_expr = func.concat(func.upper(func.trim(NonSATAgeing.project)), " | ", func.coalesce(level_col, "Unknown"))
            else:
                group_expr = func.coalesce(level_col, "Unknown")
                    
        comp_rows = q.with_entities(
            group_expr.label("label"),
            NonSATAgeing.meter_category,
            NonSATAgeing.new_meter_type,
            func.sum(case((NonSATAgeing.ageing_days <= 30, 1), else_=0)),
            func.sum(case(((NonSATAgeing.ageing_days > 30) & (NonSATAgeing.ageing_days <= 60), 1), else_=0)),
            func.sum(case(((NonSATAgeing.ageing_days > 60) & (NonSATAgeing.ageing_days <= 90), 1), else_=0)),
            func.sum(case(((NonSATAgeing.ageing_days > 90) & (NonSATAgeing.ageing_days <= 120), 1), else_=0)),
            func.sum(case((NonSATAgeing.ageing_days > 120, 1), else_=0)),
            func.count(NonSATAgeing.meter_serial_number)
        ).group_by(group_expr, NonSATAgeing.meter_category, NonSATAgeing.new_meter_type).order_by("label").all()

        comparison_map = {}
        for r in comp_rows:
            label = str(r[0])
            a0, a31, a61, a91, a120, cnt = [int(x or 0) for x in r[3:]]

            if label not in comparison_map:
                comparison_map[label] = {
                    "label": label,
                    "age_0_30": _empty_bucket(),
                    "age_31_60": _empty_bucket(),
                    "age_61_90": _empty_bucket(),
                    "age_91_120": _empty_bucket(),
                    "age_120_plus": _empty_bucket(),
                    "total_non_sat": 0
                }
            
            target = comparison_map[label]
            target["total_non_sat"] += cnt

            if category_param in ("feeder", "dt"):
                target["age_0_30"] += a0
                target["age_31_60"] += a31
                target["age_61_90"] += a61
                target["age_91_120"] += a91
                target["age_120_plus"] += a120
            else:
                key = _category_key(r[1], r[2])
                if key:
                    for b_name, b_val in [("age_0_30", a0), ("age_31_60", a31), ("age_61_90", a61), ("age_91_120", a91), ("age_120_plus", a120)]:
                        if key in target[b_name]:
                            target[b_name][key] += b_val
                        target[b_name]["total"] += b_val
                
        comparison = [v for k, v in sorted(comparison_map.items())]

        return {
            "total_non_sat": total_non_sat,
            "summary": summary,
            "comparison": comparison
        }

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
        else:
            return func.coalesce(level_col, "Unknown")

    def get_meter_journey_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Meter journey dashboard from **pre-aggregated** ``sql_meter_journey_avg_time``.

        When ``category=consumer``, each stage field is nested by meter-type group
        (1PH / 3PH / LTCT / HTCT + total).  When ``category=total``, nested by
        CONSUMER / FEEDER / DT + total.  Otherwise flat integers.
        """
        M = MeterJourneyAvgTime
        w = M.meter_count

        _STAGE_COLS = [
            "inventory_to_store", "store_to_agency",
            "agency_to_meter_installation", "meter_installation_to_sat",
            "sat_to_invoice", "invoice_to_revenue", "total_journey",
        ]

        category_param = str(filters.get("category") or "total").lower()

        def _empty_stage_bucket():
            if category_param == "consumer":
                return {k: None for k in CONSUMER_SUB_KEYS + ["total"]}
            if category_param == "total":
                return {k: None for k in CATEGORY_KEYS + ["total"]}
            return None

        def _empty_count_bucket():
            if category_param == "consumer":
                return {k: 0 for k in CONSUMER_SUB_KEYS + ["total"]}
            if category_param == "total":
                return {k: 0 for k in CATEGORY_KEYS + ["total"]}
            return 0

        def _sub_key(row_cat, row_meter_type):
            cat = str(row_cat).upper() if row_cat else "UNKNOWN"
            if category_param == "consumer" and cat == "CONSUMER":
                return CONSUMER_SUBCATEGORY_MAP.get(row_meter_type)
            if category_param == "total":
                return cat if cat in CATEGORY_KEYS else None
            return None

        needs_nesting = category_param in ("consumer", "total")

        # ── flat path (feeder / dt) ──────────────────────────────────
        if not needs_nesting:
            q_sum, _ = self._mj_dashboard_base_query(filters)
            summary_row = q_sum.with_entities(
                *[self._mj_weighted_stage(getattr(M, c), w, c) for c in _STAGE_COLS],
                func.coalesce(func.sum(w), 0).label("meter_count"),
            ).one()
            summary = self._mj_format_flat_row(summary_row._mapping, _STAGE_COLS)

            level = (filters.get("level") or "discom").lower()
            project = str(filters.get("project") or "all").lower()
            grp = self._mj_comparison_group_expr(M, level, project)
            q_cmp, _ = self._mj_dashboard_base_query(filters)
            cmp_rows = q_cmp.with_entities(
                grp.label("label"),
                *[self._mj_weighted_stage(getattr(M, c), w, c) for c in _STAGE_COLS],
                func.coalesce(func.sum(w), 0).label("meter_count"),
            ).group_by(grp).order_by(grp).all()

            comparison = []
            for r in cmp_rows:
                row_dict = self._mj_format_flat_row(r._mapping, _STAGE_COLS)
                lbl = r._mapping["label"]
                label_str = str(lbl).strip() if lbl else "Unknown"
                comparison.append({"label": label_str, **row_dict})

            return {"summary": summary, "comparison": comparison}

        # ── nested path (consumer / total) ───────────────────────────
        # Summary: group by meter_category + new_meter_type
        q_sum, _ = self._mj_dashboard_base_query(filters)
        s_rows = q_sum.with_entities(
            M.meter_category,
            M.new_meter_type,
            *[self._mj_weighted_stage(getattr(M, c), w, c) for c in _STAGE_COLS],
            func.coalesce(func.sum(w), 0).label("meter_count"),
        ).group_by(M.meter_category, M.new_meter_type).all()

        summary: Dict[str, Any] = {c: _empty_stage_bucket() for c in _STAGE_COLS}
        summary["meter_count"] = _empty_count_bucket()

        # accumulators for weighted-average totals across all sub-keys
        total_num = {c: 0.0 for c in _STAGE_COLS}
        total_den = {c: 0 for c in _STAGE_COLS}
        total_meter_count = 0

        for r in s_rows:
            m = r._mapping
            key = _sub_key(m["meter_category"], m["new_meter_type"])
            if not key:
                continue
            mc = int(m["meter_count"] or 0)
            total_meter_count += mc
            if key in summary["meter_count"]:
                summary["meter_count"][key] += mc
            summary["meter_count"]["total"] += mc

            for c in _STAGE_COLS:
                raw = m[c]
                if raw is not None:
                    summary[c][key] = self._mj_whole_days(raw)
                    total_num[c] += float(raw) * mc
                    total_den[c] += mc

        for c in _STAGE_COLS:
            summary[c]["total"] = self._mj_whole_days(
                total_num[c] / total_den[c] if total_den[c] else None
            )

        # Comparison: group by label + meter_category + new_meter_type
        level = (filters.get("level") or "discom").lower()
        project = str(filters.get("project") or "all").lower()
        grp = self._mj_comparison_group_expr(M, level, project)
        q_cmp, _ = self._mj_dashboard_base_query(filters)
        cmp_rows = q_cmp.with_entities(
            grp.label("label"),
            M.meter_category,
            M.new_meter_type,
            *[self._mj_weighted_stage(getattr(M, c), w, c) for c in _STAGE_COLS],
            func.coalesce(func.sum(w), 0).label("meter_count"),
        ).group_by(grp, M.meter_category, M.new_meter_type).order_by(grp).all()

        comparison_map: Dict[str, Dict[str, Any]] = {}
        comp_total_num: Dict[str, Dict[str, float]] = {}
        comp_total_den: Dict[str, Dict[str, int]] = {}

        for r in cmp_rows:
            m = r._mapping
            label = str(m["label"]).strip() if m["label"] else "Unknown"
            key = _sub_key(m["meter_category"], m["new_meter_type"])
            if not key:
                continue

            if label not in comparison_map:
                comparison_map[label] = {"label": label}
                comparison_map[label].update({c: _empty_stage_bucket() for c in _STAGE_COLS})
                comparison_map[label]["meter_count"] = _empty_count_bucket()
                comp_total_num[label] = {c: 0.0 for c in _STAGE_COLS}
                comp_total_den[label] = {c: 0 for c in _STAGE_COLS}

            target = comparison_map[label]
            mc = int(m["meter_count"] or 0)
            if key in target["meter_count"]:
                target["meter_count"][key] += mc
            target["meter_count"]["total"] += mc

            for c in _STAGE_COLS:
                raw = m[c]
                if raw is not None:
                    target[c][key] = self._mj_whole_days(raw)
                    comp_total_num[label][c] += float(raw) * mc
                    comp_total_den[label][c] += mc

        for label, target in comparison_map.items():
            for c in _STAGE_COLS:
                den = comp_total_den[label][c]
                target[c]["total"] = self._mj_whole_days(
                    comp_total_num[label][c] / den if den else None
                )

        comparison = sorted(comparison_map.values(), key=lambda x: x["label"])
        return {"summary": summary, "comparison": comparison}

    def _mj_format_flat_row(self, row, stage_cols) -> Dict[str, Any]:
        """Format a single aggregation row with flat integer stage values."""
        if not row:
            result = {c: None for c in stage_cols}
            result["meter_count"] = 0
            return result
        result = {c: self._mj_whole_days(row[c]) for c in stage_cols}
        result["meter_count"] = int(row["meter_count"] or 0)
        return result

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

    # KPI 10 — "Pending PMPM Collection" funnel fields and the corresponding
    # pre-aggregated columns on ``sql_meter_current_stage`` (populated by the ETL
    # in ``execute_kpi_10_meter_stage``).
    _METER_STAGE_FIELDS = ["inventory", "installed", "sat_done", "invoice_done"]
    _METER_STAGE_COLS = [
        "pending_inventory",
        "pending_installed",
        "pending_sat_done",
        "pending_invoice_done",
    ]

    # KPI 12 — Revenue Realized (same four column names as ``sql_revenue_realized``)
    _REVENUE_REALIZED_METRIC_KEYS = (
        "total_lumpsum_invoice",
        "total_pmpm_invoice",
        "total_lumpsum_collection",
        "total_pmpm_collection",
    )

    def _revenue_realized_base_query(self, filters: Dict[str, Any]):
        """Filter ``sql_revenue_realized`` for project/category/geo/duration (KPI-12)."""
        R = RevenueRealized
        skip = {
            "duration", "period", "level", "category", "project",
            "start_date", "end_date", "mi_usecase", "limit", "offset",
        }
        fd = {k: v for k, v in filters.items() if k not in skip}
        q = self.session.query(R)
        q = self._apply_filters(q, R, fd)

        project = str(filters.get("project") or "all").lower()
        if project == "all" or not project:
            q = q.filter(func.upper(func.trim(R.project)).in_(["AGRA", "KASHI", "TRIVENI"]))
        else:
            q = q.filter(func.upper(func.trim(R.project)) == project.upper())

        duration = (filters.get("duration") or filters.get("period") or "all").lower()
        if duration != "all":
            q = q.filter(R.period_type == duration)

        category = str(filters.get("category") or "total").lower()
        category_map = {"consumer": "CONSUMER", "feeder": "FEEDER", "dt": "DT"}
        meter_category = category_map.get(category)
        if meter_category:
            q = q.filter(func.upper(func.trim(R.meter_category)) == meter_category)
        else:
            q = q.filter(func.upper(func.trim(R.meter_category)).in_(list(category_map.values())))
        return q

    def _revenue_realized_flat(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Flat ``{summary, comparison}`` for ``category=feeder|dt`` (KPI 12)."""
        R = RevenueRealized
        q = self._revenue_realized_base_query(filters)

        totals = q.with_entities(
            func.coalesce(func.sum(R.total_lumpsum_invoice), 0),
            func.coalesce(func.sum(R.total_pmpm_invoice), 0),
            func.coalesce(func.sum(R.total_lumpsum_collection), 0),
            func.coalesce(func.sum(R.total_pmpm_collection), 0),
        ).first()
        t_li, t_pi, t_lc, t_pc = (
            [int(x or 0) for x in totals] if totals else [0, 0, 0, 0]
        )
        summary = {
            "total_lumpsum_invoice": t_li,
            "total_pmpm_invoice": t_pi,
            "total_lumpsum_collection": t_lc,
            "total_pmpm_collection": t_pc,
        }

        project = str(filters.get("project") or "all").lower()
        level = (filters.get("level") or "discom").lower()
        grp = self._mj_comparison_group_expr(R, level, project)

        comp_rows = q.with_entities(
            grp.label("label"),
            func.coalesce(func.sum(R.total_lumpsum_invoice), 0).label("total_lumpsum_invoice"),
            func.coalesce(func.sum(R.total_pmpm_invoice), 0).label("total_pmpm_invoice"),
            func.coalesce(func.sum(R.total_lumpsum_collection), 0).label("total_lumpsum_collection"),
            func.coalesce(func.sum(R.total_pmpm_collection), 0).label("total_pmpm_collection"),
        ).group_by("label").order_by("label").all()

        comparison = [
            {
                "label": str(row.label or "Unknown").strip(),
                "total_lumpsum_invoice": int(row.total_lumpsum_invoice or 0),
                "total_pmpm_invoice": int(row.total_pmpm_invoice or 0),
                "total_lumpsum_collection": int(row.total_lumpsum_collection or 0),
                "total_pmpm_collection": int(row.total_pmpm_collection or 0),
            }
            for row in comp_rows
        ]

        return {"summary": summary, "comparison": comparison}

    def _revenue_realized_nested(
        self,
        filters: Dict[str, Any],
        sub_keys: List[str],
        bucket_fn,
    ) -> Dict[str, Any]:
        """
        Nested ``{summary, comparison}`` for KPI 12: each metric is
        ``{<sub_key>: int, ..., "total": int}``.
        """
        R = RevenueRealized
        q = self._revenue_realized_base_query(filters)

        def _empty_field_bucket() -> Dict[str, int]:
            return {k: 0 for k in sub_keys + ["total"]}

        s_rows = q.with_entities(
            R.meter_category,
            R.new_meter_type,
            func.coalesce(func.sum(R.total_lumpsum_invoice), 0).label("total_lumpsum_invoice"),
            func.coalesce(func.sum(R.total_pmpm_invoice), 0).label("total_pmpm_invoice"),
            func.coalesce(func.sum(R.total_lumpsum_collection), 0).label("total_lumpsum_collection"),
            func.coalesce(func.sum(R.total_pmpm_collection), 0).label("total_pmpm_collection"),
        ).group_by(R.meter_category, R.new_meter_type).all()

        summary: Dict[str, Dict[str, int]] = {
            k: _empty_field_bucket() for k in self._REVENUE_REALIZED_METRIC_KEYS
        }

        for row in s_rows:
            bucket = bucket_fn(row.meter_category, row.new_meter_type)
            if not bucket or bucket not in sub_keys:
                continue
            for field in self._REVENUE_REALIZED_METRIC_KEYS:
                val = int(getattr(row, field) or 0)
                if val == 0:
                    continue
                summary[field][bucket] += val
                summary[field]["total"] += val

        project = str(filters.get("project") or "all").lower()
        level = (filters.get("level") or "discom").lower()
        grp = self._mj_comparison_group_expr(R, level, project)

        c_rows = q.with_entities(
            grp.label("label"),
            R.meter_category,
            R.new_meter_type,
            func.coalesce(func.sum(R.total_lumpsum_invoice), 0).label("total_lumpsum_invoice"),
            func.coalesce(func.sum(R.total_pmpm_invoice), 0).label("total_pmpm_invoice"),
            func.coalesce(func.sum(R.total_lumpsum_collection), 0).label("total_lumpsum_collection"),
            func.coalesce(func.sum(R.total_pmpm_collection), 0).label("total_pmpm_collection"),
        ).group_by(grp, R.meter_category, R.new_meter_type).order_by(grp).all()

        comparison_map: Dict[str, Dict[str, Any]] = {}
        for row in c_rows:
            label = str(row.label or "Unknown").strip()
            bucket = bucket_fn(row.meter_category, row.new_meter_type)
            if not bucket or bucket not in sub_keys:
                continue

            entry = comparison_map.get(label)
            if entry is None:
                entry = {"label": label}
                for f in self._REVENUE_REALIZED_METRIC_KEYS:
                    entry[f] = _empty_field_bucket()
                comparison_map[label] = entry

            for f in self._REVENUE_REALIZED_METRIC_KEYS:
                val = int(getattr(row, f) or 0)
                if val == 0:
                    continue
                entry[f][bucket] += val
                entry[f]["total"] += val

        comparison = sorted(comparison_map.values(), key=lambda x: x["label"])
        return {"summary": summary, "comparison": comparison}

    def get_meter_stage_dashboard(self, filters: Dict[str, Any], limit: int, offset: int) -> Dict[str, Any]:
        """
        KPI 10 — Meter Funnel Summary ("Pending PMPM Collection").

        Always returns ``{"summary": ..., "comparison": [...]}`` (KPI-9-style shape).
        The four funnel fields are ``inventory / installed / sat_done / invoice_done``,
        each restricted to meters where ``pmpm_collection_date IS NULL``.

        Nesting per ``category``:
        - ``consumer``  → each field nests by 1PH/3PH/LTCT/HTCT/total.
        - ``total`` (default / None) → each field nests by CONSUMER/FEEDER/DT/total.
        - ``feeder`` / ``dt`` → each field is a flat int.
        """
        category_param = str(filters.get("category") or "total").lower()

        if category_param == "consumer":
            return self._meter_stage_nested(
                filters,
                sub_keys=CONSUMER_SUB_KEYS,
                bucket_fn=lambda cat, mt: CONSUMER_SUBCATEGORY_MAP.get(mt),
            )

        if category_param in ("total", "all"):
            def _cat_bucket(cat, _mt):
                up = (cat or "").strip().upper()
                return up if up in CATEGORY_KEYS else None

            return self._meter_stage_nested(
                filters,
                sub_keys=CATEGORY_KEYS,
                bucket_fn=_cat_bucket,
            )

        # feeder / dt → flat
        return self._meter_stage_flat(filters)

    def _meter_stage_flat(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Flat ``{summary, comparison}`` for ``category=feeder|dt``."""
        M = MeterCurrentStage
        q = self._meter_stage_base_query(filters)

        totals = q.with_entities(
            func.coalesce(func.sum(M.pending_inventory), 0),
            func.coalesce(func.sum(M.pending_installed), 0),
            func.coalesce(func.sum(M.pending_sat_done), 0),
            func.coalesce(func.sum(M.pending_invoice_done), 0),
        ).first()
        t_inv, t_inst, t_sat, t_inv_done = (
            [int(x or 0) for x in totals] if totals else [0, 0, 0, 0]
        )
        summary = {
            "inventory": t_inv,
            "installed": t_inst,
            "sat_done": t_sat,
            "invoice_done": t_inv_done,
        }

        project = str(filters.get("project") or "all").lower()
        level = (filters.get("level") or "discom").lower()
        grp = self._mj_comparison_group_expr(M, level, project)

        comp_rows = q.with_entities(
            grp.label("label"),
            func.coalesce(func.sum(M.pending_inventory), 0).label("inventory"),
            func.coalesce(func.sum(M.pending_installed), 0).label("installed"),
            func.coalesce(func.sum(M.pending_sat_done), 0).label("sat_done"),
            func.coalesce(func.sum(M.pending_invoice_done), 0).label("invoice_done"),
        ).group_by("label").order_by("label").all()

        comparison = [
            {
                "label": str(row.label or "Unknown").strip(),
                "inventory": int(row.inventory or 0),
                "installed": int(row.installed or 0),
                "sat_done": int(row.sat_done or 0),
                "invoice_done": int(row.invoice_done or 0),
            }
            for row in comp_rows
        ]

        return {"summary": summary, "comparison": comparison}

    def _meter_stage_nested(
        self,
        filters: Dict[str, Any],
        sub_keys: List[str],
        bucket_fn,
    ) -> Dict[str, Any]:
        """
        Nested ``{summary, comparison}`` where each of the 4 funnel fields is a
        ``{<sub_key>: int, ..., "total": int}`` dict.

        ``sub_keys`` and ``bucket_fn`` parameterise the nesting:
        - consumer: sub_keys = CONSUMER_SUB_KEYS, bucket = CONSUMER_SUBCATEGORY_MAP.get(meter_type)
        - total:    sub_keys = CATEGORY_KEYS,    bucket = upper(meter_category) if in CATEGORY_KEYS
        """
        M = MeterCurrentStage
        q = self._meter_stage_base_query(filters)

        def _empty_field_bucket() -> Dict[str, int]:
            return {k: 0 for k in sub_keys + ["total"]}

        # ── Summary: group by (meter_category, new_meter_type) ────────────
        s_rows = q.with_entities(
            M.meter_category,
            M.new_meter_type,
            func.coalesce(func.sum(M.pending_inventory), 0).label("inventory"),
            func.coalesce(func.sum(M.pending_installed), 0).label("installed"),
            func.coalesce(func.sum(M.pending_sat_done), 0).label("sat_done"),
            func.coalesce(func.sum(M.pending_invoice_done), 0).label("invoice_done"),
        ).group_by(M.meter_category, M.new_meter_type).all()

        summary: Dict[str, Dict[str, int]] = {
            f: _empty_field_bucket() for f in self._METER_STAGE_FIELDS
        }

        for row in s_rows:
            bucket = bucket_fn(row.meter_category, row.new_meter_type)
            if not bucket or bucket not in sub_keys:
                continue
            for f in self._METER_STAGE_FIELDS:
                val = int(getattr(row, f) or 0)
                if val == 0:
                    continue
                summary[f][bucket] += val
                summary[f]["total"] += val

        # ── Comparison: group by (level_label, meter_category, new_meter_type) ─
        project = str(filters.get("project") or "all").lower()
        level = (filters.get("level") or "discom").lower()
        grp = self._mj_comparison_group_expr(M, level, project)

        c_rows = q.with_entities(
            grp.label("label"),
            M.meter_category,
            M.new_meter_type,
            func.coalesce(func.sum(M.pending_inventory), 0).label("inventory"),
            func.coalesce(func.sum(M.pending_installed), 0).label("installed"),
            func.coalesce(func.sum(M.pending_sat_done), 0).label("sat_done"),
            func.coalesce(func.sum(M.pending_invoice_done), 0).label("invoice_done"),
        ).group_by(grp, M.meter_category, M.new_meter_type).order_by(grp).all()

        comparison_map: Dict[str, Dict[str, Any]] = {}
        for row in c_rows:
            label = str(row.label or "Unknown").strip()
            bucket = bucket_fn(row.meter_category, row.new_meter_type)
            if not bucket or bucket not in sub_keys:
                continue

            entry = comparison_map.get(label)
            if entry is None:
                entry = {"label": label}
                for f in self._METER_STAGE_FIELDS:
                    entry[f] = _empty_field_bucket()
                comparison_map[label] = entry

            for f in self._METER_STAGE_FIELDS:
                val = int(getattr(row, f) or 0)
                if val == 0:
                    continue
                entry[f][bucket] += val
                entry[f]["total"] += val

        comparison = sorted(comparison_map.values(), key=lambda x: x["label"])
        return {"summary": summary, "comparison": comparison}

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

    @staticmethod
    def _fmt_command_center_date(d) -> Optional[str]:
        return d.strftime("%m/%d/%Y") if d else None

    def _build_sat_milestones_map(self, milestones_db: List[Any]) -> Dict[str, Dict[str, Any]]:
        sat_milestones: Dict[str, Dict[str, Any]] = {}
        for m in milestones_db:
            sat_milestones[m.stage] = {
                "start": self._fmt_command_center_date(m.start_date),
                "lumpsumInv": self._fmt_command_center_date(m.lumpsum_inv_date),
                "pmpInv": self._fmt_command_center_date(m.pmpm_inv_date),
                "lumpsumCol": self._fmt_command_center_date(m.lumpsum_col_date),
                "scCol": self._fmt_command_center_date(m.pmpm_col_date),
            }
        return sat_milestones

    def _build_sat_blue_data_list(
        self,
        snapshot: Any,
        sat_milestones: Dict[str, Dict[str, Any]],
        project_upper: str,
    ) -> List[Dict[str, Any]]:
        is_agra = project_upper == "AGRA"
        last_stage = "SAT-9" if is_agra else "SAT-8"
        last_ms_key = "s9" if is_agra else "s8"
        return [
            {
                "stage": "SAT-1",
                "installedBase": int(snapshot.sat_1_eligibility or 0),
                "cumulativeSat": int(snapshot.sat_1_achievement or 0),
                "efficiencyPct": float(snapshot.sat_1_throughput_pct or 0),
                "startSAT": sat_milestones.get("s1", {}).get("start"),
            },
            {
                "stage": "SAT-2",
                "installedBase": int(snapshot.sat_2_eligibility or 0),
                "cumulativeSat": int(snapshot.sat_2_achievement or 0),
                "efficiencyPct": float(snapshot.sat_2_throughput_pct or 0),
                "startSAT": sat_milestones.get("s2", {}).get("start"),
            },
            {
                "stage": "SAT-3",
                "installedBase": int(snapshot.sat_3_eligibility or 0),
                "cumulativeSat": int(snapshot.sat_3_achievement or 0),
                "efficiencyPct": float(snapshot.sat_3_throughput_pct or 0),
                "startSAT": sat_milestones.get("s3", {}).get("start"),
            },
            {
                "stage": "SAT-4",
                "installedBase": int(snapshot.sat_4_eligibility or 0),
                "cumulativeSat": int(snapshot.sat_4_achievement or 0),
                "efficiencyPct": float(snapshot.sat_4_throughput_pct or 0),
                "startSAT": sat_milestones.get("s4", {}).get("start"),
            },
            {
                "stage": "SAT-5",
                "installedBase": int(snapshot.sat_5_eligibility or 0),
                "cumulativeSat": int(snapshot.sat_5_achievement or 0),
                "efficiencyPct": float(snapshot.sat_5_throughput_pct or 0),
                "startSAT": sat_milestones.get("s5", {}).get("start"),
            },
            {
                "stage": "SAT-6",
                "installedBase": int(snapshot.sat_6_eligibility or 0),
                "cumulativeSat": int(snapshot.sat_6_achievement or 0),
                "efficiencyPct": float(snapshot.sat_6_throughput_pct or 0),
                "startSAT": sat_milestones.get("s6", {}).get("start"),
            },
            {
                "stage": "SAT-7",
                "installedBase": int(snapshot.sat_7_eligibility or 0),
                "cumulativeSat": int(snapshot.sat_7_achievement or 0),
                "efficiencyPct": float(snapshot.sat_7_throughput_pct or 0),
                "startSAT": sat_milestones.get("s7", {}).get("start"),
            },
            {
                "stage": last_stage,
                "installedBase": int((snapshot.sat_9_eligibility if is_agra else snapshot.sat_8_eligibility) or 0),
                "cumulativeSat": int((snapshot.sat_9_achievement if is_agra else snapshot.sat_8_achievement) or 0),
                "efficiencyPct": float((snapshot.sat_9_throughput_pct if is_agra else snapshot.sat_8_throughput_pct) or 0),
                "startSAT": sat_milestones.get(last_ms_key, {}).get("start"),
            },
        ]

    def _build_monthly_raw_list(self, trends: List[Any], project_upper: str) -> List[Dict[str, Any]]:
        is_agra = project_upper == "AGRA"
        sat_stage_key = "s9" if is_agra else "s8"
        raw: List[Dict[str, Any]] = []
        for row in trends:
            sat_stage_value = int((row.s9_added if is_agra else row.s8_added) or 0)
            raw.append(
                {
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
                        sat_stage_key: sat_stage_value,
                    },
                }
            )
        return raw

    @staticmethod
    def _dashboard_command_center_monthly_sort_expr():
        """
        Chronological ORDER BY for command-center monthly trends. period_value is
        typically 'Mon-YY' from ETL (TO_CHAR(..., 'Mon-YY')) — string sort is wrong
        (e.g. Apr-25 before Aug-24). Parse to date for ordering.
        """
        m = DashboardCommandCenterTrend
        pv = func.trim(m.period_value)
        return case(
            (func.length(pv) == 7, func.to_date(func.concat(pv, "-01"), "YYYY-MM-DD")),
            else_=func.to_date(pv, "Mon-YY"),
        )

    def get_command_center_dashboard(self, project: str) -> Dict[str, Any]:
        snapshot = self.session.query(DashboardCommandCenter).filter(
            DashboardCommandCenter.project.ilike(project)
        ).first()

        sort_key = self._dashboard_command_center_monthly_sort_expr()
        trends = (
            self.session.query(DashboardCommandCenterTrend)
            .filter(
                DashboardCommandCenterTrend.project.ilike(project),
                DashboardCommandCenterTrend.period_type == "monthly",
            )
            .order_by(sort_key.asc(), DashboardCommandCenterTrend.period_value.asc())
            .all()
        )

        milestones_db = self.session.query(DashboardCommandCenterMilestone).filter(
            DashboardCommandCenterMilestone.project.ilike(project)
        ).all()

        if not snapshot:
            return {}

        project_upper = (project or "").strip().upper()
        sat_milestones = self._build_sat_milestones_map(milestones_db)
        sat_blue_data = self._build_sat_blue_data_list(snapshot, sat_milestones, project_upper)
        raw = self._build_monthly_raw_list(trends, project_upper)

        return {
            "inventory": int(snapshot.inventory or 0),
            "installed": int(snapshot.installed or 0),
            "total_sat": int(snapshot.total_sat or 0),
            "total_invoice": int(snapshot.total_invoice or 0),
            "region": project_upper,
            "satBlueData": sat_blue_data,
            "raw": raw,
            "sat_milestones": sat_milestones,
        }

    def get_sat_dash_sat_blue_data(self) -> Dict[str, Any]:
        proj_key = func.lower(func.trim(DashboardCommandCenter.project))
        snapshots = (
            self.session.query(DashboardCommandCenter)
            .filter(proj_key.in_(list(SAT_DASH_REGION_KEYS)))
            .all()
        )
        snap_by_key: Dict[str, Any] = {}
        for s in snapshots:
            k = (s.project or "").strip().lower()
            if k in SAT_DASH_REGION_KEYS:
                snap_by_key[k] = s

        ms_proj = func.lower(func.trim(DashboardCommandCenterMilestone.project))
        milestones_all = (
            self.session.query(DashboardCommandCenterMilestone)
            .filter(ms_proj.in_(list(SAT_DASH_REGION_KEYS)))
            .all()
        )
        milestones_by_key: Dict[str, List[Any]] = {rk: [] for rk in SAT_DASH_REGION_KEYS}
        for m in milestones_all:
            k = (m.project or "").strip().lower()
            if k in SAT_DASH_REGION_KEYS:
                milestones_by_key[k].append(m)

        out: Dict[str, Any] = {}
        for key in SAT_DASH_REGION_KEYS:
            snap = snap_by_key.get(key)
            if not snap:
                out[key] = []
                continue
            p_upper = (snap.project or "").strip().upper()
            sat_m = self._build_sat_milestones_map(milestones_by_key[key])
            out[key] = self._build_sat_blue_data_list(snap, sat_m, p_upper)
        return out

    def get_sat_dash_region_monthly(self, region: str) -> List[Dict[str, Any]]:
        r = (region or "").strip().lower()
        if r not in SAT_DASH_REGION_KEYS:
            return []
        sort_key = self._dashboard_command_center_monthly_sort_expr()
        trends = (
            self.session.query(DashboardCommandCenterTrend)
            .filter(
                DashboardCommandCenterTrend.project.ilike(r),
                DashboardCommandCenterTrend.period_type == "monthly",
            )
            .order_by(sort_key.asc(), DashboardCommandCenterTrend.period_value.asc())
            .all()
        )
        return self._build_monthly_raw_list(trends, r.upper())

    def get_mi_sat_invoice_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """KPI 11: MI vs SAT vs Invoice funnel summary."""
        q = self.session.query(MIvsSATvsInvoice)
        
        project = str(filters.get("project") or "all").lower()
        level = (filters.get("level") or "discom").lower()
        category_param = (filters.get("category") or "total").lower()

        base_filters = dict(filters)
        start_date = base_filters.pop("start_date", None)
        end_date = base_filters.pop("end_date", None)
        base_filters.pop("duration", None)
        base_filters.pop("period", None)
        base_filters.pop("level", None)
        base_filters.pop("project", None)
        
        if "category" in base_filters:
            cat_val = base_filters.pop("category")
            if not base_filters.get("meter_category") and str(cat_val).lower() in ("consumer", "feeder", "dt"):
                base_filters["meter_category"] = str(cat_val).upper()
        
        q = self._apply_filters(q, MIvsSATvsInvoice, base_filters)

        if project == "all" or not project:
            q = q.filter(func.upper(func.trim(MIvsSATvsInvoice.project)).in_(["AGRA", "KASHI", "TRIVENI"]))
        else:
            q = q.filter(func.upper(func.trim(MIvsSATvsInvoice.project)) == project.upper())

        if start_date:
            q = q.filter(func.to_date(MIvsSATvsInvoice.period_value, "DD-MM-YY") >= func.to_date(str(start_date), "YYYY-MM-DD"))
        if end_date:
            q = q.filter(func.to_date(MIvsSATvsInvoice.period_value, "DD-MM-YY") <= func.to_date(str(end_date), "YYYY-MM-DD"))
            
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
            MIvsSATvsInvoice.meter_category,
            MIvsSATvsInvoice.new_meter_type,
            func.sum(MIvsSATvsInvoice.total_mi),
            func.sum(MIvsSATvsInvoice.total_sat),
            func.sum(MIvsSATvsInvoice.total_lumpsum_invoice),
            func.sum(MIvsSATvsInvoice.total_pmpm_invoice)
        ).group_by(group_expr, MIvsSATvsInvoice.meter_category, MIvsSATvsInvoice.new_meter_type).order_by("label").all()
        
        def _empty_bucket():
            if category_param == "total":
                return {"CONSUMER": 0, "FEEDER": 0, "DT": 0, "total": 0}
            elif category_param == "consumer":
                return {
                    "1PH-Consumer_meter": 0, "3PH-Consumer_meter": 0,
                    "LTCT-Consumer_meter": 0, "HTCT-Consumer_meter": 0, "total": 0
                }
            return 0  # for feeder/dt

        def _category_key(cat, mtype):
            cat = str(cat or "").upper().strip()
            if category_param == "total":
                return cat if cat in ("CONSUMER", "FEEDER", "DT") else None
            elif category_param == "consumer":
                if cat == "CONSUMER":
                    m = str(mtype or "").upper().strip()
                    if "1PH" in m: return "1PH-Consumer_meter"
                    if "3PH" in m: return "3PH-Consumer_meter"
                    if "LTCT" in m: return "LTCT-Consumer_meter"
                    if "HTCT" in m: return "HTCT-Consumer_meter"
            return None

        summary = {
            "total_mi": _empty_bucket(),
            "total_sat": _empty_bucket(),
            "total_lumpsum_invoice": _empty_bucket(),
            "total_pmpm_invoice": _empty_bucket()
        }

        for r in c_rows:
            cat = r[0]
            mtype = r[1]
            t_mi = int(r[2] or 0)
            t_sat = int(r[3] or 0)
            t_li = int(r[4] or 0)
            t_pi = int(r[5] or 0)

            if category_param in ("feeder", "dt"):
                summary["total_mi"] += t_mi
                summary["total_sat"] += t_sat
                summary["total_lumpsum_invoice"] += t_li
                summary["total_pmpm_invoice"] += t_pi
            else:
                key = _category_key(cat, mtype)
                if key:
                    for b_name, b_val in [
                        ("total_mi", t_mi),
                        ("total_sat", t_sat),
                        ("total_lumpsum_invoice", t_li),
                        ("total_pmpm_invoice", t_pi)
                    ]:
                        if key in summary[b_name]:
                            summary[b_name][key] += b_val
                        summary[b_name]["total"] += b_val

        comparison_map = {}
        for r in cmp_rows:
            label = str(r[0] or "Unknown").strip()
            cat = r[1]
            mtype = r[2]
            t_mi = int(r[3] or 0)
            t_sat = int(r[4] or 0)
            t_li = int(r[5] or 0)
            t_pi = int(r[6] or 0)

            if label not in comparison_map:
                comparison_map[label] = {
                    "label": label,
                    "total_mi": _empty_bucket(),
                    "total_sat": _empty_bucket(),
                    "total_lumpsum_invoice": _empty_bucket(),
                    "total_pmpm_invoice": _empty_bucket()
                }
            
            target = comparison_map[label]

            if category_param in ("feeder", "dt"):
                target["total_mi"] += t_mi
                target["total_sat"] += t_sat
                target["total_lumpsum_invoice"] += t_li
                target["total_pmpm_invoice"] += t_pi
            else:
                key = _category_key(cat, mtype)
                if key:
                    for b_name, b_val in [
                        ("total_mi", t_mi),
                        ("total_sat", t_sat),
                        ("total_lumpsum_invoice", t_li),
                        ("total_pmpm_invoice", t_pi)
                    ]:
                        if key in target[b_name]:
                            target[b_name][key] += b_val
                        target[b_name]["total"] += b_val

        comparison = [v for k, v in sorted(comparison_map.items())]

        return {
            "summary": summary,
            "comparison": comparison
        }


    def get_revenue_realized_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        KPI 12: Revenue Realized summary — KPI-10-style ``{summary, comparison}``.

        Nesting per ``category``:
        - ``consumer`` → each of the four totals nests by consumer meter-type buckets + ``total``.
        - ``total`` / ``all`` → each field nests by CONSUMER / FEEDER / DT + ``total``.
        - ``feeder`` / ``dt`` → each field is a flat int.
        """
        category_param = str(filters.get("category") or "total").lower()

        if category_param == "consumer":
            return self._revenue_realized_nested(
                filters,
                sub_keys=CONSUMER_SUB_KEYS,
                bucket_fn=lambda cat, mt: CONSUMER_SUBCATEGORY_MAP.get(mt),
            )

        if category_param in ("total", "all"):
            def _cat_bucket(cat, _mt):
                up = (cat or "").strip().upper()
                return up if up in CATEGORY_KEYS else None

            return self._revenue_realized_nested(
                filters,
                sub_keys=CATEGORY_KEYS,
                bucket_fn=_cat_bucket,
            )

        return self._revenue_realized_flat(filters)


    def get_revenue_ageing_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """KPI 13: Revenue Ageing — KPI-6-style ``summary`` + ``comparison`` (no period/category tree breakdown)."""
        duration = (filters.get("duration") or filters.get("period") or "as_on").lower()
        if duration in ("as", "ason", "snapshot"):
            duration = "as_on"
        level = (filters.get("level") or "discom").lower()
        project = (filters.get("project") or "all").lower()

        category_map = {"consumer": "CONSUMER", "feeder": "FEEDER", "dt": "DT", "dtr": "DT"}
        cat_raw = (filters.get("category") or "").strip().lower()
        meter_cat_mapped = category_map.get(cat_raw) if cat_raw else None

        raw_cat_scope = (filters.get("category") or filters.get("meter_category") or "total")
        category_param = str(raw_cat_scope).strip().lower()
        if category_param in ("all", "total", ""):
            category_param = "total"
        elif category_param == "dtr":
            category_param = "dt"
        elif category_param not in ("consumer", "feeder", "dt"):
            category_param = "total"

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

        c_rows = q.with_entities(
            RevenueAgeing.meter_category,
            RevenueAgeing.new_meter_type,
            func.sum(RevenueAgeing.age_0_30),
            func.sum(RevenueAgeing.age_31_60),
            func.sum(RevenueAgeing.age_61_90),
            func.sum(RevenueAgeing.age_90_plus),
        ).group_by(RevenueAgeing.meter_category, RevenueAgeing.new_meter_type).all()

        def _empty_bucket():
            if category_param == "consumer":
                return {k: 0 for k in CONSUMER_SUB_KEYS + ["total"]}
            if category_param == "total":
                return {k: 0 for k in ("CONSUMER", "FEEDER", "DT", "total")}
            return 0

        def _category_key(row_cat, row_meter_type):
            cat = str(row_cat).upper() if row_cat else "UNKNOWN"
            if category_param == "consumer" and cat == "CONSUMER":
                return CONSUMER_SUBCATEGORY_MAP.get(row_meter_type)
            if category_param == "total":
                return cat if cat in CATEGORY_KEYS else None
            return None

        summary = {
            "age_0_30": _empty_bucket(),
            "age_31_60": _empty_bucket(),
            "age_61_90": _empty_bucket(),
            "age_90_plus": _empty_bucket(),
            "total_pending": 0,
        }

        for r in c_rows:
            a0, a31, a61, a90 = int(r[2] or 0), int(r[3] or 0), int(r[4] or 0), int(r[5] or 0)
            summary["total_pending"] += a0 + a31 + a61 + a90
            if category_param in ("feeder", "dt"):
                summary["age_0_30"] += a0
                summary["age_31_60"] += a31
                summary["age_61_90"] += a61
                summary["age_90_plus"] += a90
            else:
                key = _category_key(r[0], r[1])
                if key:
                    for b_name, b_val in (
                        ("age_0_30", a0),
                        ("age_31_60", a31),
                        ("age_61_90", a61),
                        ("age_90_plus", a90),
                    ):
                        if key in summary[b_name]:
                            summary[b_name][key] += b_val
                        summary[b_name]["total"] += b_val

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

        if category_param in ("feeder", "dt"):
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
        else:
            comp_rows = (
                q.with_entities(
                    group_expr.label("label"),
                    RevenueAgeing.meter_category,
                    RevenueAgeing.new_meter_type,
                    func.sum(RevenueAgeing.age_0_30),
                    func.sum(RevenueAgeing.age_31_60),
                    func.sum(RevenueAgeing.age_61_90),
                    func.sum(RevenueAgeing.age_90_plus),
                )
                .group_by(group_expr, RevenueAgeing.meter_category, RevenueAgeing.new_meter_type)
                .order_by("label")
                .all()
            )
            comparison_map: Dict[str, Any] = {}
            for r in comp_rows:
                label = str(r[0]) if r[0] is not None else "Unknown"
                a0, a31, a61, a90 = int(r[3] or 0), int(r[4] or 0), int(r[5] or 0), int(r[6] or 0)
                if label not in comparison_map:
                    comparison_map[label] = {
                        "label": label,
                        "age_0_30": _empty_bucket(),
                        "age_31_60": _empty_bucket(),
                        "age_61_90": _empty_bucket(),
                        "age_90_plus": _empty_bucket(),
                        "total_pending": 0,
                    }
                target = comparison_map[label]
                target["total_pending"] += a0 + a31 + a61 + a90
                key = _category_key(r[1], r[2])
                if key:
                    for b_name, b_val in (
                        ("age_0_30", a0),
                        ("age_31_60", a31),
                        ("age_61_90", a61),
                        ("age_90_plus", a90),
                    ):
                        if key in target[b_name]:
                            target[b_name][key] += b_val
                        target[b_name]["total"] += b_val
            comparison = sorted(comparison_map.values(), key=lambda x: x["label"])

        return {"summary": summary, "comparison": comparison}

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
        
        # Handle category alias and map to proper meter_category values.
        category_map = {"consumer": "CONSUMER", "feeder": "FEEDER"}
        raw_category = (base_filters.pop("category", None) or base_filters.pop("meter_category", None) or "total").lower()
        if raw_category in ("all", ""):
            raw_category = "total"
            
        if raw_category in category_map:
            base_filters["meter_category"] = category_map[raw_category]
        elif raw_category == "dt":
            base_filters["meter_category"] = None
        
        q = self._apply_filters(q, DefectiveMeters, base_filters)
        if raw_category == "dt":
            q = q.filter(func.lower(func.trim(DefectiveMeters.meter_category)).in_(["dt", "dtr"]))
        
        q = q.filter(DefectiveMeters.period_type == duration)
        
        if project == "all" or not project:
            q = q.filter(func.upper(func.trim(DefectiveMeters.project)).in_(["AGRA", "KASHI", "TRIVENI"]))
        else:
            q = q.filter(func.upper(func.trim(DefectiveMeters.project)) == project.upper())

        if start_date:
            q = q.filter(func.to_date(DefectiveMeters.period_value, "DD-MM-YY") >= func.to_date(str(start_date), "YYYY-MM-DD"))
        if end_date:
            q = q.filter(func.to_date(DefectiveMeters.period_value, "DD-MM-YY") <= func.to_date(str(end_date), "YYYY-MM-DD"))
        
        def _category_key(cat, mtype):
            cat = str(cat or "UNKNOWN").strip().upper()
            if raw_category == "consumer":
                if cat == "CONSUMER":
                    return CONSUMER_SUBCATEGORY_MAP.get(mtype)
            elif raw_category == "total":
                return cat if cat in CATEGORY_KEYS else None
            return None

        def _empty_bucket():
            if raw_category == "consumer":
                return {k: 0 for k in CONSUMER_SUB_KEYS + ["total"]}
            if raw_category == "total":
                return {k: 0 for k in ("CONSUMER", "FEEDER", "DT", "total")}
            return 0

        entities = [
            DefectiveMeters.meter_category,
            DefectiveMeters.new_meter_type,
            func.sum(case((DefectiveMeters.defective_type == 'Meter Burnt', DefectiveMeters.meter_count), else_=0)),
            func.sum(case((DefectiveMeters.defective_type == 'Meter Faulty', DefectiveMeters.meter_count), else_=0)),
            func.sum(case((DefectiveMeters.defective_type == 'Others', DefectiveMeters.meter_count), else_=0))
        ]
        
        c_rows = q.with_entities(*entities).group_by(DefectiveMeters.meter_category, DefectiveMeters.new_meter_type).all()
        
        summary = {
            "total_defective": _empty_bucket(),
            "total_burnt": _empty_bucket(),
            "total_faulty": _empty_bucket(),
            "total_others": _empty_bucket()
        }

        for r in c_rows:
            burnt = int(r[2] or 0)
            faulty = int(r[3] or 0)
            others = int(r[4] or 0)
            total = burnt + faulty + others
            
            if raw_category in ("feeder", "dt"):
                summary["total_burnt"] += burnt
                summary["total_faulty"] += faulty
                summary["total_others"] += others
                summary["total_defective"] += total
            else:
                key = _category_key(r[0], r[1])
                if key:
                    for b_name, b_val in (
                        ("total_burnt", burnt),
                        ("total_faulty", faulty),
                        ("total_others", others),
                        ("total_defective", total)
                    ):
                        if key in summary[b_name]:
                            summary[b_name][key] += b_val
                        summary[b_name]["total"] += b_val

        p_entities = [DefectiveMeters.period_value] + entities
        p_rows = q.with_entities(*p_entities).group_by(DefectiveMeters.period_value, DefectiveMeters.meter_category, DefectiveMeters.new_meter_type).all()
        
        from datetime import datetime
        period_map = {}
        for r in p_rows:
            pv = str(r[0] or "")
            burnt = int(r[3] or 0)
            faulty = int(r[4] or 0)
            others = int(r[5] or 0)
            total = burnt + faulty + others
            
            if pv not in period_map:
                try:
                    dt = datetime.strptime(pv, "%d-%m-%y")
                    pv_norm = dt.strftime("%Y-%m-%d")
                    sort_date = dt.date()
                except Exception:
                    pv_norm = pv
                    sort_date = datetime.min.date()
                    
                period_map[pv] = {
                    "period_value": pv_norm, 
                    "sort_date": sort_date,
                    "total_defective": _empty_bucket(),
                    "total_burnt": _empty_bucket(),
                    "total_faulty": _empty_bucket(),
                    "total_others": _empty_bucket()
                }
            
            target = period_map[pv]
            if raw_category in ("feeder", "dt"):
                target["total_burnt"] += burnt
                target["total_faulty"] += faulty
                target["total_others"] += others
                target["total_defective"] += total
            else:
                key = _category_key(r[1], r[2])
                if key:
                    for b_name, b_val in (
                        ("total_burnt", burnt),
                        ("total_faulty", faulty),
                        ("total_others", others),
                        ("total_defective", total)
                    ):
                        if key in target[b_name]:
                            target[b_name][key] += b_val
                        target[b_name]["total"] += b_val
            
        period_breakdown = sorted(list(period_map.values()), key=lambda x: x.pop("sort_date"))
        
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
            *entities
        ).group_by(group_expr, DefectiveMeters.meter_category, DefectiveMeters.new_meter_type).order_by("label").all()
        
        comp_map = {}
        for r in cmp_rows:
            label = str(r[0] or "Unknown").strip()
            burnt = int(r[3] or 0)
            faulty = int(r[4] or 0)
            others = int(r[5] or 0)
            total = burnt + faulty + others
            
            if label not in comp_map:
                comp_map[label] = {
                    "label": label,
                    "total_defective": _empty_bucket(),
                    "total_burnt": _empty_bucket(),
                    "total_faulty": _empty_bucket(),
                    "total_others": _empty_bucket()
                }
            
            target = comp_map[label]
            if raw_category in ("feeder", "dt"):
                target["total_burnt"] += burnt
                target["total_faulty"] += faulty
                target["total_others"] += others
                target["total_defective"] += total
            else:
                key = _category_key(r[1], r[2])
                if key:
                    for b_name, b_val in (
                        ("total_burnt", burnt),
                        ("total_faulty", faulty),
                        ("total_others", others),
                        ("total_defective", total)
                    ):
                        if key in target[b_name]:
                            target[b_name][key] += b_val
                        target[b_name]["total"] += b_val
            
        comparison = list(comp_map.values())

        return {
            "summary": summary,
            "period_breakdown": period_breakdown,
            "comparison": comparison
        }


