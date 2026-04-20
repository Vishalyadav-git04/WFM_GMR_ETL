from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from domain.interfaces import IOMRepository
from domain.entities import OMProductivityTeamEntity, ComplaintEntity
from .models import (
    OMProductivityTeam, OMProductivityTrend, OMOpenAgeing,
    OMAvgClosureTime, OMClosedAnalysis, ComplaintsMaster
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



    def save_productivity_team(self, entities: List[OMProductivityTeamEntity]):
        pass
