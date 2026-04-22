from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from domain.interfaces import IOMRepository
from domain.entities import OMProductivityTeamEntity, ComplaintEntity
from .models import (
    OMProductivityTeam, OMProductivityTrend, OMOpenAgeing,
    OMAvgClosureTime, OMClosedAnalysis, ComplaintsMaster,
    OMTeamProductivityDashboard
)

class SQLAlchemyOMRepository(IOMRepository):
    def __init__(self, session: Session):
        self.session = session

    def _apply_filters(self, query, model, params: dict):
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
        
        # Date filtering based on model availability
        if start_date:
            if hasattr(model, "created_date"):
                query = query.filter(model.created_date >= start_date)
            elif hasattr(model, "period_value"):
                query = query.filter(model.period_value >= start_date)
        
        if end_date:
            if hasattr(model, "created_date"):
                query = query.filter(model.created_date <= end_date)
            elif hasattr(model, "period_value"):
                query = query.filter(model.period_value <= end_date)
                
        return query

    def get_productivity_team(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        q = self.session.query(OMProductivityTeam)
        q = self._apply_filters(q, OMProductivityTeam, filters)
        period = filters.get("period") or "daily"
        q = q.filter(OMProductivityTeam.period_type == period.lower())
        return q.offset(offset).limit(limit).all()

    def get_productivity_trend(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        q = self.session.query(OMProductivityTrend)
        q = self._apply_filters(q, OMProductivityTrend, filters)
        return q.offset(offset).limit(limit).all()

    def get_open_ageing(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        q = self.session.query(OMOpenAgeing)
        q = self._apply_filters(q, OMOpenAgeing, filters)
        return q.offset(offset).limit(limit).all()

    def get_avg_closure_time(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        q = self.session.query(OMAvgClosureTime)
        q = self._apply_filters(q, OMAvgClosureTime, filters)
        period = filters.get("period") or "daily"
        q = q.filter(OMAvgClosureTime.period_type == period.lower())
        return q.offset(offset).limit(limit).all()

    def get_closed_analysis(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Any]:
        q = self.session.query(OMClosedAnalysis)
        q = self._apply_filters(q, OMClosedAnalysis, filters)
        period = filters.get("period") or "daily"
        q = q.filter(OMClosedAnalysis.period_type == period.lower())
        return q.offset(offset).limit(limit).all()

    def get_productivity_team_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        from sqlalchemy import cast, Float, case
        q = self.session.query(OMTeamProductivityDashboard)

        # Filters
        project = filters.get("project")
        if project and project.lower() != "all":
            q = q.filter(OMTeamProductivityDashboard.project.ilike(project))
            
        category = filters.get("category")
        if category and category.lower() != "total":
            cat_filter = category.lower()
            if cat_filter == "dt":
                cat_filter = "dtr"
            q = q.filter(OMTeamProductivityDashboard.meter_category.ilike(cat_filter))

        for field in ["discom", "zone", "circle", "division", "subdivision", "feeder", "dtr"]:
            val = filters.get(field)
            if val:
                q = q.filter(getattr(OMTeamProductivityDashboard, field).ilike(val))
                
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")
        if start_date:
            q = q.filter(OMTeamProductivityDashboard.closed_day >= start_date)
        if end_date:
            q = q.filter(OMTeamProductivityDashboard.closed_day <= end_date)

        # -- Summary --
        daily_stats_sq = q.with_entities(
            OMTeamProductivityDashboard.closed_day,
            func.sum(OMTeamProductivityDashboard.closed_tickets).label('total_tickets'),
            (cast(func.sum(OMTeamProductivityDashboard.closed_tickets), Float) / 
             func.count(func.distinct(OMTeamProductivityDashboard.technician))).label('daily_prod')
        ).group_by(OMTeamProductivityDashboard.closed_day).subquery()
        
        summary_row = self.session.query(
            func.sum(daily_stats_sq.c.total_tickets),
            func.avg(daily_stats_sq.c.daily_prod)
        ).first()
        
        total_techs = q.with_entities(func.count(func.distinct(OMTeamProductivityDashboard.technician))).scalar() or 0
        
        summary = {
            "total_closed_tickets": int(summary_row[0] or 0) if summary_row else 0,
            "total_active_technicians": total_techs,
            "productivity_per_technician_per_day": round(float(summary_row[1] or 0), 2) if summary_row else 0.0
        }

        # -- Trend --
        duration = (filters.get("duration") or "daily").lower()
        if duration == "daily":
            date_expr = func.to_char(OMTeamProductivityDashboard.closed_day, 'YYYY-MM-DD')
        elif duration == "weekly":
            date_expr = func.to_char(func.date_trunc('week', OMTeamProductivityDashboard.closed_day), 'YYYY-MM-DD')
        elif duration == "monthly":
            date_expr = func.to_char(OMTeamProductivityDashboard.closed_day, 'YYYY-MM')
        else:
            date_expr = func.to_char(OMTeamProductivityDashboard.closed_day, 'YYYY-MM-DD')

        period_stats = q.with_entities(
            date_expr.label('period_label'),
            func.sum(OMTeamProductivityDashboard.closed_tickets),
            func.count(func.distinct(OMTeamProductivityDashboard.technician))
        ).group_by(date_expr).all()

        daily_trend_sq = q.with_entities(
            date_expr.label('period_label'),
            OMTeamProductivityDashboard.closed_day,
            (cast(func.sum(OMTeamProductivityDashboard.closed_tickets), Float) / 
             func.count(func.distinct(OMTeamProductivityDashboard.technician))).label('daily_prod')
        ).group_by(date_expr, OMTeamProductivityDashboard.closed_day).subquery()
        
        daily_avg_stats = self.session.query(
            daily_trend_sq.c.period_label,
            func.avg(daily_trend_sq.c.daily_prod)
        ).group_by(daily_trend_sq.c.period_label).all()
        
        daily_avg_dict = {row[0]: row[1] for row in daily_avg_stats}
        
        trend = []
        for row in period_stats:
            p_label = row[0]
            trend.append({
                "date": p_label,
                "total_closed_tickets": int(row[1] or 0),
                "active_technicians": int(row[2] or 0),
                "productivity_per_technician_per_day": round(float(daily_avg_dict.get(p_label, 0)), 2)
            })
        trend = sorted(trend, key=lambda x: x["date"])

        # -- Comparison --
        level = (filters.get("level") or "discom").lower()
        
        # 1. Handle common typos
        if level == "divison":
            level = "division"
        elif level == "subdivison":
            level = "subdivision"
            
        # 2. Validate against available columns
        valid_levels = {"discom", "zone", "circle", "division", "subdivision", "feeder", "dtr"}
        if level not in valid_levels:
            level = "discom"
            
        proj_filter = filters.get("project", "all").lower()
        
        if proj_filter != "all":
            label_expr = getattr(OMTeamProductivityDashboard, level)
        elif proj_filter == "all" and level == "discom":
            label_expr = OMTeamProductivityDashboard.project
        else:
            label_expr = OMTeamProductivityDashboard.project + " | " + getattr(OMTeamProductivityDashboard, level)

        comp_period_stats = q.with_entities(
            label_expr.label('label'),
            func.sum(OMTeamProductivityDashboard.closed_tickets),
            func.count(func.distinct(OMTeamProductivityDashboard.technician))
        ).filter(getattr(OMTeamProductivityDashboard, level).isnot(None)).group_by(label_expr).all()

        daily_comp_sq = q.with_entities(
            label_expr.label('label'),
            OMTeamProductivityDashboard.closed_day,
            (cast(func.sum(OMTeamProductivityDashboard.closed_tickets), Float) / 
             func.count(func.distinct(OMTeamProductivityDashboard.technician))).label('daily_prod')
        ).filter(getattr(OMTeamProductivityDashboard, level).isnot(None)).group_by(label_expr, OMTeamProductivityDashboard.closed_day).subquery()
        
        daily_comp_avg_stats = self.session.query(
            daily_comp_sq.c.label,
            func.avg(daily_comp_sq.c.daily_prod)
        ).group_by(daily_comp_sq.c.label).all()
        
        comp_avg_dict = {row[0]: row[1] for row in daily_comp_avg_stats}
        
        comparison = []
        for row in comp_period_stats:
            lbl = row[0]
            comparison.append({
                "label": str(lbl) if lbl else "Unknown",
                "total_closed_tickets": int(row[1] or 0),
                "active_technicians": int(row[2] or 0),
                "productivity_per_technician_per_day": round(float(comp_avg_dict.get(lbl, 0)), 2)
            })

        # -- Category Breakdown --
        cat_stats = q.with_entities(
            OMTeamProductivityDashboard.meter_category,
            func.sum(OMTeamProductivityDashboard.closed_tickets),
            func.count(func.distinct(OMTeamProductivityDashboard.technician))
        ).filter(OMTeamProductivityDashboard.meter_category.isnot(None)).group_by(OMTeamProductivityDashboard.meter_category).all()
        
        daily_cat_sq = q.with_entities(
            OMTeamProductivityDashboard.meter_category,
            OMTeamProductivityDashboard.closed_day,
            (cast(func.sum(OMTeamProductivityDashboard.closed_tickets), Float) / 
             func.count(func.distinct(OMTeamProductivityDashboard.technician))).label('daily_prod')
        ).filter(OMTeamProductivityDashboard.meter_category.isnot(None)).group_by(OMTeamProductivityDashboard.meter_category, OMTeamProductivityDashboard.closed_day).subquery()
        
        daily_cat_avg_stats = self.session.query(
            daily_cat_sq.c.meter_category,
            func.avg(daily_cat_sq.c.daily_prod)
        ).group_by(daily_cat_sq.c.meter_category).all()
        
        cat_avg_dict = {row[0]: row[1] for row in daily_cat_avg_stats}
        
        category_breakdown = {}
        for row in cat_stats:
            cat_name = str(row[0]) if row[0] else "Unknown"
            category_breakdown[cat_name] = {
                "total_closed_tickets": int(row[1] or 0),
                "active_technicians": int(row[2] or 0),
                "productivity_per_technician_per_day": round(float(cat_avg_dict.get(cat_name, 0)), 2)
            }

        # -- Insights --
        daily_tech_sq = q.with_entities(
            OMTeamProductivityDashboard.technician,
            OMTeamProductivityDashboard.closed_day,
            func.sum(OMTeamProductivityDashboard.closed_tickets).label('daily_prod')
        ).filter(OMTeamProductivityDashboard.technician.isnot(None)).group_by(OMTeamProductivityDashboard.technician, OMTeamProductivityDashboard.closed_day).subquery()
        
        tech_avg_stats = self.session.query(
            daily_tech_sq.c.technician,
            func.avg(daily_tech_sq.c.daily_prod).label('avg_prod')
        ).group_by(daily_tech_sq.c.technician).order_by(func.avg(daily_tech_sq.c.daily_prod).desc()).all()
        
        insights = {
            "top_performing_technician": {},
            "lowest_performing_technician": {}
        }
        
        if tech_avg_stats:
            top_t = tech_avg_stats[0]
            bot_t = tech_avg_stats[-1]
            insights["top_performing_technician"] = {
                "name": top_t[0],
                "productivity_per_technician_per_day": round(float(top_t[1]), 2)
            }
            insights["lowest_performing_technician"] = {
                "name": bot_t[0],
                "productivity_per_technician_per_day": round(float(bot_t[1]), 2)
            }

        return {
            "summary": summary,
            "insights": insights,
            "trend": trend,
            "comparison": comparison,
            "category_breakdown": category_breakdown
        }

    def get_productivity_trend_dashboard(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """KPI O&M-2: Productivity Trend Dashboard.

        Reuses sql_om_team_productivity_dashboard (same source as O&M-1)
        to compute monthly trend with per-technician-per-day productivity.
        """
        from sqlalchemy import cast, Float, case, extract

        q = self.session.query(OMTeamProductivityDashboard)

        # -- Filters (same logic as O&M-1) --
        project = filters.get("project")
        if project and project.lower() != "all":
            q = q.filter(OMTeamProductivityDashboard.project.ilike(project))

        category = filters.get("category")
        if category and category.lower() != "total":
            cat_filter = category.lower()
            if cat_filter == "dt":
                cat_filter = "dtr"
            q = q.filter(OMTeamProductivityDashboard.meter_category.ilike(cat_filter))

        for field in ["discom", "zone", "circle", "division", "subdivision", "feeder", "dtr"]:
            val = filters.get(field)
            if val:
                q = q.filter(getattr(OMTeamProductivityDashboard, field).ilike(val))

        start_date = filters.get("start_date")
        end_date = filters.get("end_date")
        if start_date:
            q = q.filter(OMTeamProductivityDashboard.closed_day >= start_date)
        if end_date:
            q = q.filter(OMTeamProductivityDashboard.closed_day <= end_date)

        # -- Month expression --
        month_expr = func.to_char(OMTeamProductivityDashboard.closed_day, 'YYYY-MM')

        # ── SUMMARY ──────────────────────────────────────────────────
        # Step 1: daily prod per day = tickets / distinct technicians
        daily_sq = q.with_entities(
            OMTeamProductivityDashboard.closed_day,
            month_expr.label('month'),
            func.sum(OMTeamProductivityDashboard.closed_tickets).label('day_tickets'),
            (cast(func.sum(OMTeamProductivityDashboard.closed_tickets), Float) /
             func.count(func.distinct(OMTeamProductivityDashboard.technician))).label('daily_prod')
        ).group_by(OMTeamProductivityDashboard.closed_day, month_expr).subquery()

        # Step 2: monthly avg of daily_prod
        monthly_sq = self.session.query(
            daily_sq.c.month,
            func.sum(daily_sq.c.day_tickets).label('month_tickets'),
            func.count(daily_sq.c.closed_day).label('active_days'),
            func.avg(daily_sq.c.daily_prod).label('monthly_prod')
        ).group_by(daily_sq.c.month).subquery()

        # Step 3: overall summary
        summary_row = self.session.query(
            func.sum(monthly_sq.c.month_tickets),
            func.count(monthly_sq.c.month),
            func.avg(monthly_sq.c.monthly_prod)
        ).first()

        summary = {
            "total_closed_tickets": int(summary_row[0] or 0) if summary_row else 0,
            "total_active_months": int(summary_row[1] or 0) if summary_row else 0,
            "avg_monthly_productivity_per_technician_per_day": round(float(summary_row[2] or 0), 2) if summary_row else 0.0
        }

        # ── TREND (per month) ────────────────────────────────────────
        # daily subquery for avg_active_technicians per month
        daily_tech_sq = q.with_entities(
            month_expr.label('month'),
            OMTeamProductivityDashboard.closed_day,
            func.count(func.distinct(OMTeamProductivityDashboard.technician)).label('day_techs'),
            func.sum(OMTeamProductivityDashboard.closed_tickets).label('day_tickets'),
            (cast(func.sum(OMTeamProductivityDashboard.closed_tickets), Float) /
             func.count(func.distinct(OMTeamProductivityDashboard.technician))).label('daily_prod')
        ).group_by(month_expr, OMTeamProductivityDashboard.closed_day).subquery()

        trend_rows = self.session.query(
            daily_tech_sq.c.month,
            func.sum(daily_tech_sq.c.day_tickets).label('total_tickets'),
            func.count(daily_tech_sq.c.closed_day).label('active_days'),
            func.avg(daily_tech_sq.c.day_techs).label('avg_techs'),
            func.avg(daily_tech_sq.c.daily_prod).label('prod')
        ).group_by(daily_tech_sq.c.month).order_by(daily_tech_sq.c.month).all()

        trend = []
        for row in trend_rows:
            trend.append({
                "month": row[0],
                "total_closed_tickets": int(row[1] or 0),
                "active_days": int(row[2] or 0),
                "avg_active_technicians": round(float(row[3] or 0), 2),
                "productivity_per_technician_per_day": round(float(row[4] or 0), 2)
            })

        # ── COMPARISON ───────────────────────────────────────────────
        level = (filters.get("level") or "discom").lower()
        if level == "divison":
            level = "division"
        elif level == "subdivison":
            level = "subdivision"
        valid_levels = {"discom", "zone", "circle", "division", "subdivision", "feeder", "dtr"}
        if level not in valid_levels:
            level = "discom"

        proj_filter = filters.get("project", "all").lower()
        if proj_filter != "all":
            label_expr = getattr(OMTeamProductivityDashboard, level)
        elif proj_filter == "all" and level == "discom":
            label_expr = OMTeamProductivityDashboard.project
        else:
            label_expr = OMTeamProductivityDashboard.project + " | " + getattr(OMTeamProductivityDashboard, level)

        comp_daily_sq = q.with_entities(
            label_expr.label('label'),
            OMTeamProductivityDashboard.closed_day,
            (cast(func.sum(OMTeamProductivityDashboard.closed_tickets), Float) /
             func.count(func.distinct(OMTeamProductivityDashboard.technician))).label('daily_prod')
        ).filter(
            getattr(OMTeamProductivityDashboard, level).isnot(None)
        ).group_by(label_expr, OMTeamProductivityDashboard.closed_day).subquery()

        comp_rows = self.session.query(
            comp_daily_sq.c.label,
            func.avg(comp_daily_sq.c.daily_prod)
        ).group_by(comp_daily_sq.c.label).all()

        comparison = []
        for row in comp_rows:
            comparison.append({
                "label": str(row[0]) if row[0] else "Unknown",
                "productivity_per_technician_per_day": round(float(row[1] or 0), 2)
            })

        # ── CATEGORY BREAKDOWN ───────────────────────────────────────
        cat_daily_sq = q.with_entities(
            OMTeamProductivityDashboard.meter_category,
            OMTeamProductivityDashboard.closed_day,
            (cast(func.sum(OMTeamProductivityDashboard.closed_tickets), Float) /
             func.count(func.distinct(OMTeamProductivityDashboard.technician))).label('daily_prod')
        ).filter(
            OMTeamProductivityDashboard.meter_category.isnot(None)
        ).group_by(OMTeamProductivityDashboard.meter_category, OMTeamProductivityDashboard.closed_day).subquery()

        cat_rows = self.session.query(
            cat_daily_sq.c.meter_category,
            func.avg(cat_daily_sq.c.daily_prod)
        ).group_by(cat_daily_sq.c.meter_category).all()

        category_breakdown = {}
        for row in cat_rows:
            cat_name = str(row[0]) if row[0] else "Unknown"
            category_breakdown[cat_name] = {
                "avg_monthly_productivity_per_technician_per_day": round(float(row[1] or 0), 2)
            }

        return {
            "summary": summary,
            "trend": trend,
            "comparison": comparison,
            "category_breakdown": category_breakdown
        }



    def save_productivity_team(self, entities: List[OMProductivityTeamEntity]):
        pass
