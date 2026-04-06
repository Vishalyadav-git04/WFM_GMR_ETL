# Smart Meter KPI Backend & ETL

This repository contains the backend API and ETL pipeline for tracking Smart Meter KPI metrics (MI & O&M), restructured for a professional, Domain-Driven architecture.

## 🚀 Quick Setup

### 1. Prerequisites
- **Python**: 3.11+
- **Database**: PostgreSQL (accessible via `DATABASE_URL`)
- **Docker** (Optional, for containerized deployment)

### 2. Environment Configuration
Copy the `.env.example` to a new file named `.env`:
```bash
cp .env.example .env
# Edit .env and set your DATABASE_URL
```

### 3. Installation
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Unix/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

---

## 🖥️ Running the Application

### Option A: Local Development
Start the FastAPI server:
```bash
# From the project root
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```
- **Swagger UI**: `http://localhost:8000/docs`

### Option B: Docker Deployment
```bash
docker-compose up --build -d
```

---

## ⚙️ Running the ETL Pipeline

Refresh KPI tables from raw staging data:
```bash
# Run All Pipelines
python src/pipeline.py --pipeline all

# Run specific domain
python src/pipeline.py --pipeline [mi | om]
```

---

## 📂 Project Structure

- `src/core/`: Foundational logic (database, models, configuration, utilities).
- `src/modules/mi/`: Domain-specific logic for Meter Installation (MI) KPIs.
- `src/modules/om/`: Domain-specific logic for Operations & Maintenance (O&M) KPIs.
- `src/api/`: FastAPI routes and schemas.
- `docs/`: Technical documentation and architecture guides.
- `Dockerfile` & `docker-compose.yml`: Containerization for production-ready deployment.

## 📊 Core APIs

- `GET /api/dashboard/overview`: Project-wide summary (Unified Dashboard).
- `GET /api/mi/progress/summary`: Installation trends.
- `GET /api/om/productivity-team`: O&M ticket closure metrics.

For detailed endpoint definitions, see `docs/api_contract.md`.
