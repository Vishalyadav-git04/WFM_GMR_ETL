# Smart Meter KPI Backend & ETL

This repository contains the backend API and ETL pipeline for tracking Smart Meter KPI metrics (MI & O&M).

## 🚀 Quick Setup

### 1. Prerequisites
- **Python**: 3.9 or higher
- **C++ Build Tools**: Required for some Python libraries (like `psycopg2`).
- **Database**: Access to the project's PostgreSQL RDS instance.

### 2. Environment Configuration
Copy the `.env.example` to a new file named `.env` and ensure the `DATABASE_URL` is correctly set.
```bash
# Example .env content
DATABASE_URL=postgresql://user:password@host:port/dbname
```

### 3. Installation
Create a virtual environment and install the required dependencies:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Activate virtual environment (Unix/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🖥️ Running the API Server

The backend is built with FastAPI. To start the server:

```bash
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```
- **Base URL**: `http://127.0.0.1:8000`
- **Interactive Documentation**: `http://127.0.0.1:8000/docs` (Swagger UI)

---

## ⚙️ Running the ETL Pipeline (Optional)

If you need to refresh the KPI tables from the raw staging data:

```bash
# Run MI Pipeline
python src/pipeline.py --pipeline mi

# Run O&M Pipeline
python src/pipeline.py --pipeline om
```

---

## 📂 Project Structure

- `src/api/`: FastAPI routes and schemas.
- `src/transform/`: KPI calculation logic (Polars based).
- `src/load/`: Database models and write logic.
- `src/extract/`: Data extraction from staging tables.
- `data/`: Local data storage (Ignored by Git).
- `api_contract.md`: Detailed endpoint definitions and example responses.

## 📊 API Documentation
For a complete list of endpoints, query parameters, and response schemas, please refer to the **[API Contract](api_contract.md)**.

### Key MI Endpoints:
- `GET /api/mi/progress/summary`: Overall MI installation count.
- `GET /api/mi/inventory-utilization/summary`: Stock vs Installed metrics.
- `GET /api/mi/mi-vs-sat/summary`: MI progress vs SAT completion (stage-wise).
- `GET /api/mi/stock-ageing`: List of unutilized meters and their days in stock.

### Key O&M Endpoints:
- `GET /api/dashboard/overview`: Project-wide summary across all verticals.
- `GET /api/om/productivity-team`: Closure counts by technician/agency.
- `GET /api/om/open-ageing`: Current backlog and ticket ageing.
