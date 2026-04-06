"""
FastAPI application — Smart Meter KPI API.
"""

import sys
import os
from pathlib import Path

# Ensure src/ is on the Python path
SRC_DIR = str(Path(__file__).resolve().parent.parent.parent)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Use absolute imports relative to src
from adapters.api.routes import mi, om, dashboard

app = FastAPI(
    title="Smart Meter ETL API",
    description="API for accessing pre-calculated Smart Meter KPIs (Clean Architecture)",
    version="2.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dashboard.router)
app.include_router(mi.router)
app.include_router(om.router)

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "Smart Meter KPI API", "architecture": "Clean Architecture"}

@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
