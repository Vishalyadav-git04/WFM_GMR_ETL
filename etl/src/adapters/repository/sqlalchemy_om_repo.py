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

    def get_open_complaints_count(self, filters: Dict[str, Any]) -> int:
        q = self.session.query(func.count(ComplaintsMaster.ticket_id))
        q = self._apply_filters(q, ComplaintsMaster, filters)
        q = q.filter(ComplaintsMaster.complaint_status != 'Closed')
        return q.scalar() or 0

    def get_avg_closure_time_metric(self, filters: Dict[str, Any]) -> float:
        # Calculate avg closure time in days from ComplaintsMaster
        q = self.session.query(func.avg(
            func.extract('epoch', (ComplaintsMaster.closed_date - ComplaintsMaster.created_date)) / 86400.0
        ))
        q = self._apply_filters(q, ComplaintsMaster, filters)
        q = q.filter(ComplaintsMaster.complaint_status == 'Closed')
        q = q.filter(ComplaintsMaster.closed_date.isnot(None))
        q = q.filter(ComplaintsMaster.created_date.isnot(None))
        return float(q.scalar() or 0.0)

    def save_productivity_team(self, entities: List[OMProductivityTeamEntity]):
        pass
