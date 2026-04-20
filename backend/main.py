import sys
import os
from pathlib import Path

# Ensure backend/src is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from adapters.api.routes import mi, om

ROOT_PATH = os.getenv("ROOT_PATH", "/mdms")

app = FastAPI(
    title="Smart Meter Backend API",
    description="Dedicated Backend Service for Smart Meter KPIs",
    version="2.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    root_path=ROOT_PATH,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mi.router)
app.include_router(om.router)

@app.get("/")
def root():
    return {"status": "ok", "service": "Smart Meter Backend API"}

@app.get("/health")
def health():
    return {"status": "healthy"}
