"""
Central configuration for the Smart Meter ETL pipeline.
All paths, database settings, dimension lists, and mappings live here.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths: Check local first, then project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
if not DATA_DIR.exists():
    DATA_DIR = BASE_DIR.parent / "data"
INPUT_DIR = DATA_DIR / "input"

# Source Database Tables
MI_SOURCE_TABLE = "unified_installation_inventory_data"
OM_SOURCE_TABLE = "unified_complaints"

# ── Database ─────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is not set. "
        "Please ensure it is defined in your .env file."
    )

# ── Dimension Columns ────────────────────────────────────────────────────
MI_DIMENSIONS = [
    "project",
    "discom",
    "zone",
    "circle",
    "division",
    "subdivision",
    "substation",
    "feeder",
    "dtr",
    "metertype",
    "connection_type",
]

OM_DIMENSIONS = [
    "Project",
    "Discom",
    "Zone",
    "Circle",
    "Division",
    "SubDivision",
    "SubStation",
    "Feeder",
    "DTR",
    "MeterCategory",
]
