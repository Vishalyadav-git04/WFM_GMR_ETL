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

INSTALL_FILE = INPUT_DIR / "installation_merged 123.csv"
INVENTORY_FILE = INPUT_DIR / "inventory_merged 2.csv"

# Source Database Tables
INSTALL_TABLE = "new_installation_data"
INVENTORY_TABLE = "new_inventory_data"

# O&M complaint files
OM_FILES = {
    "Consumer": {
        "closed": INPUT_DIR / "Consumer closed compl.csv",
        "open": INPUT_DIR / "Consumer non closed compl.csv",
    },
    "Feeder": {
        "closed": INPUT_DIR / "Feeder closed compl.csv",
        "open": INPUT_DIR / "Feeder non closed compl.csv",
    },
    "DT": {
        "closed": INPUT_DIR / "DT closed compl.csv",
        "open": INPUT_DIR / "DT non closed compl.csv",
    },
}

# ── Database ─────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is not set. "
        "Please ensure it is defined in your .env file."
    )

# ── Dimension Columns ────────────────────────────────────────────────────
MI_DIMENSIONS = [
    "Project",
    "Discom",
    "Zone",
    "Circle",
    "Division",
    "SubDivision",
    "SubStation",
    "Feeder",
    "DTR",
    "newMeterType",
    "MeterCategory",
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
