# Smart Meter KPI API Contract

> **Version**: 2.1 &nbsp;|&nbsp; **Last Updated**: 2026-04-19  
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
| `duration` | `string` | `daily` / `weekly` / `monthly` | Alias for `period` used by dashboard-style endpoints (`/progress/dashboard`, `/inventory-utilization/summary`, `/pace-vs-stock/summary`, `/non-sat-ageing/dashboard`, etc.) |
| `start_date` | `string` | `YYYY-MM-DD` | Filter records on or after this date |
| `end_date` | `string` | `YYYY-MM-DD` | Filter records on or before this date |

### Pagination

| Parameter | Type | Default | Max | Description |
| :--- | :--- | :--- | :--- | :--- |
| `limit` | `int` | `1000` | `50000` | Maximum rows to return |
| `offset` | `int` | `0` | — | Number of rows to skip |

---


---

## 📏 Meter Installation (MI) KPIs

All MI endpoints are under the prefix `/api/mi`.

---

### KPI 1 — MI Progress

Tracks the total number of meter installations over time.


#### `GET /api/mi/progress/dashboard` ⭐ _New Endpoint_

Single endpoint for the MI Progress dashboard (Trend + Comparison by Cluster) with strict date-range filtering.

**Parameters**

- `duration`: `daily` / `weekly` / `monthly`
- `category`: `total` / `consumer` / `feeder` / `dt`
- `level`: `discom` / `zone` / `circle` / `division` / `subdivision`
- `project`: `all` / `kashi` / `agra` / `triveni`
- `start_date` / `end_date`: `YYYY-MM-DD`
- Plus the usual geo filters: `discom`, `zone`, `circle`, `division`, `subdivision`, `substation`, `feeder`, `dtr`
- Plus category filter: `new_meter_type`

**Behavior Notes**

- If `project=all` and `level=discom`, the comparison chart returns **3 bars** for `KASHI`, `AGRA`, `TRIVENI`.
- If `project=all` and `level` is `zone/circle/division/subdivision`, comparison labels are **prefixed** as `AGRA | <zone>` to avoid collisions across projects.
- If `category=total`, the trend chart returns separate series for `CONSUMER`, `FEEDER`, and `DT`. Otherwise it returns the selected category series (others will be 0).
- `start_date/end_date` are applied by converting the stored `period_value` into a real date (no string-based comparisons).

**Response** — `MIProgressDashboardOut`

```json
{
  "total_progress": 154200,
  "category_breakdown": {
    "CONSUMER": {
      "total": { "count": 120000 },
      "1PH-STSM": { "count": 115000 },
      "3PLTCTSM": { "count": 5000 }
    },
    "FEEDER": {
      "total": { "count": 3420 },
      "HTCTPTSM": { "count": 3420 }
    }
  },
  "trend": [
    { "period_value": "16-03-26", "CONSUMER": 120, "FEEDER": 3, "DT": 7 },
    { "period_value": "17-03-26", "CONSUMER": 98, "FEEDER": 4, "DT": 6 }
  ],
   "comparison": [
    { "label": "KASHI", "CONSUMER": 30000, "FEEDER": 15000, "DT": 5000, "count": 50000 },
    { "label": "AGRA", "CONSUMER": 40000, "FEEDER": 15000, "DT": 5000, "count": 60000 },
    { "label": "TRIVENI", "CONSUMER": 25000, "FEEDER": 12000, "DT": 7200, "count": 44200 }
  ]
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

### KPI 2.5 — MI Productivity per Team (Agency) Dashboard ⭐ _New Endpoint_

Provides aggregated productivity metrics grouped by agency (team), with trend and comparison visualizations.

**Formula**:  
`MI Productivity per Team = Total verified installations / Number of active agencies`

#### `GET /api/mi/productivity/team/dashboard`

**Parameters**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `duration` | `string` | Aggregation granularity: `daily` / `weekly` / `monthly` |
| `level` | `string` | Cluster level for comparison: `project`, `discom`, `zone`, `circle`, `division`, `subdivision` |
| `project` | `string` | Project filter: `all` (shows all 3 projects) or specific project name (`AGRA`, `KASHI`, `TRIVENI`) |
| `start_date` / `end_date` | `string` | Date range filter (`YYYY-MM-DD`) |
| Plus all standard geographical & category filters |

**Behavior Notes**

- **Trend chart**: Returns time-series data at the selected `duration` granularity. Each point includes total installations, active agencies count, and productivity per agency per day.
- **Comparison chart**:
  - If `project=all` + `level=project` or `level=discom` → 3 bars: `AGRA`, `KASHI`, `TRIVENI`
  - If `project=all` + `level=zone/circle/division/subdivision` → composite labels like `AGRA | AGRA I`, `KASHI | ZONE-A`
  - If `project=AGRA` + `level=zone` → bars: `AGRA I`, `AGRA II` (raw zone names, no project prefix)
- **Category breakdown**: Breaks down total installations and productivity per day by `meter_category` (`CONSUMER`, `FEEDER`, `DT`).
- **Insights**: Shows top and lowest performing agencies based on overall productivity.
- All installations are **verified only** (`sat_no IS NOT NULL`).
- `productivity_per_agency_per_day` = `total_installations / (active_agencies × active_days)`

**Response** — `MIPerTeamDashboardOut`:

```json
{
  "summary": {
    "total_installations": 15000,
    "total_agencies": 25,
    "total_active_days": 30,
    "productivity_per_day": 500.0,
    "productivity_per_agency_per_day": 20.0
  },
  "insights": {
    "top_performing_agency": {
      "name": "ABC Agency",
      "productivity_per_agency_per_day": 35.2
    },
    "lowest_performing_agency": {
      "name": "XYZ Agency",
      "productivity_per_agency_per_day": 12.8
    }
  },
  "trend": [
    {
      "date": "2026-03-01",
      "total_installations": 500,
      "active_agencies": 5,
      "productivity_per_agency_per_day": 100.0
    },
    {
      "date": "2026-03-02",
      "total_installations": 550,
      "active_agencies": 5,
      "productivity_per_agency_per_day": 110.0
    }
  ],
  "comparison": [
    {
      "label": "AGRA",
      "total_installations": 5000,
      "active_agencies": 8,
      "active_days": 30,
      "productivity_per_agency_per_day": 20.83
    },
    {
      "label": "KASHI",
      "total_installations": 4500,
      "active_agencies": 7,
      "active_days": 30,
      "productivity_per_agency_per_day": 21.43
    },
    {
      "label": "TRIVENI",
      "total_installations": 5500,
      "active_agencies": 10,
      "active_days": 30,
      "productivity_per_agency_per_day": 18.33
    }
  ],
  "category_breakdown": {
    "CONSUMER": {
      "total_installations": 12000,
      "productivity_per_day": 400.0
    },
    "FEEDER": {
      "total_installations": 2000,
      "productivity_per_day": 66.6
    },
    "DT": {
      "total_installations": 1000,
      "productivity_per_day": 33.3
    }
  }
}
```

**Frontend Usage**

- **Daily Performance Graph**: Use the `trend` array. X-axis = `date`, Y-axis = `productivity_per_agency_per_day` (or `total_installations`).
- **Comparison by Cluster**: Use the `comparison` array. Each bar's height = `productivity_per_agency_per_day`. Tooltip can show `total_installations` and `active_agencies`.
- **Summary Cards**: Use `summary` for overall KPIs (total installations, total agencies, overall productivity).
- **Category Distribution**: Use `category_breakdown` for pie/bar charts by meter type.

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

### KPI 3.5 — Monthly Productivity Trend Dashboard ⭐ _New Endpoint_

Provides a monthly view of installation productivity (installations per calendar day) with trend and comparison charts. Uses pre-aggregated data for fast performance.

**Formula**:  
`Monthly Productivity = Total Installations / Active Days`  
where `Active Days = Calendar days in that month` (e.g., January = 31, February = 28/29).

#### `GET /api/mi/productivity/trend/dashboard`

**Parameters**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `duration` | `string` | Aggregation granularity: `daily` / `weekly` / `monthly` (used by trend; comparison always monthly) |
| `project` | `string` | Project filter: `all` (shows all 3 projects) or specific project name (`AGRA`, `KASHI`, `TRIVENI`) |
| `level` | `string` | Level for comparison grouping: `discom` / `zone` / `circle` / `division` / `subdivision` (default: `zone`) |
| `start_date` / `end_date` | `string` | Date range filter (`YYYY-MM-DD`) |
| Plus all standard geographical & category filters |

**Behavior Notes**

- **Trend chart**: Returns monthly time-series. Each month shows:
  - `total_installations` — sum of all verified installations that month
  - `active_days` — calendar days in that month (31 for Jan, 30 for Apr, etc.)
  - `productivity_per_day` = `total_installations / active_days`
- **Comparison chart** — grouping mirrors `/api/mi/progress/dashboard` (KPI 1):
  - `project=all` & `level=discom` → 3 bars: `AGRA`, `KASHI`, `TRIVENI`
  - `project=all` & `level=zone/circle/division/subdivision` → **composite labels** like `AGRA | AGRA I`, `KASHI | ZONE-A` (PROJECT | LEVEL)
  - `project=AGRA` & `level=zone` → bars show zones within AGRA only (e.g., `AGRA I`, `AGRA II`) — raw level values, no project prefix
- All installations are **verified only** (`sat_no IS NOT NULL`).
- The `active_days` in comparison sums calendar days across all months included in the filtered date range.
- Data comes from a pre-aggregated summary table (`sql_monthly_productivity_trend_summary`) — no on-the-fly aggregation.

**Response** — `MonthlyProductivityTrendOut`

```json
{
  "monthly_productivity_trend": [
    {
      "month": "2025-01",
      "total_installations": 129038,
      "active_days": 31,
      "productivity_per_day": 4162.52
    },
    {
      "month": "2025-02",
      "total_installations": 121412,
      "active_days": 28,
      "productivity_per_day": 4336.14
    },
    {
      "month": "2025-03",
      "total_installations": 118852,
      "active_days": 31,
      "productivity_per_day": 3833.94
    },
    {
      "month": "2025-04",
      "total_installations": 130066,
      "active_days": 30,
      "productivity_per_day": 4335.53
    },
    {
      "month": "2025-05",
      "total_installations": 137478,
      "active_days": 31,
      "productivity_per_day": 4434.77
    },
    {
      "month": "2025-06",
      "total_installations": 161450,
      "active_days": 30,
      "productivity_per_day": 5381.67
    }
  ],
  "comparison": [
    {
      "label": "AGRA",
      "total_installations": 305477,
      "active_days": 181,
      "productivity_per_day": 1687.72
    },
    {
      "label": "KASHI",
      "total_installations": 257417,
      "active_days": 181,
      "productivity_per_day": 1422.19
    },
    {
      "label": "TRIVENI",
      "total_installations": 235402,
      "active_days": 181,
      "productivity_per_day": 1300.56
    }
  ]
}
```

**Frontend Usage**

- **Trend chart**: Line chart with `month` on X-axis, `productivity_per_day` on Y-axis. Tooltip can show `total_installations` and `active_days`.
- **Comparison chart**: Bar chart with `label` (project/zone/circle) on X-axis, `productivity_per_day` as bar height. Tooltip shows `total_installations` and `active_days` to explain the calculation.
- **Summary cards**: Use trend data to compute overall totals across all months.

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

#### `GET /api/mi/inventory-utilization/summary` ⭐ _Updated_

Aggregated inventory utilization with nested category/period breakdowns and comparison chart grouped by hierarchy level.

**Parameters**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `duration` | `string` | Aggregation granularity: `daily` / `weekly` / `monthly` (default: `daily`) |
| `level` | `string` | Hierarchy level for comparison grouping: `discom` / `zone` / `circle` / `division` / `subdivision` (default: `discom`) |
| `project` | `string` | Project filter: `all` (shows all 3 projects) or specific project (`AGRA`, `KASHI`, `TRIVENI`) |
| `category` | `string` | Optional meter category filter: `total` (all categories), `consumer`, `feeder`, or `dt` (case-insensitive). Default: `total` |
| `start_date` / `end_date` | `string` | Date range filter (`YYYY-MM-DD`) — records are converted from stored `period_value` format to DATE for accurate comparison |
| Plus all standard geographical filters: `discom`, `zone`, `circle`, `division`, `subdivision`, `substation`, `feeder`, `dtr`, `new_meter_type` |

**Behavior Notes**

- **Category breakdown**: Nested by `meter_category` → `new_meter_type`. Each leaf includes `total_inventory`, `total_installed`, and computed `utilization_rate_pct`. Parent nodes aggregate these metrics as well.
- **Period breakdown**: Nested by `period_value` → `meter_category` → `new_meter_type`. Each node includes `total_inventory`, `total_installed`, and `utilization_rate_pct`. Periods are ordered chronologically (converting stored `DD-MM-YY` strings into dates).
- **Comparison chart** (`comparison` array) — grouping mirrors `/api/mi/progress/dashboard` (KPI 1):
  - `project=all` & `level=discom` → 3 bars: `AGRA`, `KASHI`, `TRIVENI`
  - `project=all` & `level=zone/circle/division/subdivision` → **composite labels** like `AGRA | AGRA I`, `KASHI | ZONE-A` (PROJECT | LEVEL)
  - `project=AGRA` & `level=zone` → bars show zones within AGRA only (e.g., `AGRA I`, `AGRA II`) — raw level values, no project prefix
  - Each bar includes: `label`, `total_inventory`, `total_installed`, `utilization_rate_pct`, and category splits `CONSUMER`/`FEEDER`/`DT`
- `category=dt` filters all breakdowns and the comparison array to the DT category only (CONSUMER/FEEDER will be 0 or absent).
- Date filtering uses `_period_value_as_date()` to convert stored `period_value` strings (`DD-MM-YY`) to real dates, ensuring correct range filtering regardless of string ordering.
- If no data matches the filters, all numeric fields return `0` and breakdown objects are empty (`{}`).

**Response** — `InventoryUtilizationSummaryOut`:

```json
{
  "total_inventory": 50000,
  "total_installed": 15000,
  "utilization_rate_pct": 30.0,
  "remaining_stock": 35000,
  "category_breakdown": {
    "CONSUMER": {
      "1PH-STSM": {
        "total_inventory": 40000,
        "total_installed": 12000,
        "utilization_rate_pct": 30.0
      }
    },
    "FEEDER": {
      "HTCTPTSM": {
        "total_inventory": 8000,
        "total_installed": 2400,
        "utilization_rate_pct": 30.0
      }
    },
    "DT": {
      "3PLTCTSM": {
        "total_inventory": 2000,
        "total_installed": 600,
        "utilization_rate_pct": 30.0
      }
    }
  },
  "period_breakdown": {
    "01-01-25": {
      "CONSUMER": {
        "1PH-STSM": {
          "total_inventory": 5000,
          "total_installed": 1500,
          "utilization_rate_pct": 30.0
        }
      }
    },
    "02-01-25": {
      "CONSUMER": {
        "1PH-STSM": {
          "total_inventory": 5500,
          "total_installed": 1650,
          "utilization_rate_pct": 30.0
        }
      }
    }
  },
  "comparison": [
    {
      "label": "AGRA I",
      "total_inventory": 18000,
      "total_installed": 5400,
      "utilization_rate_pct": 30.0,
      "CONSUMER": 3200,
      "FEEDER": 1400,
      "DT": 800
    },
    {
      "label": "AGRA II",
      "total_inventory": 15000,
      "total_installed": 4500,
      "utilization_rate_pct": 30.0,
      "CONSUMER": 2500,
      "FEEDER": 1200,
      "DT": 800
    }
  ]
}
```

---

### KPI 5 — MI Pace vs Stock Availability

Focused view of installation pace against stock. Defaults to **daily** granularity.

#### `GET /api/mi/pace-vs-stock`

**Parameters**: `period`, `project`, `discom`, `zone`, pagination.

**Response** — `List[InventoryUtilizationOut]` (same shape as KPI 4).

#### `GET /api/mi/pace-vs-stock/summary` ⭐ _Updated_

Aggregated inventory utilization summary focused on stock availability vs installations. Differs from KPI 4 in the `comparison` array: each item shows `remaining_stock` instead of `utilization_rate_pct`.

**Parameters**

Identical to `GET /api/mi/inventory-utilization/summary`:  
`duration`, `category`, `level`, `project`, `start_date`, `end_date`, plus all standard geographical filters.

**Response** — `PaceVsStockSummaryOut`

```json
{
  "total_inventory": 50000,
  "total_installed": 15000,
  "utilization_rate_pct": 30.0,
  "remaining_stock": 35000,
  "category_breakdown": {
    "CONSUMER": {
      "1PH-STSM": {
        "total_inventory": 40000,
        "total_installed": 12000,
        "remaining_stock": 28000
      }
    },
    "FEEDER": {
      "HTCTPTSM": {
        "total_inventory": 8000,
        "total_installed": 2400,
        "remaining_stock": 5600
      }
    }
  },
  "period_breakdown": {
    "01-01-25": {
      "CONSUMER": {
        "1PH-STSM": {
          "total_inventory": 5000,
          "total_installed": 1500,
          "remaining_stock": 3500
        }
      }
    }
  },
  "comparison": [
    {
      "label": "AGRA I",
      "total_inventory": 18000,
      "total_installed": 5400,
      "remaining_stock": 12600,
      "CONSUMER": 3200,
      "FEEDER": 1400,
      "DT": 800
    }
  ]
}
```

**Key points**:
- `category_breakdown` and `period_breakdown` leaf nodes use `total_inventory`, `total_installed`, `remaining_stock` — **no** `utilization_rate_pct`
- `comparison` uses `PaceVsStockComparisonItem` (has `remaining_stock`, no `utilization_rate_pct`)
- Top-level retains `utilization_rate_pct` for overall utilization percentage

---

### KPI 6 — Stock Ageing ⭐ _Updated_

Tracks how long dispatched meters remain uninstalled, categorized into aging buckets (0-30, 31-60, 61-90, 90+ days). Provides multiple views for dashboard and drill-down.

---

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

---

#### `GET /api/mi/stock-ageing/summary`

Returns aggregated aging bucket totals with nested breakdowns by category and by time period. Suitable for summary cards and drill-down charts.

**Parameters**: All geographical + category filters, `start_date`, `end_date`.

**Response** — `StockAgeingSummaryOut`:
```json
{
  "category_breakdown": {
    "CONSUMER": {
      "total": 1500,
      "1PH-STSM": {
        "age_0_30": 120,
        "age_31_60": 85,
        "age_61_90": 40,
        "age_90_plus": 1250,
        "total": 1495
      },
      "3PLTCTSM": {
        "age_0_30": 10,
        "age_31_60": 5,
        "age_61_90": 2,
        "age_90_plus": 30,
        "total": 47
      }
    },
    "FEEDER": {
      "total": 16,
      "HTCTPTSM": {
        "age_0_30": 0,
        "age_31_60": 0,
        "age_61_90": 1,
        "age_90_plus": 15,
        "total": 16
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
          "age_90_plus": 450,
          "total": 450
        }
      }
    },
    "01-11-24": {
      "CONSUMER": {
        "1PH-STSM": {
          "age_0_30": 0,
          "age_31_60": 0,
          "age_61_90": 0,
          "age_90_plus": 180,
          "total": 180
        }
      }
    }
  }
}
```

> **Note**: The `category_breakdown` and `period_breakdown` structures include a `total` field at each category and meter_type level, representing the sum of all four aging buckets.

---

#### `GET /api/mi/stock-ageing/dashboard` ⭐ _New Endpoint_

Dashboard-optimized endpoint combining summary totals, time-series trend, comparison by hierarchical level, and category breakdown. Supports multiple duration granularities (daily/weekly/monthly) using pre-aggregated data.

**Parameters**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `duration` | `string` | Aggregation granularity: `daily` / `weekly` / `monthly` (default: `monthly`) |
| `level` | `string` | Hierarchy level for comparison grouping: `discom` / `zone` / `circle` / `division` / `subdivision` (default: `discom`) |
| `project` | `string` | Project filter: `all` (shows all 3 projects) or specific project (`AGRA`, `KASHI`, `TRIVENI`) (default: `all`) |
| `start_date` / `end_date` | `string` | Date range filter (`YYYY-MM-DD`) |
| Plus all standard geographical & category filters: `discom`, `zone`, `circle`, `division`, `subdivision`, `substation`, `feeder`, `dtr`, `new_meter_type`, `meter_category` |

**Behavior Notes**

- **Data source**: Uses pre-aggregated `sql_stock_ageing` table with separate `period_type` entries for daily, weekly, and monthly granularities.
- **Period format**:
  - `monthly`: `period_value` is `DD-MM-YY` (e.g., `01-01-24`)
  - `weekly`: `period_value` is `YYYY-MM-DD` (Monday of the week)
  - `daily`: `period_value` is `YYYY-MM-DD`
- **Comparison chart** (`comparison` array) — grouping mirrors `/api/mi/progress/dashboard`:
  - `project=all` & `level=discom` → 3 bars: `AGRA`, `KASHI`, `TRIVENI`
  - `project=all` & `level=zone/circle/division/subdivision` → composite labels like `AGRA | AGRA I`
  - `project=AGRA` & `level=zone` → zones within AGRA only (e.g., `AGRA I`, `AGRA II`)
- **Trend chart** (`period_breakdown`): Chronologically ordered array of period aggregates, each containing totals across all categories.
- **Category breakdown** (`category_breakdown`): Nested by `meter_category` → `new_meter_type`. Category-level nodes contain aggregated age bucket sums (`age_0_30`, `age_31_60`, `age_61_90`, `age_90_plus`, `total`).
- If no data matches filters, all numeric fields return `0` and breakdown objects are empty (`{}`).

**Response** — `StockAgeingDashboardOut`

```json
{
  "total_stock": 837156,
  "category_breakdown": {
    "CONSUMER": {
      "age_0_30": 0,
      "age_31_60": 0,
      "age_61_90": 61705,
      "age_90_plus": 336882,
      "total": 398587,
      "1PH-STSM": {
        "age_0_30": 0,
        "age_31_60": 0,
        "age_61_90": 61705,
        "age_90_plus": 336882,
        "total": 398587
      },
      "NSM1-PH": {
        "age_0_30": 0,
        "age_31_60": 0,
        "age_61_90": 225,
        "age_90_plus": 5639,
        "total": 5864
      }
    },
    "FEEDER": {
      "age_0_30": 0,
      "age_31_60": 0,
      "age_61_90": 0,
      "age_90_plus": 8885,
      "total": 8885,
      "HTCTPTSM": {
        "age_0_30": 0,
        "age_31_60": 0,
        "age_61_90": 0,
        "age_90_plus": 8885,
        "total": 8885
      }
    },
    "DT": {
      "age_0_30": 0,
      "age_31_60": 0,
      "age_61_90": 234,
      "age_90_plus": 670,
      "total": 904,
      "3PLTCTSM": {
        "age_0_30": 0,
        "age_31_60": 0,
        "age_61_90": 234,
        "age_90_plus": 670,
        "total": 904
      }
    }
  },
  "period_breakdown": [
    {
      "period_value": "01-05-24",
      "age_0_30": 0,
      "age_31_60": 0,
      "age_61_90": 0,
      "age_90_plus": 184,
      "total_stock": 184
    },
    {
      "period_value": "01-06-24",
      "age_0_30": 0,
      "age_31_60": 0,
      "age_61_90": 0,
      "age_90_plus": 4428,
      "total_stock": 4428
    }
  ],
  "comparison": [
    {
      "label": "AGRA",
      "age_0_30": 0,
      "age_31_60": 0,
      "age_61_90": 12000,
      "age_90_plus": 50000,
      "total_stock": 62000
    },
    {
      "label": "KASHI",
      "age_0_30": 0,
      "age_31_60": 0,
      "age_61_90": 8000,
      "age_90_plus": 35000,
      "total_stock": 43000
    },
    {
      "label": "TRIVENI",
      "age_0_30": 0,
      "age_31_60": 0,
      "age_61_90": 5000,
      "age_90_plus": 25000,
      "total_stock": 30000
    }
  ]
}
```

**Frontend Usage**

- **Summary card**: Use `total_stock` (top-level) for the big number.
- **Category breakdown**: Use for pie/bar charts showing aging distribution across meter categories and types. The category-level fields (`age_0_30`, `age_31_60`, `age_61_90`, `age_90_plus`, `total`) provide high-level views; drill-down into meter types for detailed breakdowns.
- **Period breakdown** (`period_breakdown`): Time-series trend chart. X-axis = `period_value`, Y-axis = counts. You can plot each aging bucket as a stacked area or separate lines. `total_stock` gives the overall trend.
- **Comparison** (`comparison`): Bar chart comparing total stock (or individual aging buckets) across hierarchical groups (projects/zones/etc.). Use `label` for X-axis categories.

---

> **Note**: This endpoint replaced the older `GET /api/mi/stock-ageing/summary` which only provided category and period breakdowns without comparison data. The dashboard endpoint is recommended for new UI implementations.

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

#### `GET /api/mi/mi-vs-sat/summary` ⭐ _Updated_

Aggregated MI vs SAT comparison with nested category/period breakdowns and comparison chart grouped by hierarchy level.

**Parameters**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `duration` | `string` | Aggregation granularity: `daily` / `weekly` / `monthly` (default: `daily`) |
| `level` | `string` | Hierarchy level for comparison grouping: `discom` / `zone` / `circle` / `division` / `subdivision` (default: `discom`) |
| `project` | `string` | Project filter: `all` (shows all 3 projects) or specific project (`AGRA`, `KASHI`, `TRIVENI`) |
| `category` | `string` | Optional meter category filter: `consumer`, `feeder`, or `dt` (case-insensitive) |
| `new_meter_type` | `string` | Optional meter hardware type filter |
| `start_date` / `end_date` | `string` | Date range filter (`YYYY-MM-DD`) |
| Plus all standard geographical filters: `discom`, `zone`, `circle`, `division`, `subdivision`, `substation`, `feeder`, `dtr` |

**Behavior Notes**

- **Category breakdown**: Nested by `meter_category` → `new_meter_type`. Each leaf includes `total_mi`, `total_sat`, and all nine SAT stage counts (`sat_1` through `sat_9`). Parent `total` nodes aggregate these metrics as well.
- **Period breakdown**: Nested by `period_value` → `meter_category` → `new_meter_type`. Each leaf includes `total_sat` and all nine SAT stage counts (`sat_1` through `sat_9`). The `period_value` format depends on `duration` (all use `DD-MM-YY` format representing the start of the period):
  - `duration=daily`: `DD-MM-YY` (e.g., `17-04-25`) — each day separate
  - `duration=weekly`: `DD-MM-YY` (e.g., `14-06-24`) — Monday (start) of each ISO week
  - `duration=monthly`: `DD-MM-YY` (e.g., `01-04-25`) — first day of month
  Periods are ordered chronologically within each duration grain.
- The underlying MIvsSAT table stores only daily records; aggregation to weekly/monthly is performed on-the-fly.
- **Comparison chart** (`comparison` array) — grouping mirrors `/api/mi/progress/dashboard` (KPI 1):
  - `project=all` & `level=discom` → 3 bars: `AGRA`, `KASHI`, `TRIVENI`
  - `project=all` & `level=zone/circle/division/subdivision` → **composite labels** like `AGRA | AGRA I`, `KASHI | ZONE-A` (PROJECT | LEVEL)
  - `project=AGRA` & `level=zone` → bars show zones within AGRA only (e.g., `AGRA I`, `AGRA II`) — raw level values, no project prefix
  - Each bar includes: `label`, `total_mi`, `total_sat`, `sat_progress_pct`, and category totals for `CONSUMER`, `FEEDER`, `DT` (these category values represent MI counts per category).
- The `category` filter (`meter_category`) narrows all breakdowns to that category only; the comparison array still returns category totals (with other categories zeroed).
- If no data matches the filters, all numeric fields return `0` and breakdown objects are empty (`{}`).

**Response** — `MIvsSATSummaryOut`

```json
{
  "total_mi": 1086387,
  "total_sat": 696186,
  "sat_1": 228242, "sat_2": 171406, "sat_3": 169023,
  "sat_4": 57999, "sat_5": 28179, "sat_6": 20990,
  "sat_7": 20347, "sat_8": 0, "sat_9": 0,
  "sat_progress_pct": 64.08,
  "category_breakdown": {
    "CONSUMER": {
      "total": {
        "total_mi": 800000,
        "total_sat": 512000,
        "sat_1": 167000, "sat_2": 125000, "sat_3": 123000,
        "sat_4": 42000, "sat_5": 21000, "sat_6": 15000,
        "sat_7": 14500, "sat_8": 0, "sat_9": 0
      },
      "1PH-STSM": {
        "total_mi": 800000,
        "total_sat": 512000,
        "sat_1": 167000, "sat_2": 125000, "sat_3": 123000,
        "sat_4": 42000, "sat_5": 21000, "sat_6": 15000,
        "sat_7": 14500, "sat_8": 0, "sat_9": 0
      }
    },
    "FEEDER": {
      "total": {
        "total_mi": 200000,
        "total_sat": 128000,
        "sat_1": 42000, "sat_2": 32000, "sat_3": 31000,
        "sat_4": 12000, "sat_5": 5500, "sat_6": 4000,
        "sat_7": 4000, "sat_8": 0, "sat_9": 0
      },
      "HTCTPTSM": {
        "total_mi": 200000,
        "total_sat": 128000,
        "sat_1": 42000, "sat_2": 32000, "sat_3": 31000,
        "sat_4": 12000, "sat_5": 5500, "sat_6": 4000,
        "sat_7": 4000, "sat_8": 0, "sat_9": 0
      }
    },
    "DT": {
      "total": {
        "total_mi": 86387,
        "total_sat": 56186,
        "sat_1": 19242, "sat_2": 14406, "sat_3": 15023,
        "sat_4": 3999, "sat_5": 1679, "sat_6": 1990,
        "sat_7": 1847, "sat_8": 0, "sat_9": 0
      },
      "3PLTCTSM": {
        "total_mi": 86387,
        "total_sat": 56186,
        "sat_1": 19242, "sat_2": 14406, "sat_3": 15023,
        "sat_4": 3999, "sat_5": 1679, "sat_6": 1990,
        "sat_7": 1847, "sat_8": 0, "sat_9": 0
      }
    }
  },
  "period_breakdown": {
    "01-01-24": {
      "CONSUMER": {
        "total": {
          "total_sat": 5000,
          "sat_1": 1500, "sat_2": 1200, "sat_3": 1000,
          "sat_4": 400, "sat_5": 200, "sat_6": 150,
          "sat_7": 100, "sat_8": 0, "sat_9": 0
        },
        "1PH-STSM": {
          "total_sat": 5000,
          "sat_1": 1500, "sat_2": 1200, "sat_3": 1000,
          "sat_4": 400, "sat_5": 200, "sat_6": 150,
          "sat_7": 100, "sat_8": 0, "sat_9": 0
        }
      }
    }
  },
  "comparison": [
    {
      "label": "AGRA",
      "CONSUMER": 400000,
      "FEEDER": 100000,
      "DT": 40000,
      "total_mi": 540000,
      "total_sat": 345600,
      "sat_progress_pct": 64.0
    },
    {
      "label": "KASHI",
      "CONSUMER": 300000,
      "FEEDER": 80000,
      "DT": 30000,
      "total_mi": 410000,
      "total_sat": 262400,
      "sat_progress_pct": 64.0
    },
    {
      "label": "TRIVENI",
      "CONSUMER": 200000,
      "FEEDER": 20000,
      "DT": 16387,
      "total_mi": 236387,
      "total_sat": 88186,
      "sat_progress_pct": 37.28
    }
  ]
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

#### `GET /api/mi/non-sat-ageing/dashboard` ⭐ _New Endpoint_

Dashboard for Non-SAT Ageing with ageing bucket distributions, category breakdown, trend over installation periods, and hierarchical comparison.

**Parameters**

- `duration`: `daily` / `weekly` / `monthly` (aggregation granularity)
- `category`: `total` / `consumer` / `feeder` / `dt` (meter category filter)
- `level`: `discom` / `zone` / `circle` / `division` / `subdivision` (hierarchy level for comparison grouping)
- `project`: `all` / `kashi` / `agra` / `triveni`
- `start_date` / `end_date`: `YYYY-MM-DD` (installation date range filter)
- Plus the usual geo filters: `discom`, `zone`, `circle`, `division`, `subdivision`, `substation`, `feeder`, `dtr`
- Plus: `new_meter_type`

**Behavior Notes**

- **Ageing buckets**: Discrete buckets (`age_0_30`, `age_31_60`, `age_61_90`, `age_91_120`, `age_120_plus`).
- **Nesting**: In `summary` and `comparison`, each ageing bucket is an object containing counts for `CONSUMER`, `FEEDER`, `DT`, and a `total`.
- If `project=all` and `level=discom`, the comparison chart returns **3 bars** for `KASHI`, `AGRA`, `TRIVENI`.
- If `project=all` and `level` is `zone/circle/division/subdivision`, comparison labels are **prefixed** as `AGRA | <zone>` to avoid collisions across projects.
- If `category=total`, the trend chart returns separate series for `CONSUMER`, `FEEDER`, and `DT`. Otherwise it returns the selected category series (others will be 0).
- `start_date/end_date` filter on the installation date (`date_value`).
- Trend period (`period_value`) is based on the installation date truncated to the selected `duration`.

**Response** — `NonSATAgeingDashboardOut`

```json
{
  "total_non_sat": 882002,
  "category_breakdown": {
    "CONSUMER": 819605,
    "FEEDER": 281,
    "DT": 62116
  },
  "summary": {
    "age_0_30": { "CONSUMER": 0, "FEEDER": 0, "DT": 0, "total": 0 },
    "age_31_60": { "CONSUMER": 0, "FEEDER": 0, "DT": 0, "total": 0 },
    "age_61_90": { "CONSUMER": 265000, "FEEDER": 100, "DT": 21344, "total": 286444 },
    "age_91_120": { "CONSUMER": 275000, "FEEDER": 150, "DT": 23804, "total": 298954 },
    "age_120_plus": { "CONSUMER": 279605, "FEEDER": 31, "DT": 16968, "total": 296604 },
    "total_non_sat": 882002
  },
  "period_breakdown": [
    {
      "period_value": "16-03-26",
      "age_0_30": 0,
      "age_31_60": 0,
      "age_61_90": 5000,
      "age_91_120": 3000,
      "age_120_plus": 1500,
      "total_non_sat": 9500
    }
  ],
  "comparison": [
    {
      "label": "KASHI",
      "CONSUMER": 40000,
      "FEEDER": 25000,
      "DT": 15000,
      "count": 80000,
      "age_0_30": { "CONSUMER": 0, "FEEDER": 0, "DT": 0, "total": 0 },
      "age_31_60": { "CONSUMER": 0, "FEEDER": 0, "DT": 0, "total": 0 },
      "age_61_90": { "CONSUMER": 12000, "FEEDER": 50, "DT": 3000, "total": 15050 },
      "age_91_120": { "CONSUMER": 13000, "FEEDER": 100, "DT": 5000, "total": 18100 },
      "age_120_plus": { "CONSUMER": 15000, "FEEDER": 20, "DT": 7000, "total": 22020 },
      "total_non_sat": 80000
    }
  ]
}
```

---

### KPI 9 — Meter Journey Average Time

Average **calendar days** per stage for meters that have **completed PMPM revenue** (`pmpm_collection_date` is not null). Each value is `AVG` over that cohort (PostgreSQL skips null date differences for a given stage). **PMPM-only** invoice/revenue legs use `pmpm_invoice_date` and `pmpm_collection_date`.

**Stage definitions (materialized list + dashboard)**

| Field | Span |
| :--- | :--- |
| `inventory_to_store` | `gmrtoagencyts::date − didate::date` (same boundary as legacy “pre-agency pipeline”; no separate store-receipt column in source) |
| `store_to_agency` | `agencytosupts::date − gmrtoagencyts::date` |
| `agency_to_meter_installation` | `installedts::date − agencytosupts::date` |
| `meter_installation_to_sat` | `sat_date::date − installedts::date` |
| `sat_to_invoice` | `pmpm_invoice_date::date − sat_date::date` |
| `invoice_to_revenue` | `pmpm_collection_date::date − pmpm_invoice_date::date` |
| `total_journey` | `pmpm_collection_date::date − didate::date` |

Lumpsum invoice/collection dates are **not** blended into these PMPM stage averages.

**Time buckets (ETL)**  
Each row includes **`period_type`** (`daily` / `weekly` / `monthly`) and **`period_value`** (bucket label, `DD-MM-YY`), based on **`pmpm_collection_date`** (same cohort filter as before). The ETL writes three sets of rows (one per granularity).

**API presentation (whole days)**  
Stage averages are still computed in SQL as floating-point means over the cohort. In JSON, each stage field is **always rounded up** to a whole number of days: `int(math.ceil(x))` in Python, where `x` is that mean. Examples: `23.01` → `24`, `23.99` → `24`, `23.0` → `23`. This applies to **`GET /api/mi/meter-journey`** and **`GET /api/mi/meter-journey/dashboard`**.

#### `GET /api/mi/meter-journey`

Pre-aggregated rows from `sql_meter_journey_avg_time` (run MI ETL). Fine grain by geography + `new_meter_type` + resolved `meter_category` + **`period_type` / `period_value`**.

**Parameters**: `project`, **`period_type`** (`daily` / `weekly` / `monthly`, default **`daily`**), optional dimension filters (`discom`, `zone`, …), pagination (`limit` default 100, `offset`).

**Response** — `List[MeterJourneyOut]` (dimension fields plus):

```json
[
  {
    "project": "AGRA",
    "discom": "DVVNL",
    "zone": null,
    "circle": null,
    "division": null,
    "subdivision": null,
    "substation": null,
    "feeder": null,
    "dtr": null,
    "new_meter_type": "1PHSM",
    "meter_category": "CONSUMER",
    "period_type": "daily",
    "period_value": "19-04-26",
    "inventory_to_store": 5,
    "store_to_agency": 3,
    "agency_to_meter_installation": 7,
    "meter_installation_to_sat": 12,
    "sat_to_invoice": 4,
    "invoice_to_revenue": 5,
    "total_journey": 36,
    "meter_count": 128
  }
]
```

#### `GET /api/mi/meter-journey/dashboard`

Reads **`sql_meter_journey_avg_time`** with **`period_type`** / **`period_value`** populated by ETL (bucket = **`pmpm_collection_date`**).

- **Summary** and **comparison**: weighted mean per stage over all matching fine-grained rows for the selected **`duration`** (`daily` / `weekly` / `monthly`, default **`daily`**) and optional **`start_date`** / **`end_date`** (parsed as dates on `period_value`, same rules as MI progress).
- **Trend**: one row per **`period_value`** in that filter, each row a weighted roll-up across geography for that bucket (ordered by date).

**Parameters**

| Parameter | Description |
| :--- | :--- |
| `duration` | `daily` / `weekly` / `monthly` (selects which ETL bucket set to read; default `daily`). |
| `category` | `total` (default) or `consumer` / `feeder` / `dt` |
| `level` | `discom` (default), `zone`, `circle`, `division`, `subdivision`, `substation`, `feeder`, `dtr` — comparison grouping (same rules as `/api/mi/progress/dashboard`: when `level=discom` and `project=all`, clusters are **projects** AGRA/KASHI/TRIVENI; when `project=all` and level is below discom, label is `PROJECT \| levelValue`; else label is the level column.) |
| `project` | `all` (default, restricts to AGRA/KASHI/TRIVENI) or a single project code |
| `start_date` / `end_date` | Optional `YYYY-MM-DD` — filter rows whose `period_value` falls in that inclusive range (after parsing `period_value` as a date). |
| Plus optional `discom`, `zone`, `circle`, `division`, `subdivision`, `substation`, `feeder`, `dtr`, `new_meter_type`, `meter_category` (ILIKE on stored `meter_category`) |

**Response** — `MeterJourneyDashboardOut`:

```json
{
  "summary": {
    "inventory_to_store": 5,
    "store_to_agency": 3,
    "agency_to_meter_installation": 6,
    "meter_installation_to_sat": 12,
    "sat_to_invoice": 4,
    "invoice_to_revenue": 5,
    "total_journey": 35,
    "meter_count": 5000
  },
  "trend": [
    {
      "period_value": "01-03-26",
      "inventory_to_store": 5,
      "store_to_agency": 3,
      "agency_to_meter_installation": 6,
      "meter_installation_to_sat": 12,
      "sat_to_invoice": 4,
      "invoice_to_revenue": 5,
      "total_journey": 34,
      "meter_count": 120
    },
    {
      "period_value": "01-04-26",
      "inventory_to_store": 5,
      "store_to_agency": 3,
      "agency_to_meter_installation": 6,
      "meter_installation_to_sat": 12,
      "sat_to_invoice": 4,
      "invoice_to_revenue": 5,
      "total_journey": 35,
      "meter_count": 210
    }
  ],
  "comparison": [
    {
      "label": "AGRA",
      "inventory_to_store": 5,
      "store_to_agency": 3,
      "agency_to_meter_installation": 6,
      "meter_installation_to_sat": 12,
      "sat_to_invoice": 4,
      "invoice_to_revenue": 4,
      "total_journey": 35,
      "meter_count": 1800
    }
  ]
}
```

---

### KPI 10 — Meter Funnel Summary (Inventory → Installed → SAT → Revenue)

Shows a four-stage funnel count of meters from inventory through to revenue collection. Data is pre‑aggregated in `sql_meter_current_stage` at the grain of geography × meter type × meter category — no on‑the‑fly source scans.

**Metric definitions**:

| Metric | Condition |
| :--- | :--- |
| `inventory` | Total meters (all rows) |
| `installed` | `mi_date IS NOT NULL` AND `sat_no` is not empty |
| `sat_done` | `sat_date IS NOT NULL` |
| `revenue_collected` | `pmpm_collection_date IS NOT NULL` |

#### `GET /api/mi/meter-stage`

Returns the funnel totals, a nested category breakdown, and a comparison array grouped by hierarchical level.

**Response model**: `MeterStageFunnelSummaryOut`

**Parameters**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `project` | `string` | `all` (default, includes AGRA/KASHI/TRIVENI) or single project code (`AGRA`, `KASHI`, `TRIVENI`) |
| `category` | `string` | `total` (default) or `consumer` / `feeder` / `dt` — filters `meter_category` |
| `level` | `string` | Comparison grouping: `discom` (default), `zone`, `circle`, `division`, `subdivision`, `substation`, `feeder`, `dtr` |
| `duration` | `string` | Not used — present for backward compatibility |
| `limit` / `offset` | `int` | Ignored — present for backward compatibility |
| Plus any standard geo/category filters | `discom`, `zone`, `circle`, `division`, `subdivision`, `substation`, `feeder`, `dtr`, `new_meter_type`, `meter_category` | ILIKE filtering on the respective dimension |

**Response** — `MeterStageFunnelSummaryOut`

```json
{
  "inventory": 3520662,
  "installed": 3206479,
  "sat_done": 2293081,
  "revenue_collected": 1536780,
  "category_breakdown": {
    "CONSUMER": {
      "total": { "inventory": 3301781, "installed": 3090455, "sat_done": 2239455, "revenue_collected": 1500788 },
      "1PH-STSM": { "inventory": 3205338, "installed": 3010165, "sat_done": 2179729, "revenue_collected": 1460873 },
      "3PH-STSM": { "inventory": 42324, "installed": 29380, "sat_done": 19725, "revenue_collected": 14323 }
    },
    "FEEDER": { "total": { ... }, "HTCTPTSM": { ... } },
    "DT": { "total": { ... }, "3PLTCTSM": { ... } }
  },
   "comparison": [
     {
       "label": "AGRA",
       "inventory": 1338949,
       "installed": 1242904,
       "sat_done": 942664,
       "revenue_collected": 621264
     },
     { "label": "KASHI", "inventory": 1101643, "installed": 998578, "sat_done": 681121, "revenue_collected": 464403 },
     { "label": "TRIVENI", "inventory": 1080070, "installed": 964997, "sat_done": 669296, "revenue_collected": 451113 }
   ]
}
```

**Behavior notes**

- **`category_breakdown`**: Nested by `meter_category` (CONSUMER / FEEDER / DT) → `new_meter_type`. Each leaf and the `total` node contain all four metrics.
- **`comparison`**: One entry per cluster label determined by `level`. Each entry contains the aggregated four metrics directly (not split by category):
  - `project=all` + `level=discom` → labels are the three project names (`AGRA`, `KASHI`, `TRIVENI`).
  - `project=all` + `level` below discom → composite labels `PROJECT | levelValue` (e.g., `AGRA | AGRA I`).
  - `project=AGRA` + `level=zone` → zone names only (no project prefix).
  - Each cluster object: `{ label, inventory, installed, sat_done, revenue_collected }`.
- **`limit` / `offset`**: Accepted but ignored — the table is at summary grain; all rows are returned in the comparison array.

---

### KPI 11 — MI vs SAT vs Invoice Funnel

Tracks the funnel from MI → SAT → Invoice, with invoice broken down by type (Lumpsum vs PMPM). Provides trend analysis and comparison across hierarchical clusters.

**Formulas**:
- `total_mi` = Count of meters with MI date
- `total_sat` = Count of meters with SAT date
- `total_lumpsum_invoice` = Count of meters with `lumpsum_invoice_date` set
- `total_pmpm_invoice` = Count of meters with `pmpm_invoice_date` set
- `total_invoice` = `total_lumpsum_invoice + total_pmpm_invoice` (arithmetic sum; may exceed distinct invoice count if a meter has both invoice types)

#### `GET /api/mi/mi-vs-sat-vs-invoice/summary`

Returns aggregated funnel metrics with breakdowns by category/period and comparison bars by hierarchical level.

**Parameters**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `duration` | `string` | Aggregation granularity: `daily` / `weekly` / `monthly` (default: `monthly`) |
| `level` | `string` | Hierarchy level for comparison grouping: `discom` / `zone` / `circle` / `division` / `subdivision` (default: `discom`) |
| `category` | `string` | Filter by meter category: `consumer` / `feeder` / `dt` (case-insensitive) |
| `project` | `string` | Project filter: `all` (shows all 3 projects) or specific project (`AGRA`, `KASHI`, `TRIVENI`) |
| `start_date` / `end_date` | `string` | Date range filter (`YYYY-MM-DD`) |
| Plus all standard geographical & category filters | | `discom`, `zone`, `circle`, `division`, `subdivision`, `substation`, `feeder`, `dtr`, `new_meter_type` |

**Behavior Notes**

- **Trend chart** (`period_breakdown`): Returns time-series data at selected `duration` granularity. Each period includes counts for MI, SAT, Lumpsum Invoice, and PMPM Invoice, broken down by meter category and meter type.
- **Comparison chart** (`comparison`): Returns grouped totals by the selected `level`:
  - `project=all` + `level=discom` → 3 bars: `AGRA`, `KASHI`, `TRIVENI`
  - `project=all` + `level=zone/circle/division/subdivision` → composite labels like `AGRA | AGRA I`, `KASHI | ZONE-A`
  - `project=AGRA` + `level=zone` → bars show zones within AGRA only (raw level values)
  - Each bar shows: `total_mi`, `total_sat`, `total_lumpsum_invoice`, `total_pmpm_invoice`
- **Category breakdown**: Nested structure grouped by `meter_category` → `new_meter_type`, with all four metrics at each level.
- **Data granularity**: Currently only monthly data is populated (period_type = 'monthly').

**Response** — `MIvsSATvsInvoiceSummaryOut`

```json
{
  "total_mi": 3381850,
  "total_sat": 2293081,
  "total_lumpsum_invoice": 1873388,
  "total_pmpm_invoice": 1873388,
  "total_invoice": 3746776,
  "category_breakdown": {
    "CONSUMER": {
      "1PH-STSM": {
        "total_mi": 2500000,
        "total_sat": 1700000,
        "total_lumpsum_invoice": 1200000,
        "total_pmpm_invoice": 1200000
      },
      "3PH-STSM": {
        "total_mi": 150000,
        "total_sat": 100000,
        "total_lumpsum_invoice": 80000,
        "total_pmpm_invoice": 80000
      }
    },
    "FEEDER": {
      "HTCTPTSM": {
        "total_mi": 500000,
        "total_sat": 350000,
        "total_lumpsum_invoice": 300000,
        "total_pmpm_invoice": 300000
      }
    },
    "DT": {
      "3PLTCTSM": {
        "total_mi": 200000,
        "total_sat": 140000,
        "total_lumpsum_invoice": 100000,
        "total_pmpm_invoice": 100000
      }
    }
  },
  "period_breakdown": {
    "01-01-25": {
      "CONSUMER": {
        "1PH-STSM": {
          "total_mi": 50000,
          "total_sat": 40000,
          "total_lumpsum_invoice": 30000,
          "total_pmpm_invoice": 30000
        }
      }
    }
  },
  "comparison": [
    {
      "label": "KASHI",
      "total_mi": 1000000,
      "total_sat": 680000,
      "total_lumpsum_invoice": 500000,
      "total_pmpm_invoice": 500000
    },
    {
      "label": "AGRA",
      "total_mi": 1200000,
      "total_sat": 820000,
      "total_lumpsum_invoice": 650000,
      "total_pmpm_invoice": 650000
    },
    {
      "label": "TRIVENI",
      "total_mi": 800000,
      "total_sat": 550000,
      "total_lumpsum_invoice": 400000,
      "total_pmpm_invoice": 400000
    }
  ]
}
```

**Frontend Usage**

- **Funnel metrics**: Top-level fields show cumulative totals across all filters.
- **Trend chart**: Use `period_breakdown` — X-axis = `period_value`, series = `total_mi` / `total_sat` / `total_lumpsum_invoice` / `total_pmpm_invoice` (stacked or grouped).
- **Comparison chart**: Use `comparison` array — bar chart with `label` on X-axis, stacked bars for each metric type, or separate bar series.
- **Category distribution**: Use `category_breakdown` for pie/treemap visualizations by meter type.

**Key Insights**

- Gap between `total_sat` and `total_invoice` represents meters with completed SAT but pending invoice generation.
- SAT stage analysis shows ~419K meters in SAT-8/9 stages awaiting invoice (data from KPI 7 integration).

---


### KPI 12 — Revenue Realized

Tracks total revenue collected from installed meters. Provides a single aggregated count (`total_realized`) representing meters with a collection date (`pmpm_collection_date`).

**Metric**:
- `total_realized` = Count of meters where `pmpm_collection_date IS NOT NULL`

#### `GET /api/mi/revenue-realized/summary`

Returns aggregated revenue realized count with breakdowns by category, time period, and hierarchical comparison clusters.

**Parameters**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `duration` | `string` | Aggregation granularity: `daily` / `weekly` / `monthly` (default: `monthly`) |
| `level` | `string` | Hierarchy level for comparison grouping: `discom` / `zone` / `circle` / `division` / `subdivision` / `substation` / `feeder` / `dtr` (default: `discom`) |
| `project` | `string` | Project filter: `all` (shows all 3 projects) or specific project (`AGRA`, `KASHI`, `TRIVENI`) |
| `meter_category` | `string` | Optional filter: `consumer` / `feeder` / `dt` (case-insensitive) |
| `start_date` / `end_date` | `string` | Date range filter (`YYYY-MM-DD`) — applied on the derived period date |
| Plus all standard geographical & category filters | | `discom`, `zone`, `circle`, `division`, `subdivision`, `substation`, `feeder`, `dtr`, `new_meter_type` |

**Behavior Notes**

- **Period breakdown**: Time-series trend grouped by `period_value` (derived from `pmpm_collection_date`) → `meter_category` → `new_meter_type`. Periods are ordered chronologically (converting stored `period_value` strings into dates based on `duration` grain).
- **Category breakdown**: Nested by `meter_category` → `new_meter_type`, each leaf containing `realized` count. Parent `total` node aggregates all types within that category.
- **Comparison chart**: Grouped by `level` and `project`. Labels follow the same convention as other dashboard endpoints:
  - `project=all` & `level=discom` → `AGRA`, `KASHI`, `TRIVENI`
  - `project=all` & `level` below discom → `PROJECT | levelValue` (e.g., `AGRA | AGRA I`)
  - `project=AGRA` & `level=zone` → zone names only (no project prefix)
  - Each cluster object contains `CONSUMER`, `FEEDER`, `DT` sub-objects with `realized` counts.
- **Date filtering**: Uses `_period_value_as_date()` to convert the stored `period_value` into a real DATE for accurate range filtering regardless of string format (`DD-MM-YY` vs `YYYY-MM-DD`).

**Response** — `RevenueRealizedSummaryOut`

```json
{
  "total_realized": 1536780,
  "category_breakdown": {
    "CONSUMER": {
      "total": { "realized": 1500788 },
      "1PH-STSM": { "realized": 1460873 },
      "3PH-STSM": { "realized": 14323 }
    },
    "FEEDER": {
      "HTCTPTSM": { "realized": 6352 }
    },
    "DT": {
      "3PLTCTSM": { "realized": 29640 }
    }
  },
  "period_breakdown": {
    "01-01-26": {
      "CONSUMER": {
        "1PH-STSM": { "realized": 110006 },
        "3PH-STSM": { "realized": 902 }
      }
    }
  },
  "comparison": [
    {
      "label": "AGRA",
      "CONSUMER": { "realized": 611344 },
      "FEEDER": { "realized": 2940 },
      "DT": { "realized": 6980 }
    },
    { "label": "KASHI", "CONSUMER": { "realized": 450652 }, "FEEDER": { "realized": 1757 }, "DT": { "realized": 11994 } },
    { "label": "TRIVENI", "CONSUMER": { "realized": 438792 }, "FEEDER": { "realized": 1655 }, "DT": { "realized": 10666 } }
  ]
}
```

---

### KPI 13 — Revenue Ageing (SAT to Collection)

Tracks aging of revenue collection after SAT, with bucket-based breakdown.

#### `GET /api/mi/revenue-ageing/summary`

**Parameters**: All geographical + category filters, `project`, `level`, `duration` (currently only `monthly` is populated in the ETL — default **`monthly`**), optional `meter_category` or `category` (`consumer` / `feeder` / `dt`), `start_date`, `end_date`.

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
  },
  "comparison": [
    {
      "label": "AGRA",
      "age_0_30": 120,
      "age_31_60": 90,
      "age_61_90": 50,
      "age_90_plus": 800,
      "total_pending": 1060
    }
  ]
}
```

**Frontend usage**

- **Category / trend**: `category_breakdown` and `period_breakdown` (nested by meter category → meter type → four age buckets).
- **Comparison chart**: `comparison` — one object per cluster (`label`); each item has `age_0_30` … `age_90_plus` and `total_pending`.

---

### KPI 14 — Defective Meters ⭐ _Revamped_

Tracks defective meters based on complaint data, with focus on **replaced meters only** (where both old and new smart meter numbers are present). Complaints are categorized into **Meter Burnt**, **Meter Faulty**, and **Others**.

#### `GET /api/mi/defective-meters/summary`

**Parameters**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `duration` | `string` | Aggregation granularity: `daily` / `weekly` / `monthly` (default: `daily`) |
| `level` | `string` | Hierarchy level for comparison: `project`, `discom`, `zone`, `circle`, `division`, `subdivision` (default: `discom`) |
| `project` | `string` | Project filter: `all` (shows all 3 projects) or specific project (`AGRA`, `KASHI`, `TRIVENI`) (default: `all`) |
| `meter_category` | `string` | Optional filter: `consumer`, `feeder`, or `dt` (case-insensitive) |
| `start_date` / `end_date` | `string` | Date range filter (`YYYY-MM-DD`) |
| Plus all standard geographical filters: `discom`, `zone`, `circle`, `division`, `subdivision`, `substation`, `feeder`, `dtr`, `new_meter_type` |

**Behavior Notes**

- **Data source**: `unified_complaints` table, filtered to records where **both** `old_smart_meter_number` and `new_smart_meter_number` are present (indicates meter replacement).
- **Complaint categorization**:
  - `Meter Burnt`: "Meter Terminal Burnt", "Meter burnt", "Meter Sparking or Sparking at Meter terminal"
  - `Meter Faulty`: "Meter faulty or not working"
  - `Others`: all other complaint types
- **Trend chart**: Returns time-series at selected `duration` with counts per period for each meter category (CONSUMER/FEEDER/DT) and defective type (burnt/faulty/others).
- **Comparison chart**:
  - `project=all` & `level=discom` → 3 bars: `AGRA`, `KASHI`, `TRIVENI`
  - `project=all` & `level=zone/circle/division/subdivision` → composite labels like `AGRA | Zone-1`
  - `project=AGRA` & `level=zone` → zones within AGRA only
- **Category filter**: When `meter_category` is set, both trend and comparison show only that category; totals reflect filtered subset.

**Response** — `DefectiveMetersOut`

```json
{
  "total_defective": 484,
  "total_burnt": 67,
  "total_faulty": 36,
  "total_others": 381,
  "category_breakdown": {
    "CONSUMER": {
      "1PH-STSM": {
        "meter_burnt": 59,
        "meter_faulty": 22,
        "others": 338
      },
      "3PH-STSM": {
        "meter_burnt": 3,
        "meter_faulty": 2,
        "others": 9
      }
    },
    "FEEDER": {
      "HTCTPTSM": {
        "meter_burnt": 3,
        "meter_faulty": 4,
        "others": 10
      }
    },
    "DT": {
      "3PLTCTSM": {
        "meter_burnt": 1,
        "meter_faulty": 1,
        "others": 1
      }
    }
  },
  "trend": [
    {
      "period_value": "2026-04-16",
      "CONSUMER": 120,
      "FEEDER": 30,
      "DT": 15,
      "burnt": 10,
      "faulty": 25,
      "others": 130
    }
  ],
  "comparison": [
    {
      "label": "AGRA",
      "CONSUMER": 148,
      "FEEDER": 5,
      "DT": 0,
      "burnt": 38,
      "faulty": 9,
      "others": 108,
      "total_defective": 153
    },
    {
      "label": "KASHI",
      "CONSUMER": 200,
      "FEEDER": 3,
      "DT": 0,
      "burnt": 4,
      "faulty": 16,
      "others": 208,
      "total_defective": 203
    },
    {
      "label": "TRIVENI",
      "CONSUMER": 96,
      "FEEDER": 9,
      "DT": 27,
      "burnt": 25,
      "faulty": 11,
      "others": 65,
      "total_defective": 128
    }
  ]
}
```

**Frontend Usage**

- **Summary cards**: Use `total_defective`, `total_burnt`, `total_faulty`, `total_others`.
- **Trend chart**: Line chart with `period_value` on X-axis; plot `CONSUMER`, `FEEDER`, `DT` as separate series (or `burnt`/`faulty`/`others` as needed).
- **Comparison chart**: Bar chart with `label` on X-axis; stacked bars for `CONSUMER` + `FEEDER` + `DT` (or grouped by defective type).
- **Category breakdown**: Nested pie/bar charts from `category_breakdown` (outer key = meter_category, inner key = new_meter_type).

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
