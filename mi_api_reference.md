# MI KPI API Reference Guide

This document provides a detailed list of all API endpoints for the 7 Meter Installation (MI) KPIs, including examples of how to apply filters like `project`, `financial year`, and geographical dimensions.

## Base URL
`http://127.0.0.1:8000`

---

## 🛠 Available Filtering Parameters

All endpoints (except Stock Ageing) support the following query parameters:

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `project` | String | **[NEW]** Name of the project (e.g., `agra`) |
| `period` | String | `daily`, `weekly`, or `monthly` |
| `start_date` | Date | Filter from date (Format: `YYYY-MM-DD`) |
| `end_date` | Date | Filter to date (Format: `YYYY-MM-DD`) |
| `discom` | String | Name of the Discom |
| `zone` | String | Name of the Zone |
| `circle` | String | Name of the Circle |
| `division` | String | Name of the Division |
| `subdivision`| String | Name of the Subdivision |
| `substation` | String | Name of the Substation |
| `meter_category`| String | `LTCT`, `1 Phase`, `3 Phase`, etc. |

---

## 📈 MI KPI Endpoints

### 1. MI Progress (KPI 1)
Tracks the trend of meter installations over time.
- **Trend Data**: `/api/mi/progress`
- **Aggregated Summary**: `/api/mi/progress/summary`
- **Test URL (Project + FY 2024-25)**:
  `http://127.0.0.1:8000/api/mi/progress/summary?project=agra&start_date=2024-04-01&end_date=2025-03-31&period=monthly`

### 2. Technician Productivity (KPI 2)
Tracks installations performed by specific technicians.
- **Endpoint**: `/api/mi/productivity`
- **Test URL (Specific Project)**:
  `http://127.0.0.1:8000/api/mi/productivity?project=agra&period=daily`

### 3. Monthly Productivity (KPI 3)
Focuses on monthly installation targets and achievements.
- **Summary**: `/api/mi/monthly-productivity/summary`
- **Detail**: `/api/mi/monthly-productivity`
- **Test URL (Specific Month)**:
  `http://127.0.0.1:8000/api/mi/monthly-productivity/summary?period_value=2025-02&project=agra`

### 4. Inventory Utilization (KPI 4)
Compares total inventory vs. number of meters installed.
- **Trend**: `/api/mi/inventory-utilization`
- **Summary**: `/api/mi/inventory-utilization/summary`
- **Test URL (Clean Grand Total)**:
  `http://127.0.0.1:8000/api/mi/inventory-utilization/summary?project=agra&period=monthly`

### 5. MI Pace vs Stock Availability (KPI 5)
Analyzes if installation pace aligns with available stock.
- **Endpoint**: `/api/mi/pace-vs-stock`
- **Summary**: `/api/mi/pace-vs-stock/summary`
- **Test URL (Daily Pace)**:
  `http://127.0.0.1:8000/api/mi/pace-vs-stock/summary?project=agra&period=daily`

### 6. Stock Ageing (Unutilized Stock)
- **Trend List**: `GET /api/mi/stock-ageing?limit=100`
- **Summary (Bucketed)**: `GET /api/mi/stock-ageing/summary?project=agra`
    - Returns counts in categories: `0-30 Days`, `31-90 Days`, `91-180 Days`, `181-365 Days`, `1 Year+`.
- **Filters**: `project`, `new_meter_type`, `meter_category`.
This is a snapshot KPI and does not support date filtering in the same way as others.
- **Test URL**:
  `http://127.0.0.1:8000/api/mi/stock-ageing?limit=100`

### 7. MI vs SAT Progress (KPI 7)
Compares Meter Installation progress against SAT (Site Acceptance Test) progress.
- **Endpoint**: `/api/mi/mi-vs-sat`
- **Test URL (Region Filtered)**:
  `http://127.0.0.1:8000/api/mi/mi-vs-sat?project=agra&discom=DVVNL`

---

## 🏛 Unified Dashboard Overview
Provides a high-level overview combining MI (KPI 1, 4) and O&M (Complaints).
- **Endpoint**: `/api/dashboard/overview`
- **Test URL (Everything Combined)**:
  `http://127.0.0.1:8000/api/dashboard/overview?project=agra&period=monthly`

---

## 📝 Recommendation for Financial Year (FY) Filtering
Since "Financial Year" is not a single column, use the date range parameters:

- **FY 2024-25**: `?start_date=2024-04-01&end_date=2025-03-31`
- **FY 2023-24**: `?start_date=2023-04-01&end_date=2024-03-31`
