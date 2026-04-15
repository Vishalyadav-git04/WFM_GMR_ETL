# Smart Meter KPI API Contract

> **Version**: 2.0 &nbsp;|&nbsp; **Last Updated**: 2026-04-13  
> This document provides the complete technical specification for the Smart Meter KPI REST API, intended for frontend integration.

---

## 🏗️ Base URL

| Environment | URL |
| :--- | :--- |
| Dev Tunnel | `https://2nbdzssr-8000.inc1.devtunnels.ms` |
| Local | `http://localhost:8000` |

**Swagger UI**: Append `/docs` to the Base URL for interactive exploration.

---

## 🔎 Global Query Parameters

Most `GET` endpoints accept the following optional query parameters. Pass them as URL query strings (e.g. `?project=AGRA&discom=DVVNL`).

### Geographical Dimension Filters

| Parameter | Type | Example | Description |
| :--- | :--- | :--- | :--- |
| `project` | `string` | `AGRA` | Project region name |
| `discom` | `string` | `DVVNL` | Distribution Company |
| `zone` | `string` | `AGRA I` | Administrative Zone |
| `circle` | `string` | `EDC FATEHABAD` | Administrative Circle |
| `division` | `string` | `EDD BAH` | Administrative Division |
| `subdivision` | `string` | `EDSD I BAH` | Administrative Sub-Division |
| `substation` | `string` | `33/11 KV BAH TOWN` | Connected Sub-Station |
| `feeder` | `string` | `BIJOLI_251...` | Connected Feeder |
| `dtr` | `string` | `250KVA SAMARTH...` | Distribution Transformer |

### Category Filters

| Parameter | Type | Example | Description |
| :--- | :--- | :--- | :--- |
| `new_meter_type` | `string` | `1PH-STSM` | Meter hardware type |
| `meter_category` | `string` | `CONSUMER` | Connection type: `CONSUMER`, `FEEDER`, or `DT` |

### Time Filters

| Parameter | Type | Format | Description |
| :--- | :--- | :--- | :--- |
| `period` | `string` | `daily` / `weekly` / `monthly` | Aggregation granularity |
| `start_date` | `string` | `YYYY-MM-DD` | Filter records on or after this date |
| `end_date` | `string` | `YYYY-MM-DD` | Filter records on or before this date |

### Pagination

| Parameter | Type | Default | Max | Description |
| :--- | :--- | :--- | :--- | :--- |
| `limit` | `int` | `1000` | `50000` | Maximum rows to return |
| `offset` | `int` | `0` | — | Number of rows to skip |

---

## 📊 Dashboard API

### `GET /api/dashboard/overview`

Returns a unified, high-level summary combining MI and O&M metrics in a single call.

**Parameters**: `period`, plus all geographical and category filters.

**Response Schema** (`DashboardOverviewOut`):
```json
{
  "total_meters_installed": 15420,
  "total_inventory": 50000,
  "overall_utilization_pct": 30.84,
  "total_open_complaints": 210,
  "avg_closure_time_days": 3.42,
  "kpi_breakdowns": [
    { "kpi_name": "Total MI Progress", "value": 15420 },
    { "kpi_name": "Total Inventory", "value": 50000 },
    { "kpi_name": "Overall Utilization %", "value": 30.84 },
    { "kpi_name": "Open O&M Tickets", "value": 210 },
    { "kpi_name": "Avg Resolution Timeline (Days)", "value": 3.42 }
  ]
}
```

---

## 📏 Meter Installation (MI) KPIs

All MI endpoints are under the prefix `/api/mi`.

---

### KPI 1 — MI Progress

Tracks the total number of meter installations over time.

#### `GET /api/mi/progress`
Returns a paginated list of installation counts per period/region.

**Extra Parameters**: `period`, `start_date`, `end_date`, pagination.

**Response** — `List[MIProgressOut]`:
```json
[
  {
    "project": "AGRA", "discom": "DVVNL", "zone": "AGRA I",
    "circle": null, "division": null, "subdivision": null,
    "substation": null, "feeder": null, "dtr": null,
    "new_meter_type": "1PH-STSM", "meter_category": "CONSUMER",
    "period_type": "monthly",
    "period_value": "2024-08",
    "total_mi_progress": 1520
  }
]
```

#### `GET /api/mi/progress/summary`
Returns a single aggregated object with nested breakdowns by category and period.

**Response** — `MIProgressSummaryOut`:
```json
{
  "total_progress": 154200,
  "category_breakdown": {
    "CONSUMER": {
      "1PH-STSM": 120000,
      "3PLTCTSM": 5000
    },
    "FEEDER": { "HTCTPTSM": 3420 }
  },
  "period_breakdown": {
    "2024-08": {
      "CONSUMER": { "1PH-STSM": 1500) }
    }
  }
}
```

---

### KPI 2 — MI Productivity (Per Technician)

Tracks individual technician installation performance.

#### `GET /api/mi/productivity`

**Extra Parameters**: `technician`, `period`, `start_date`, `end_date`, pagination.

**Response** — `List[MIProductivityOut]`:
```json
[
  {
    "project": "AGRA", "discom": "DVVNL", "zone": "AGRA I",
    "circle": null, "division": null, "subdivision": null,
    "substation": null, "feeder": null, "dtr": null,
    "new_meter_type": "1PH-STSM", "meter_category": "CONSUMER",
    "technician": "John Doe",
    "period_type": "daily",
    "period_value": "2024-08-01",
    "daily_installations": 12
  }
]
```

---

### KPI 3 — Monthly Productivity (Location-Level)

Tracks monthly installation volume at each location.

#### `GET /api/mi/monthly-productivity`

**Extra Parameters**: `period_value` (e.g. `2024-08`), `start_date`, `end_date`, pagination.

**Response** — `List[MonthlyProductivityOut]`:
```json
[
  {
    "project": "AGRA", "discom": "DVVNL",
    "new_meter_type": "1PH-STSM", "meter_category": "CONSUMER",
    "period_type": "monthly",
    "period_value": "2024-08",
    "location_monthly_installations": 450,
    "total_monthly_installations": 4500
  }
]
```

#### `GET /api/mi/monthly-productivity/summary`

**Response** — `MonthlyProductivitySummaryOut`:
```json
{
  "total_installations": 4500,
  "period_value": "2024-08",
  "category_breakdown": { "CONSUMER": { "1PH-STSM": 3800 } },
  "period_breakdown": { "2024-08": { "CONSUMER": { "1PH-STSM": 3800 } } }
}
```

---

### KPI 4 — Inventory Utilization

Tracks stock received vs. stock installed.

#### `GET /api/mi/inventory-utilization`

**Extra Parameters**: `period`, `start_date`, `end_date`, pagination.

**Response** — `List[InventoryUtilizationOut]`:
```json
[
  {
    "project": "AGRA", "discom": "DVVNL",
    "new_meter_type": "1PH-STSM", "meter_category": "CONSUMER",
    "period_type": "monthly", "period_value": "2024-08",
    "total_inventory": 50000,
    "total_installed": 15000,
    "utilization_rate_pct": 30.0,
    "remaining_stock": 35000
  }
]
```

#### `GET /api/mi/inventory-utilization/summary`

**Response** — `InventoryUtilizationSummaryOut`:
```json
{
  "total_inventory": 50000,
  "total_installed": 15000,
  "utilization_rate_pct": 30.0,
  "remaining_stock": 35000,
  "category_breakdown": { "CONSUMER": { "1PH-STSM": { "total_inventory": 40000, "total_installed": 12000 } } },
  "period_breakdown": { "2024-08": { "CONSUMER": { "1PH-STSM": { "total_inventory": 5000 } } } }
}
```

---

### KPI 5 — MI Pace vs Stock Availability

Focused view of installation pace against stock. Defaults to **daily** granularity.

#### `GET /api/mi/pace-vs-stock`

**Parameters**: `period`, `project`, `discom`, `zone`, pagination.

**Response** — `List[InventoryUtilizationOut]` (same shape as KPI 4).

#### `GET /api/mi/pace-vs-stock/summary`

**Response** — `InventoryUtilizationSummaryOut` (same shape as KPI 4 summary).

---

### KPI 6 — Stock Ageing ⭐ _Updated_

Tracks how long dispatched meters remain uninstalled, categorized into aging buckets.

#### `GET /api/mi/stock-ageing`

Returns paginated detail rows with per-row aging bucket counts.

**Parameters**: All geographical + category filters, pagination (`limit` max 1000).

**Response** — `List[StockAgeingOut]`:
```json
[
  {
    "age_0_30": 0,
    "age_31_60": 0,
    "age_61_90": 0,
    "age_90_plus": 5
  }
]
```

#### `GET /api/mi/stock-ageing/summary` ⭐ _New Endpoint_

Returns aggregated aging bucket totals with nested breakdowns by category and by time period. **This mirrors the Revenue Ageing summary format.**

**Parameters**: All geographical + category filters, `start_date`, `end_date`.

**Response** — `StockAgeingSummaryOut`:
```json
{
  "category_breakdown": {
    "CONSUMER": {
      "1PH-STSM": {
        "age_0_30": 120,
        "age_31_60": 85,
        "age_61_90": 40,
        "age_90_plus": 1250
      },
      "3PLTCTSM": {
        "age_0_30": 10,
        "age_31_60": 5,
        "age_61_90": 2,
        "age_90_plus": 30
      }
    },
    "FEEDER": {
      "HTCTPTSM": {
        "age_0_30": 0,
        "age_31_60": 0,
        "age_61_90": 1,
        "age_90_plus": 15
      }
    }
  },
  "period_breakdown": {
    "01-09-24": {
      "CONSUMER": {
        "1PH-STSM": {
          "age_0_30": 0,
          "age_31_60": 0,
          "age_61_90": 0,
          "age_90_plus": 450
        }
      }
    },
    "01-11-24": {
      "CONSUMER": {
        "1PH-STSM": {
          "age_0_30": 0,
          "age_31_60": 0,
          "age_61_90": 0,
          "age_90_plus": 180
        }
      }
    }
  }
}
```

> **Frontend Usage**: Use `category_breakdown` for pie/bar charts showing aging distribution per meter type. Use `period_breakdown` for time-series trend charts.

---

### KPI 7 — MI vs SAT Progress

Compares Meter Installation against SAT (Site Acceptance Test) completion across 9 stages.

#### `GET /api/mi/mi-vs-sat`

**Parameters**: `project`, `discom`, pagination.

**Response** — `List[MIvsSATOut]`:
```json
[
  {
    "project": "AGRA", "discom": "DVVNL",
    "period_type": "daily", "period_value": "2024-08-01",
    "total_mi": 15420, "total_sat": 9800,
    "sat_1": 3000, "sat_2": 2500, "sat_3": 2000,
    "sat_4": 800, "sat_5": 500, "sat_6": 400,
    "sat_7": 350, "sat_8": 150, "sat_9": 100,
    "sat_progress_pct": 63.55
  }
]
```

#### `GET /api/mi/mi-vs-sat/summary`

**Response** — `MIvsSATSummaryOut`:
```json
{
  "total_mi": 1086387,
  "total_sat": 696186,
  "sat_1": 228242, "sat_2": 171406, "sat_3": 169023,
  "sat_4": 57999, "sat_5": 28179, "sat_6": 20990,
  "sat_7": 20347, "sat_8": 0, "sat_9": 0,
  "sat_progress_pct": 64.08,
  "category_breakdown": {},
  "period_breakdown": {}
}
```

---

### KPI 8 — Non-SAT Ageing

Lists installed meters that have not yet completed SAT, ordered by ageing.

#### `GET /api/mi/non-sat-ageing`

**Parameters**: `project`, pagination.

**Response** — `List[MINonSATAgeingOut]`:
```json
[
  {
    "project": "AGRA", "discom": "DVVNL",
    "meter_serial_number": "AL0502972",
    "installation_date": "2024-06-15",
    "ageing_days": 180
  }
]
```

---

### KPI 9 — Meter Journey Average Time

Shows average number of days a meter spends in each lifecycle stage.

#### `GET /api/mi/meter-journey`

**Parameters**: `project`, pagination (`limit` default 100).

**Response** — `List[MeterJourneyOut]`:
```json
[
  {
    "project": "AGRA", "discom": "DVVNL",
    "di_to_gmr": 5.2, inventory to store
    "gmr_to_agency": 3.1,store to agency , 
    "agency_to_sup": 2.0,    remove agenecny to sup keep agency to installation
    "sup_to_install": 4.5, agency to meter installation
    "install_to_sat": 12.3,meter installation to sat
    "sat_to_revenue": 8.7, sat to invoice and invocice to revenue
    "total_journey": 35.8 
  }
]
```

---

### KPI 10 — Meter Current Stage Distribution

Shows how many meters are currently at each lifecycle stage.

#### `GET /api/mi/meter-stage`

**Parameters**: `project`, pagination (`limit` default 100).

**Response** — `List[MeterStageOut]`:
```json
[
  {
    "project": "AGRA", "discom": "DVVNL",
    "current_stage": "INSTALLED",
    "meter_count": 45000
  },
  {
    "project": "AGRA", "discom": "DVVNL",
    "current_stage": "SAT_DONE",
    "meter_count": 22000
  }
]
```

---

### KPI 11 — MI vs SAT vs Invoice Funnel

Compares MI → SAT → Invoice counts as a funnel.

#### `GET /api/mi/mi-vs-sat-vs-invoice/summary`

**Parameters**: All geographical + category filters, `start_date`, `end_date`.

**Response** — `MIvsSATvsInvoiceSummaryOut`:
```json
{
  "total_mi": 1086387,
  "total_sat": 696186,
  "total_invoice": 450000,
  "category_breakdown": {},
  "period_breakdown": {}
}
```

---

### KPI 12 — Revenue Realized

Tracks revenue realization from installed meters.

#### `GET /api/mi/revenue-realized/summary`

**Parameters**: All geographical + category filters, `start_date`, `end_date`.

**Response** — `RevenueRealizedSummaryOut`:
```json
{
  "total_realized": 320000,
  "category_breakdown": { "CONSUMER": { "1PH-STSM": 280000 } },
  "period_breakdown": { "2024-08": { "CONSUMER": { "1PH-STSM": 50000 } } }
}
```

---

### KPI 13 — Revenue Ageing (SAT to Collection)

Tracks aging of revenue collection after SAT, with bucket-based breakdown.

#### `GET /api/mi/revenue-ageing/summary`

**Parameters**: All geographical + category filters, `start_date`, `end_date`.

**Response** — `RevenueAgeingSummaryOut`:
```json
{
  "category_breakdown": {
    "CONSUMER": {
      "1PH-STSM": {
        "age_0_30": 500,
        "age_31_60": 300,
        "age_61_90": 150,
        "age_90_plus": 2000
      }
    }
  },
  "period_breakdown": {
    "01-08-24": {
      "CONSUMER": {
        "1PH-STSM": { "age_0_30": 100, "age_31_60": 80, "age_61_90": 40, "age_90_plus": 600 }
      }
    }
  }
}
```

---

### KPI 14 — Defective Meters

Tracks counts of defective, burnt, and faulty meters.

#### `GET /api/mi/defective-meters/summary`

**Parameters**: All geographical + category filters, `start_date`, `end_date`.

**Response** — `DefectiveMetersSummaryOut`:
```json
{
  "total_defective": 1200,
  "total_burnt": 350,
  "total_faulty": 850,
  "category_breakdown": { "CONSUMER": { "1PH-STSM": { "defective": 1000, "burnt": 300, "faulty": 700 } } },
  "period_breakdown": {}
}
```

---

### SAT Dashboard

Regional snapshot with SAT stage-wise eligibility, achievement, and throughput.

#### `GET /api/mi/command-center/{region}`

**Path Parameter**: `region` — one of `kashi`, `agra`, `triveni`.

**Response**: A comprehensive JSON object with project-level SAT metrics. Refer to `/docs` for the full shape.

---

## 🛠️ Operations & Maintenance (O&M) KPIs

All O&M endpoints are under the prefix `/api/om`. They share these common parameters:

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `project` | `string` | Project name filter |
| `meter_category` | `string` | `CONSUMER` / `FEEDER` / `DT` |
| `om_category` | `string` | Legacy alias for `meter_category` (auto-mapped) |
| `period` | `string` | `daily` / `weekly` / `monthly` |
| `start_date` / `end_date` | `string` | Date range filter |
| `limit` / `offset` | `int` | Pagination |

Plus all geographical dimensions (`discom`, `zone`, `circle`, `division`, `subdivision`, `feeder`, `dtr`).

---

### KPI O&M-1 — Team Productivity

#### `GET /api/om/productivity-team`

**Response** — `List[OMProductivityTeamOut]`:
```json
[
  {
    "project": "AGRA", "discom": "DVVNL", "zone": "AGRA I",
    "circle": null, "division": null, "subdivision": null,
    "substation": null, "feeder": null, "dtr": null,
    "meter_category": "CONSUMER",
    "technician": "Team Alpha",
    "agency": "GMR Service",
    "period_type": "daily",
    "period_value": "2024-08-01",
    "closed_tickets": 45
  }
]
```

---

### KPI O&M-2 — Productivity Trend

#### `GET /api/om/productivity-trend`

**Response** — `List[OMProductivityTrendOut]`:
```json
[
  {
    "project": "AGRA", "discom": "DVVNL",
    "meter_category": "CONSUMER",
    "closed_month": "2024-08",
    "total_closed_tickets": 1200
  }
]
```

---

### KPI O&M-3 — Open Ticket Ageing

#### `GET /api/om/open-ageing`

**Response** — `List[OMOpenAgeingOut]`:
```json
[
  {
    "project": "AGRA", "discom": "DVVNL",
    "meter_category": "CONSUMER",
    "ticket_id": "TKT-998",
    "created_date": "2024-08-10T10:00:00",
    "ageing_days": 5.5,
    "technician": "Team Alpha",
    "agency": "GMR Service"
  }
]
```

---

### KPI O&M-4 — Average Closure Time

#### `GET /api/om/avg-closure-time`

**Extra Parameters**: `period` (daily/weekly/monthly).

**Response** — `List[OMAvgClosureTimeOut]`:
```json
[
  {
    "project": "AGRA", "discom": "DVVNL",
    "meter_category": "CONSUMER",
    "period_type": "monthly",
    "period_value_created": "2024-08",
    "period_value_closed": "2024-08",
    "avg_resolution_days": 2.8
  }
]
```

---

### KPI O&M-5 — Closed Ticket Analysis

#### `GET /api/om/closed-analysis`

**Extra Parameters**: `period`.

**Response** — `List[OMClosedAnalysisOut]`:
```json
[
  {
    "project": "AGRA", "discom": "DVVNL",
    "meter_category": "CONSUMER",
    "complaint_type": "Meter No Display",
    "complaint_category": "Hardware Fault",
    "period_type": "monthly",
    "period_value": "2024-08",
    "closed_tickets": 150
  }
]
```

---

## 💡 Quick Reference for Frontend

| Pattern | When to Use | Example |
| :--- | :--- | :--- |
| `/endpoint` (detail) | Paginated tables, drill-down views | `/api/mi/progress?project=AGRA&limit=50` |
| `/endpoint/summary` | Dashboard cards, charts, KPI tiles | `/api/mi/progress/summary?project=AGRA` |
| `category_breakdown` | Pie charts, grouped bar charts | Keys: `meter_category` → `new_meter_type` → values |
| `period_breakdown` | Time-series line/area charts | Keys: `period_value` → `meter_category` → `new_meter_type` → values |

### Common Nesting Pattern (Summary Endpoints)

Most `/summary` endpoints follow a two-level nesting pattern inside `category_breakdown` and `period_breakdown`:

```
category_breakdown
  └── <meter_category> (e.g. "CONSUMER")
        └── <new_meter_type> (e.g. "1PH-STSM")
              └── { metric values }

period_breakdown
  └── <period_value> (e.g. "2024-08" or "01-09-24")
        └── <meter_category>
              └── <new_meter_type>
                    └── { metric values }
```

### Date Format Notes

| Context | Format | Example |
| :--- | :--- | :--- |
| Query param `start_date` / `end_date` | `YYYY-MM-DD` | `2024-08-01` |
| Monthly `period_value` | `YYYY-MM` | `2024-08` |
| Daily `period_value` | `DD-MM-YY` | `01-08-24` |
| Aging `period_value` | `DD-MM-YY` | `01-09-24` |
