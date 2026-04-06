# Smart Meter ETL & API Project Architecture

This document provides a comprehensive overview of the entire project structure. It explains the purpose of every folder, file, and major function we have created to build this dual-pipeline (ETL + API) ecosystem.

---

## 🏗️ 1. Project Root Directory
The root folder contains configuration, environment, and documentation files that drive the entire application.

- **`requirements.txt`**: Lists all Python dependencies (FastAPI, SQLAlchemy, Polars, psycopg2, Uvicorn, Pydantic, etc.) required to run the project.
- **`.env`**: Stores sensitive environment variables like `DATABASE_URL` so credentials are never hardcoded.
- **`api_contract.md` & `mi_api_reference.md`**: Technical documentation that serves as the contract between the backend API and the frontend dashboard team, detailing every endpoint, parameter, and JSON response.
- **`project_anatomy.md`**: This file! A high-level overview of how the code works.

---

## ⚙️ 2. Core Application (`src/` folder)
The `src/` directory contains all the Python code. It is strictly divided into two halves: **The ETL Pipeline** (which extracts and calculates the KPIs) and **The API Layer** (which serves the data to the frontend).

### 2.1 The Pipeline Orchestrator
- **`src/pipeline.py`**: The central brain of the ETL process. It coordinates extracting data, running transformations, and bulk-inserting it into the database.
  - `run_mi_pipeline()`: Triggers the multi-step process for Meter Installation data (3 million+ rows).
  - `run_om_pipeline()`: Triggers the extraction and loading for O&M complaints tickets.

### 2.2 Core Utilities (`src/core/` & `src/utils/`)
Shared foundational code used by both the ETL pipeline and the API.
- **`src/core/config.py`**: Uses Pydantic to load and validate variables from the `.env` file (like checking if `DATABASE_URL` exists).
- **`src/core/database.py`**: Sets up the SQLAlchemy Engine, creates Database Sessions (`get_db()`), and handles connection pooling to PostgreSQL.
- **`src/core/models.py`**: Defines the SQLAlchemy ORM classes that represent our database tables (e.g., `MIProgress`, `InventoryUtilization`, `StockAgeing`, `ComplaintsMaster`).
- **`src/utils/logger.py`**: Sets up a unified logging format so both the API and the pipeline output clean, timestamped logs.
- **`src/utils/date_parser.py`**: Contains `parse_mixed_dates()`. A highly robust Polars function that handles dirty data by parsing dates across 4+ different common formats (`DD/MM/YYYY`, `DD-Mon-YY`, etc.).

---

## 🚜 3. The ETL Pipeline (`src/extract`, `transform`, `load`)
This section runs once per day/night. It pulls raw data, calculates the heavy KPIs (like joining 4 million rows), and saves the answers.

### 3.1 Extraction (`src/extract/`)
Loads raw data from PostgreSQL source tables into lightning-fast Polars DataFrames.
- **`inventory.py` (`extract_inventory`)**: Pulls ~3.1M rows from `inventory_data`. It categorizes meters using Regex (e.g., Consumer vs Feeder) and parses `DIDate`.
- **`installation.py` (`extract_installations`)**: Pulls ~1M rows from `installation_staging`.
- **`om_complaints.py` (`extract_om`)**: Pulls raw O&M tickets from CSV or external DB sources.

### 3.2 Transformation (`src/transform/`)
Where the heavy mathematical lifting and joining happens using Polars.
- **`mi_kpis.py`**: Contains the logic for MI KPIs 1 through 7.
  - `kpi_1_progress()` & `kpi_2_3_productivity()`: Groups installations by day/month and technician.
  - `kpi_4_5_inventory_and_pace()`: Executes a massive `LEFT JOIN` between inventory and installations to calculate Utilization Rates and Remaining Stock.
  - `kpi_6_stock_ageing()`: Filters for meters that haven't been installed and subtracts their `DIDate` from today to get ageing days.
  - `kpi_7_mi_vs_sat()`: Compares installation progress against Site Acceptance Test (SAT) stages.
- **`om_kpis.py` (`transform_om_data`)**: Cleans and standardizes the dates in O&M tickets (it does *not* group them, it just cleans them for the API to group later).

### 3.3 Loading (`src/load/`)
Writes the computed DataFrames into PostgreSQL.
- **`writer.py` (`write_kpi`)**: A robust bulk-inserter. It truncates the old KPI table, matches the DataFrame columns to the SQL schema, and uses pandas `.to_sql()` to write hundreds of thousands of rows in seconds.

---

## 🌐 4. The API Layer (`src/api/`)
This section runs continuously via Uvicorn/FastAPI. It listens for requests from the frontend dashboard and returns the JSON data.

- **`src/api/main.py`**: The entry point for the FastAPI server. It includes the CORS middleware (allowing the frontend to talk to it) and registers the routers below.
- **`src/api/routes/dashboard.py`**: Features the `/api/dashboard/overview` endpoint that unifies top-level numbers (MI totals + O&M totals) into one JSON response.

- **`src/api/routes/mi.py`**: The router for Meter Installation endpoints.
  - *Trend Endpoints*: Operations like `/api/mi/progress` query the pre-calculated `MIProgress` table and apply dimension filters dynamically (`_apply_mi_filters`).
  - *Summary Endpoints*: Operations like `get_inventory_utilization_summary()` bypass the pre-aggregated tables and execute Raw SQL directly against the `inventory_data` source to ensure 100% accurate, un-inflated grand totals.

- **`src/api/routes/om.py`**: The router for O&M endpoints (`/api/om/productivity-team`, `/open-ageing`, etc.).
  - *On-the-fly execution*: Because O&M only has ~60k rows, these endpoints don't query pre-calculated tables. Instead, they dynamically aggregate the data per request using raw SQL.

- **`src/api/routes/om_kpi_queries.sql`**: A `.sql` file that houses all the raw PostgreSQL queries used by `om.py` (e.g., `GROUP BY om_category`, computing `AVG(resolution_time)`). This keeps the Python files clean of massive SQL strings.
