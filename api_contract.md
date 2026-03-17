# Smart Meter KPI API Contract

This document provides detailed technical specifications for the Smart Meter KPI API.

## 🏗️ Base URL
`https://2nbdzssr-8000.inc1.devtunnels.ms`

## 📂 Search & Pagination (Global Parameters)
Most GET endpoints support the following optional dimensions and pagination:
- **Dimensions**: `project`, `discom`, `zone`, `circle`, `division`, `subdivision`, `substation`, `feeder`, `dtr`, `new_meter_type`, `meter_category`
- **Filters**: `start_date`, `end_date` (Format: `YYYY-MM-DD`)
- **Pagination**: `limit` (default 1000, max 50000), `offset` (default 0)

---

## 📊 Dashboard API

### `GET /api/dashboard/overview`
**Description**: High-level summary of all project verticals.
- **Parameters**: `period` (daily/weekly/monthly), plus all dimensions.
- **Response**:
```json
{
  "total_meters_installed": 15420,
  "total_inventory": 50000,
  "overall_utilization_pct": 30.84,
  "total_open_complaints": 210,
  "avg_closure_time_days": 3.42,
  "kpi_breakdowns": [
    { "kpi_name": "Total MI Progress", "value": 15420 },
    { "kpi_name": "Open O&M Tickets", "value": 210 }
  ]
}
```

---

## 📏 Meter Installation (MI) KPIs

### KPI 1: MI Progress
- **Endpoints**: 
  - `GET /api/mi/progress` (Trend data)
  - `GET /api/mi/progress/summary` (Aggregated total)
- **Parameters**: `project`, `period` (daily/weekly/monthly), `start_date`, `end_date`
- **Summary Response**:
```json
{
  "total_progress": 15420,
  "category_breakdown": { "Consumer": 12000, "Feeder": 3420 },
  "period_breakdown": [
    { "period_value": "2024-08-01", "progress": 150 }
  ]
}
```

### KPI 2: MI Productivity
- **Endpoint**: `GET /api/mi/productivity`
- **Parameters**: `project`, `technician`, `period`, `start_date`, `end_date`
- **Response Row**:
```json
{
  "technician": "John Doe",
  "period_value": "2024-08-01",
  "daily_installations": 12,
  "discom": "EDC Ballia"
}
```

### KPI 3: Monthly Productivity
- **Endpoints**: 
  - `GET /api/mi/monthly-productivity/summary`
  - `GET /api/mi/monthly-productivity`
- **Parameters**: `project`, `period_value` (YYYY-MM), `start_date`, `end_date`
- **Summary Response**:
```json
{
  "total_installations": 4500,
  "period_value": "2024-08"
}
```

### KPI 4: Inventory Utilization
- **Endpoints**: 
  - `GET /api/mi/inventory-utilization` (Detail)
  - `GET /api/mi/inventory-utilization/summary` (Aggregated)
- **Parameters**: `project`, `start_date`, `end_date`
- **Description**: Tracks total stock and how much has been installed.
- **Summary Response**:
```json
{
  "total_inventory": 50000,
  "total_installed": 15000,
  "utilization_rate_pct": 30.0,
  "remaining_stock": 35000
}
```

### KPI 5: MI Pace vs Stock Availability
- **Endpoints**: 
  - `GET /api/mi/pace-vs-stock` (Detail)
  - `GET /api/mi/pace-vs-stock/summary` (Aggregated)
- **Parameters**: `project`, `start_date`, `end_date`
- **Description**: Focused on the relationship between installation pace and current stock. Defaults to **daily** view.
- **Summary Response**:
```json
{
  "total_inventory": 50000,
  "total_installed": 15000,
  "utilization_rate_pct": 30.0,
  "remaining_stock": 35000
}
```

### KPI 6: Stock Ageing
- **Endpoint**: `GET /api/mi/stock-ageing`
- **Parameters**: `project`, `start_date`, `end_date`
- **Response Row**:
```json
{
  "meter_serial_number": "MTR12345",
  "di_date": "2024-01-15",
  "installed_ts": null,
  "ageing_days": 210
}
```

### KPI 7: MI vs SAT
- **Endpoints**: 
  - `GET /api/mi/mi-vs-sat` (Historical detail)
  - `GET /api/mi/mi-vs-sat/summary` (Aggregated total with stages)
- **Parameters**: `project`, `start_date`, `end_date`
- **Description**: Compares Meter Installation progress against SAT completion, with stage-wise breakdown.
- **Summary Response**:
```json
{
  "total_mi": 1086387,
  "total_sat": 696186,
  "sat_1": 228242,
  "sat_2": 171406,
  "sat_3": 169023,
  "sat_4": 57999,
  "sat_5": 28179,
  "sat_6": 20990,
  "sat_7": 20347,
  "sat_progress_pct": 64.08
}
```

---

## 🛠️ Operations & Maintenance (O&M) KPIs

### KPI 8: Team Productivity
- **Endpoint**: `GET /api/om/productivity-team`
- **Params**: `period`, `om_category`
- **Response Row**:
```json
{
  "technician": "Team Alpha",
  "agency": "GMR Service",
  "closed_tickets": 45
}
```

### KPI 9: Productivity Trend
- **Endpoint**: `GET /api/om/productivity-trend`
- **Response Row**:
```json
{
  "closed_month": "2024-08",
  "total_closed_tickets": 1200
}
```

### KPI 10: Open Ageing
- **Endpoint**: `GET /api/om/open-ageing`
- **Response Row**:
```json
{
  "ticket_id": "TKT-998",
  "created_date": "2024-08-10T10:00:00",
  "ageing_days": 5.5
}
```

### KPI 11: Avg Closure Time
- **Endpoint**: `GET /api/om/avg-closure-time`
- **Response Row**:
```json
{
  "avg_resolution_days": 2.8,
  "period_value_closed": "2024-08"
}
```

### KPI 12: Closed Analysis
- **Endpoint**: `GET /api/om/closed-analysis`
- **Response Row**:
```json
{
  "complaint_type": "Meter No Display",
  "closed_tickets": 150
}
```

---

## 💡 Quick Tips
- All date formats are generally `YYYY-MM-DD` for daily and `YYYY-MM` for monthly.
- Use `limit` and `offset` for scrolling tables on the frontend.
- Swagger UI: `https://2nbdzssr-8000.inc1.devtunnels.ms/docs`
