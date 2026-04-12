"""
SQLAlchemy ORM models base for ETL.
"""

from sqlalchemy import (
    Column, Integer, BigInteger, Float, String, Date, DateTime, Text,
    func,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# ── Helper mixin for the common MI dimension columns ────────────────────
class MIDimensionMixin:
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project = Column(String(200))
    discom = Column(String(200))
    zone = Column(String(200))
    circle = Column(String(200))
    division = Column(String(200))
    subdivision = Column(String(200))
    substation = Column(String(200))
    feeder = Column(String(200))
    dtr = Column(String(200))
    new_meter_type = Column(String(200))
    meter_category = Column(String(100))


class OMDimensionMixin:
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project = Column(String(200))
    discom = Column(String(200))
    zone = Column(String(200))
    circle = Column(String(200))
    division = Column(String(200))
    subdivision = Column(String(200))
    substation = Column(String(200))
    feeder = Column(String(200))
    dtr = Column(String(200))
    meter_category = Column(String(100))  # renamed from om_category
