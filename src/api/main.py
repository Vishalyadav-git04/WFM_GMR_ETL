"""
FastAPI application — Smart Meter KPI API.
"""

import sys
from pathlib import Path

# Ensure src/ is on the Python path so all imports resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import mi, om, dashboard

app = FastAPI(
    title="Smart Meter ETL API",
    description="API for accessing pre-calculated Smart Meter KPIs",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
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
    return {"status": "ok", "service": "Smart Meter KPI API"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
