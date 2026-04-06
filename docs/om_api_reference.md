# O&M KPI API Reference Guide

This document provides a detailed list of all API endpoints for the 5 Operations & Maintenance (O&M) KPIs, including examples of how to apply filters like `project`, `period`, and geographical dimensions.

## Base URL
`http://127.0.0.1:8000`

---

## 🛠 Available Filtering Parameters

All O&M endpoints support the following query parameters:

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `project` | String | Name of the project (e.g., `agra`, `kashi`) |
| `period` | String | `daily`, `weekly`, or `monthly` |
| `start_date` | Date | Filter from date (Format: `YYYY-MM-DD`) |
| `end_date` | Date | Filter to date (Format: `YYYY-MM-DD`) |
| `discom` | String | Name of the Discom |
| `zone` | String | Name of the Zone |
| `circle` | String | Name of the Circle |
| `division` | String | Name of the Division |
| `subdivision`| String | Name of the Subdivision |
| `feeder` | String | Name of the Feeder |
| `dtr` | String | Name of the DTR |
| `meter_category`| String | `Consumer`, `Feeder`, `DTR` |
| `om_category` | String | Legacy API alias for `meter_category` |
| `limit` | Integer | Max records to return (default 1000) |
| `offset` | Integer | Pagination offset (default 0) |

---

## 🛠 O&M KPI Endpoints

### 1. Team Productivity (KPI 8)
Tracks number of closed tickets per technician and agency.
- **Endpoint**: `/api/om/productivity-team`
- **Test URL**:
  `http://127.0.0.1:8000/api/om/productivity-team?project=agra&period=monthly`

### 2. Productivity Trend (KPI 9)
Tracks the monthly trend of total closed tickets.
- **Endpoint**: `/api/om/productivity-trend`
- **Test URL**:
  `http://127.0.0.1:8000/api/om/productivity-trend?project=agra`

### 3. Open Ticket Ageing (KPI 10)
List of currently open tickets with calculated ageing in days.
- **Endpoint**: `/api/om/open-ageing`
- **Test URL**:
  `http://127.0.0.1:8000/api/om/open-ageing?limit=100`

### 4. Average Closure Time (KPI 11)
Calculates the average time (in days) taken to close tickets.
- **Endpoint**: `/api/om/avg-closure-time`
- **Test URL**:
  `http://127.0.0.1:8000/api/om/avg-closure-time?period=monthly&project=agra`

### 5. Closed Analysis (KPI 12)
Breakdown of closed tickets by complaint type and category.
- **Endpoint**: `/api/om/closed-analysis`
- **Test URL**:
  `http://127.0.0.1:8000/api/om/closed-analysis?project=agra&period=daily`

---

## 🏛 Unified Dashboard Overview
Provides a high-level overview combining MI and O&M summary stats.
- **Endpoint**: `/api/dashboard/overview`
- **Test URL**:
  `http://127.0.0.1:8000/api/dashboard/overview?project=agra`
