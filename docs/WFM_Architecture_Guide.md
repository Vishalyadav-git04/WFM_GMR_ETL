# WFM KPI Architecture & Strategy Guide

## Overview
This document outlines the architectural blueprint for the Smart Meter Work Force Management (WFM) ecosystem. The project is responsible for receiving daily data regarding **Meter Installation (MI)** and **Operations & Maintenance (O&M)** complaints, performing heavy ETL (Extract, Transform, Load) operations to calculate standard Key Performance Indicators (KPIs), and finally serving those calculated answers via a lightning-fast REST API to the frontend dashboard.

---

## 🏗️ High-Level Architecture Flow
The system acts as a dual-engine machine:
1. **The Backend ETL Engine:** Wakes up daily, fetches huge payloads from external APIs, crunches the numbers (averages, groups, ageings), and saves the tiny "answers."
2. **The Frontend API Server:** Runs 24/7, listens to the frontend dashboard, and instantly returns the pre-calculated answers.

```mermaid
graph TD
    A[External Source APIs (Daily)] -->|Extract JSON/CSV| B(Python Polars Memory)
    B -->|Transform & Clean Data| C(Calculate KPIs)
    C -->|Group by Dimension| D(Pre-Calculated Summary Tables)
    D -->|Load| E[(PostgreSQL Database)]
    F[Frontend Dashboard] -->|HTTP GET Request| G[FastAPI Application]
    G -.->|Query Summary Table| E
    E -.->|Milliseconds Response| G
    G -->|Serve JSON Data| F
```

---

## ⚙️ How We Calculate KPIs (The Data Journey)

### 1. Data Ingestion (The API Pull)
When we receive data via the external provider's API, the ETL pipeline first parses the payload. 
- *Instead of downloading 9 different Excel files per day*, the Python orchestration script (e.g., `src/pipeline.py`) makes a network call to the provider.
- It pulls only the new or updated tickets/installations for that specific day.
- Using an "upsert" strategy, it inserts these new raw records into our permanent staging tables (`inventory_data`, `complaints_master`). 
- The data is labeled automatically (e.g., mapping a specific `Discom` to the Agra `Project`).

### 2. The Transformation Engine (`src/transform/`)
Once raw data is captured, we must turn millions of individual rows into high-level dashboard metrics (KPIs). We use **Polars** (an extremely fast Python dataframe library) to do the heavy lifting in Python memory instead of straining the database.
- **MI Example:** To find the "Monthly MI Productivity," the script pulls 1 million installation rows, groups them by `install_month`, `discom`, and `technician`, and counts them.
- **O&M Example:** To find the "Average Closure Time," the script pulls the `complaints_master` table, groups tickets by `om_category` and `closed_month`, and leverages date-math to find the average hours-to-close.

### 3. Loading the Answers (`src/load/`)
The result of the transformation step is a series of tiny tables containing the final KPI answers (e.g., `August: 450 Tickets, 2.3 Days Avg`).
- We use a function (`write_kpi()`) to save each distinct answer sheet into its own dedicated PostgreSQL table (e.g., `om_avg_closure_time`, `mi_productivity`).

### 4. Serving the View (`src/api/`)
Because the heavy math was already done by the nighttime ETL engine, the FastAPI application running during the day does absolutely no calculation.
- When the frontend calls `/api/om/avg-closure-time`, the `src/api/routes/om.py` router simply runs a standard `SELECT * FROM om_avg_closure_time` query.
- **Result:** Whether you have 10 thousand or 10 million raw tickets in your system, the dashboard loads instantly in 15 milliseconds.

---

## 🛠️ Codebase Structure (What Does What)

- **`src/pipeline.py`**: The "Boss" script. It tells the Extract, Transform, and Load steps when to run in chronological order.
- **`src/core/models.py`**: The architectural map of the PostgreSQL database. Defines exactly what columns exist in our KPI summary tables.
- **`src/extract/`**: Where we write the scripts that actually talk to the external daily APIs and fetch the new JSON/CSV payloads.
- **`src/transform/`**: Where we write the mathematical formulas and `group_by` statements for calculating a specific KPI (e.g., `kpi_1_progress()`).
- **`src/api/routes/`**: Contains the REST API endpoints that the frontend developers use to draw their graphs. 

---

## 🔗 The GitHub & Version Control Strategy
Because this pipeline and API share the exact same database architecture (`src/core/models.py`) and configuration (`src/core/config.py`), they belong in a **Monorepo** (a single GitHub repository).

**You MUST push both the ETL code and the API code to the same GitHub repository.**

Every folder inside `smart_meter_etl` must be pushed except for sensitive hidden files. This ensures any future developer pulling the repo instantly has both the engine that calculates the data and the server that shows the data.
