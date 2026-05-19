# Smart Meter KPI API Contract — Dashboard Endpoints

> **Version**: 1.0 &nbsp;|&nbsp; **Last Updated**: 2026-05-04  
> This document covers only the **dashboard / summary** endpoints used by the frontend. For raw list endpoints, see `api_contract.md`.

---

## Base URL

| Environment | URL |
| :--- | :--- |
| Dev Tunnel | `https://2nbdzssr-8000.inc1.devtunnels.ms` |
| Local | `http://localhost:8000` |

**Swagger UI**: Append `/docs` to the Base URL for interactive exploration.

---

## Global Query Parameters

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
| `duration` | `string` | `daily` / `weekly` / `monthly` | Aggregation granularity used by dashboard-style endpoints |
| `start_date` | `string` | `YYYY-MM-DD` | Filter records on or after this date |
| `end_date` | `string` | `YYYY-MM-DD` | Filter records on or before this date |

### Pagination

| Parameter | Type | Default | Max | Description |
| :--- | :--- | :--- | :--- | :--- |
| `limit` | `int` | `1000` | `50000` | Maximum rows to return |
| `offset` | `int` | `0` | — | Number of rows to skip |

---

## Meter Installation (MI) KPIs

All MI endpoints are under the prefix `/api/mi`.

---

### KPI 1 — MI Progress Dashboard

Tracks the total number of meter installations over time.

#### `GET /api/mi/progress/dashboard`

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

- When `category=consumer` is selected, `consumer_meter_type` is flattened directly into the response payload objects (no nested keys or parent category keys).
- When `category=feeder` or `category=dt` is selected, the `total` key is replaced with the category name (`FEEDER` or `DT`).

**Response** — `MIProgressDashboardOut`

```json
{
  "total_progress": 120000,
  "trend": [
    {
      "period_value": "16-03-26",
      "total": 120,
      "1PH-Consumer_meter": 100,
      "3PH-Consumer_meter": 10,
      "LTCT-Consumer_meter": 5,
      "HTCT-Consumer_meter": 5
    }
  ],
  "comparison": [
    {
      "label": "KASHI",
      "total": 30000,
      "1PH-Consumer_meter": 25000,
      "3PH-Consumer_meter": 3000,
      "LTCT-Consumer_meter": 1500,
      "HTCT-Consumer_meter": 500
    }
  ]
}
```

---

### KPI 2.5 — MI Productivity per Team Dashboard

Provides aggregated productivity metrics grouped by **technician**, with trend and comparison visualizations.

**Productivity Logic**: Compute **daily productivity** as `total_installations_that_day / distinct_technicians_that_day`. For `duration=weekly/monthly`, the dashboard returns **average of the daily productivity values** within each bucket.

#### `GET /api/mi/productivity/team/dashboard`

**Parameters**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `duration` | `string` | Aggregation granularity: `daily` / `weekly` / `monthly` |
| `level` | `string` | Cluster level for comparison: `project`, `discom`, `zone`, `circle`, `division`, `subdivision` |
| `project` | `string` | Project filter: `all` or specific project name (`AGRA`, `KASHI`, `TRIVENI`) |
| `start_date` / `end_date` | `string` | Date range filter (`YYYY-MM-DD`) |
| Plus all standard geographical & category filters |

**Behavior Notes**

- **Trend chart**: Returns time-series data at the selected `duration` granularity. Each point includes total installations, active technicians count, and productivity per technician per day (avg-of-daily logic).
- **Comparison chart**:
  - If `project=all` + `level=project` or `level=discom` → 3 bars: `AGRA`, `KASHI`, `TRIVENI`
  - If `project=all` + `level=zone/circle/division/subdivision` → composite labels like `AGRA | AGRA I`, `KASHI | ZONE-A`
  - If `project=AGRA` + `level=zone` → bars: `AGRA I`, `AGRA II` (raw zone names, no project prefix)
- **Category breakdown**: Breaks down total installations and productivity per day by `meter_category` (`CONSUMER`, `FEEDER`, `DT`).
- **Insights**: Shows top and lowest performing technicians based on overall productivity.
- All installations are **verified only** (`sat_no IS NOT NULL` and non-empty).

**Response** — `MITeamProductivityDashboardOut`

```json
{
  "summary": {
    "total_installations": 15000,
    "total_active_technicians": 25,
    "total_active_days": 30,
    "productivity_per_technician_per_day": 20.0
  },
  "insights": {
    "top_performing_technician": {
      "name": "John Doe",
      "productivity_per_technician_per_day": 35.2
    },
    "lowest_performing_technician": {
      "name": "Jane Smith",
      "productivity_per_technician_per_day": 12.8
    }
  },
  "trend": [
    {
      "date": "2026-03-01",
      "total_installations": 500,
      "active_technicians": 5,
      "productivity_per_technician_per_day": 100.0
    },
    {
      "date": "2026-03-02",
      "total_installations": 550,
      "active_technicians": 5,
      "productivity_per_technician_per_day": 110.0
    }
  ],
  "comparison": [
    {
      "label": "AGRA",
      "total_installations": 5000,
      "active_technicians": 8,
      "productivity_per_technician_per_day": 20.83
    },
    {
      "label": "KASHI",
      "total_installations": 4500,
      "active_technicians": 7,
      "productivity_per_technician_per_day": 21.43
    },
    {
      "label": "TRIVENI",
      "total_installations": 5500,
      "active_technicians": 10,
      "productivity_per_technician_per_day": 18.33
    }
  ],
  "category_breakdown": {
    "CONSUMER": {
      "total_installations": 12000,
      "productivity_per_technician_per_day": 400.0
    },
    "FEEDER": {
      "total_installations": 2000,
      "productivity_per_technician_per_day": 66.6
    },
    "DT": {
      "total_installations": 1000,
      "productivity_per_technician_per_day": 33.3
    }
  }
}
```

**Frontend Usage**

- **Daily Performance Graph**: Use the `trend` array. X-axis = `date`, Y-axis = `productivity_per_technician_per_day` (or `total_installations`).
- **Comparison by Cluster**: Use the `comparison` array. Each bar's height = `productivity_per_technician_per_day`. Tooltip can show `total_installations` and `active_technicians`.
- **Summary Cards**: Use `summary` for overall KPIs (total installations, total active technicians, overall productivity).
- **Category Distribution**: Use `category_breakdown` for pie/bar charts by meter type.

---

### KPI 3.5 — Monthly Productivity Trend Dashboard

Provides a dashboard-ready view of **technician productivity trend** using the **KPI 2.5 avg-of-daily** method, rendered as a monthly trend by default (but supports daily/weekly/monthly buckets).

**Productivity Logic (same as KPI 2.5)**:
- **Daily productivity** = `total_installations_that_day / distinct_technicians_that_day`
- **Bucket productivity** (`duration=weekly/monthly`) = `AVG(daily productivity)` across the days in the bucket
- If a day has `0` active technicians, that day's productivity is treated as `0`

#### `GET /api/mi/productivity/trend/dashboard`

**Parameters**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `duration` | `string` | Aggregation granularity: `daily` / `weekly` / `monthly` (**default: `monthly`**) |
| `project` | `string` | Project filter: `all` or specific project name (`AGRA`, `KASHI`, `TRIVENI`) |
| `level` | `string` | Level for comparison grouping: `discom` / `zone` / `circle` / `division` / `subdivision` (default: `zone`) |
| `start_date` / `end_date` | `string` | Date range filter (`YYYY-MM-DD`) |
| Plus all standard geographical & category filters |

**Behavior Notes**

- **Trend chart**: Returns time-series at the selected `duration`. Each point includes `total_installations`, `active_days`, `avg_active_technicians`, and `productivity_per_technician_per_day`.
- **Comparison chart** — grouping mirrors KPI 1:
  - `project=all` & `level=discom` → 3 bars: `AGRA`, `KASHI`, `TRIVENI`
  - `project=all` & `level=zone/circle/division/subdivision` → composite labels like `AGRA | AGRA I`
  - `project=AGRA` & `level=zone` → bars show zones within AGRA only
- All installations are **verified only** (`sat_no IS NOT NULL`).

**Response** — `MIProductivityTrendDashboardOut`

```json
{
  "summary": {
    "total_installations": 305477,
    "total_active_months": 6,
    "productivity_per_technician_per_day": 20.83
  },
  "trend": [
    {
      "month": "2025-01",
      "total_installations": 129038,
      "active_days": 26,
      "avg_active_technicians": 45,
      "productivity_per_technician_per_day": 10.25
    },
    {
      "month": "2025-02",
      "total_installations": 121412,
      "active_days": 24,
      "avg_active_technicians": 48,
      "productivity_per_technician_per_day": 11.72
    }
  ],
  "comparison": [
    {
      "label": "AGRA",
      "total_installations": 305477,
      "active_days": 150,
      "avg_active_technicians": 47.2,
      "productivity_per_technician_per_day": 12.5
    },
    {
      "label": "KASHI",
      "total_installations": 257417,
      "active_days": 145,
      "avg_active_technicians": 44.8,
      "productivity_per_technician_per_day": 11.2
    },
    {
      "label": "TRIVENI",
      "total_installations": 235402,
      "active_days": 142,
      "avg_active_technicians": 43.1,
      "productivity_per_technician_per_day": 10.8
    }
  ],
  "category_breakdown": {
    "CONSUMER": { "total_installations": 12000, "active_days": 26, "avg_active_technicians": 40.2, "productivity_per_technician_per_day": 18.2 },
    "FEEDER": { "total_installations": 2000, "active_days": 26, "avg_active_technicians": 8.4, "productivity_per_technician_per_day": 9.5 },
    "DT": { "total_installations": 1000, "active_days": 26, "avg_active_technicians": 5.1, "productivity_per_technician_per_day": 6.1 }
  }
}
```

**Frontend Usage**

- **Trend chart**: X-axis = `month` (or the chosen bucket label), Y-axis = `productivity_per_technician_per_day`. Tooltip can show `total_installations`, `active_days`, `avg_active_technicians`.
- **Comparison chart**: Bar height = `productivity_per_technician_per_day`, label from `comparison[].label`.
- **Summary cards**: Use `summary` for headline numbers.

---

### KPI 4 — Inventory Utilization Summary

Tracks stock received vs. stock installed with utilization percentage.

#### `GET /api/mi/inventory-utilization/summary`

**Parameters**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `duration` | `string` | Aggregation granularity: `daily` / `weekly` / `monthly` (default: `daily`) |
| `level` | `string` | Hierarchy level for comparison grouping: `discom` / `zone` / `circle` / `division` / `subdivision` (default: `discom`) |
| `project` | `string` | Project filter: `all` or specific project (`AGRA`, `KASHI`, `TRIVENI`) |
| `category` | `string` | Optional meter category filter: `total` (all categories), `consumer`, `feeder`, or `dt` (case-insensitive). Default: `total` |
| `start_date` / `end_date` | `string` | Date range filter (`YYYY-MM-DD`) |
| Plus all standard geographical filters: `discom`, `zone`, `circle`, `division`, `subdivision`, `substation`, `feeder`, `dtr`, `new_meter_type` |

**Behavior Notes**

- **No `category_breakdown`** — removed. Category detail is flattened into `period_breakdown` and `comparison`.
- **Period breakdown**: Flat array (like KPI 1's `trend`). Each element contains `period_value`, `total_inventory`, `total_installed`, `utilization_rate_pct`, and category-specific keys. For `category=total` or `category=consumer`, each category key is an object `{ inventory, installed, utilization_rate_pct }` where `utilization_rate_pct` is computed for that bucket.
- **Category-aware keys** (mirrors KPI 1 logic):
  - When `category=total`: keys are `CONSUMER`, `FEEDER`, `DT` — each holding `{ inventory, installed, utilization_rate_pct }`.
  - When `category=consumer`: keys are `1PH-Consumer_meter`, `3PH-Consumer_meter`, `LTCT-Consumer_meter`, `HTCT-Consumer_meter` — each holding `{ inventory, installed, utilization_rate_pct }`.
  - When `category=feeder` or `category=dt`: no category-specific keys are returned; use the top-level `total_inventory` and `total_installed` counts instead.
- **Comparison chart** — grouping mirrors KPI 1:
  - `project=all` & `level=discom` → 3 bars: `AGRA`, `KASHI`, `TRIVENI`
  - `project=all` & `level=zone/circle/division/subdivision` → composite labels like `AGRA | AGRA I`
  - `project=AGRA` & `level=zone` → bars show zones within AGRA only
  - Each bar includes: `label`, `total_inventory`, `total_installed`, `utilization_rate_pct`, and the same category-aware keys (with per-bucket `utilization_rate_pct` when `category=total` or `category=consumer`).
- Date filtering uses `_period_value_as_date()` to convert stored `period_value` strings to real dates.

**Response (category=total)** — `InventoryUtilizationSummaryOut`

```json
{
  "total_inventory": 50000,
  "total_installed": 15000,
  "utilization_rate_pct": 30.0,
  "remaining_stock": 35000,
  "period_breakdown": [
    {
      "period_value": "01-01-25",
      "total_inventory": 5000,
      "total_installed": 1500,
      "utilization_rate_pct": 30.0,
      "CONSUMER": { "inventory": 4000, "installed": 1200, "utilization_rate_pct": 30.0 },
      "FEEDER": { "inventory": 600, "installed": 200, "utilization_rate_pct": 33.33 },
      "DT": { "inventory": 400, "installed": 100, "utilization_rate_pct": 25.0 }
    }
  ],
  "comparison": [
    {
      "label": "AGRA I",
      "total_inventory": 18000,
      "total_installed": 5400,
      "utilization_rate_pct": 30.0,
      "CONSUMER": { "inventory": 14000, "installed": 3200, "utilization_rate_pct": 22.86 },
      "FEEDER": { "inventory": 2500, "installed": 1400, "utilization_rate_pct": 56.0 },
      "DT": { "inventory": 1500, "installed": 800, "utilization_rate_pct": 53.33 }
    },
    {
      "label": "AGRA II",
      "total_inventory": 15000,
      "total_installed": 4500,
      "utilization_rate_pct": 30.0,
      "CONSUMER": { "inventory": 12000, "installed": 2500, "utilization_rate_pct": 20.83 },
      "FEEDER": { "inventory": 2000, "installed": 1200, "utilization_rate_pct": 60.0 },
      "DT": { "inventory": 1000, "installed": 800, "utilization_rate_pct": 80.0 }
    }
  ]
}
```

**Response (category=consumer)** — `InventoryUtilizationSummaryOut`

```json
{
  "total_inventory": 40000,
  "total_installed": 12000,
  "utilization_rate_pct": 30.0,
  "remaining_stock": 28000,
  "period_breakdown": [
    {
      "period_value": "01-01-25",
      "total_inventory": 5000,
      "total_installed": 1500,
      "utilization_rate_pct": 30.0,
      "1PH-Consumer_meter": { "inventory": 4000, "installed": 1200, "utilization_rate_pct": 30.0 },
      "3PH-Consumer_meter": { "inventory": 500, "installed": 150, "utilization_rate_pct": 30.0 },
      "LTCT-Consumer_meter": { "inventory": 300, "installed": 100, "utilization_rate_pct": 33.33 },
      "HTCT-Consumer_meter": { "inventory": 200, "installed": 50, "utilization_rate_pct": 25.0 }
    }
  ],
  "comparison": [
    {
      "label": "AGRA I",
      "total_inventory": 14000,
      "total_installed": 3200,
      "utilization_rate_pct": 22.86,
      "1PH-Consumer_meter": { "inventory": 11000, "installed": 2500, "utilization_rate_pct": 22.73 },
      "3PH-Consumer_meter": { "inventory": 1500, "installed": 400, "utilization_rate_pct": 26.67 },
      "LTCT-Consumer_meter": { "inventory": 1000, "installed": 200, "utilization_rate_pct": 20.0 },
      "HTCT-Consumer_meter": { "inventory": 500, "installed": 100, "utilization_rate_pct": 20.0 }
    }
  ]
}
```

---

### KPI 5 — Pace vs Stock Summary

Focused view of installation pace against stock. Shares the same data source and logic as KPI 4. Each row uses `remaining_stock` instead of `utilization_rate_pct` at the period/comparison level; for `category=total` or `category=consumer`, nested category objects use `remaining_stock` per bucket (not `utilization_rate_pct`).

#### `GET /api/mi/pace-vs-stock/summary`

**Parameters**

Identical to `GET /api/mi/inventory-utilization/summary`:
`duration`, `category`, `level`, `project`, `start_date`, `end_date`, plus all standard geographical filters.

**Behavior Notes**

- Same category-aware flattening as KPI 4 (see above).
- `period_breakdown` and `comparison` rows use `remaining_stock` instead of `utilization_rate_pct` for the overall totals line.
- When `category=total` or `category=consumer`, each nested bucket (`CONSUMER` / `FEEDER` / `DT` or consumer meter keys) includes `remaining_stock` computed for that bucket (`inventory - installed`, floored at zero).
- Top-level retains `utilization_rate_pct` for overall utilization percentage.

**Response (category=total)** — `PaceVsStockSummaryOut`

```json
{
  "total_inventory": 50000,
  "total_installed": 15000,
  "utilization_rate_pct": 30.0,
  "remaining_stock": 35000,
  "period_breakdown": [
    {
      "period_value": "01-01-25",
      "total_inventory": 5000,
      "total_installed": 1500,
      "remaining_stock": 3500,
      "CONSUMER": { "inventory": 4000, "installed": 1200, "remaining_stock": 2800 },
      "FEEDER": { "inventory": 600, "installed": 200, "remaining_stock": 400 },
      "DT": { "inventory": 400, "installed": 100, "remaining_stock": 300 }
    }
  ],
  "comparison": [
    {
      "label": "AGRA I",
      "total_inventory": 18000,
      "total_installed": 5400,
      "remaining_stock": 12600,
      "CONSUMER": { "inventory": 14000, "installed": 3200, "remaining_stock": 10800 },
      "FEEDER": { "inventory": 2500, "installed": 1400, "remaining_stock": 1100 },
      "DT": { "inventory": 1500, "installed": 800, "remaining_stock": 700 }
    }
  ]
}
```

**Response (category=consumer)** — `PaceVsStockSummaryOut`

```json
{
  "total_inventory": 40000,
  "total_installed": 12000,
  "utilization_rate_pct": 30.0,
  "remaining_stock": 28000,
  "period_breakdown": [
    {
      "period_value": "01-01-25",
      "total_inventory": 5000,
      "total_installed": 1500,
      "remaining_stock": 3500,
      "1PH-Consumer_meter": { "inventory": 4000, "installed": 1200, "remaining_stock": 2800 },
      "3PH-Consumer_meter": { "inventory": 500, "installed": 150, "remaining_stock": 350 },
      "LTCT-Consumer_meter": { "inventory": 300, "installed": 100, "remaining_stock": 200 },
      "HTCT-Consumer_meter": { "inventory": 200, "installed": 50, "remaining_stock": 150 }
    }
  ],
  "comparison": [
    {
      "label": "AGRA I",
      "total_inventory": 14000,
      "total_installed": 3200,
      "remaining_stock": 10800,
      "1PH-Consumer_meter": { "inventory": 11000, "installed": 2500, "remaining_stock": 8500 },
      "3PH-Consumer_meter": { "inventory": 1500, "installed": 400, "remaining_stock": 1100 },
      "LTCT-Consumer_meter": { "inventory": 1000, "installed": 200, "remaining_stock": 800 },
      "HTCT-Consumer_meter": { "inventory": 500, "installed": 100, "remaining_stock": 400 }
    }
  ]
}
```

---

### KPI 6 — Stock Ageing Dashboard

Tracks how long dispatched meters remain uninstalled, categorized into aging buckets (0-30, 31-60, 61-90, 90+ days).

#### `GET /api/mi/stock-ageing/dashboard`

**Parameters**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `duration` | `string` | Aggregation granularity: `daily` / `weekly` / `monthly` (default: `monthly`) |
| `level` | `string` | Hierarchy level for comparison grouping: `discom` / `zone` / `circle` / `division` / `subdivision` (default: `discom`) |
| `project` | `string` | Project filter: `all` or specific project (`AGRA`, `KASHI`, `TRIVENI`) (default: `all`) |
| `category` | `string` | Meter category filter: `total` / `consumer` / `feeder` / `dt` (default: `total`) |
| `start_date` / `end_date` | `string` | Date range filter (`YYYY-MM-DD`) |
| Plus all standard geographical & category filters |

**Behavior Notes**

- **Data source**: Uses pre-aggregated table with separate `period_type` entries for daily, weekly, and monthly granularities.
- **Comparison chart**: Grouping mirrors KPI 1. Contains dynamic sub-keys depending on the `category` filter.
- **Trend chart (`summary`)**: Rather than a time-series trend, this provides an overall summary mapping total stock into age buckets (`0-30 days`, `31-60 days`, etc.), mirroring the dashboard's "Stock Ageing Trend" visualization.
- **Category Formatting**:
  - `category=total`: Age buckets embed `CONSUMER`, `FEEDER`, `DT` sub-keys.
  - `category=consumer`: Age buckets embed `1PH-Consumer_meter`, `3PH-Consumer_meter`, `LTCT-Consumer_meter`, `HTCT-Consumer_meter` sub-keys.
  - `category=feeder/dt`: Age buckets contain flat totals.

**Response** — `StockAgeingDashboardOut`

```json
{
  "total_stock": 62000,
  "summary": {
    "age_0_30": { "CONSUMER": 0, "FEEDER": 0, "DT": 0, "total": 0 },
    "age_31_60": { "CONSUMER": 0, "FEEDER": 0, "DT": 0, "total": 0 },
    "age_61_90": { "CONSUMER": 10000, "FEEDER": 1000, "DT": 1000, "total": 12000 },
    "age_90_plus": { "CONSUMER": 45000, "FEEDER": 3000, "DT": 2000, "total": 50000 },
    "total_stock": 62000
  },
  "comparison": [
    {
      "label": "AGRA",
      "age_0_30": { "CONSUMER": 0, "FEEDER": 0, "DT": 0, "total": 0 },
      "age_31_60": { "CONSUMER": 0, "FEEDER": 0, "DT": 0, "total": 0 },
      "age_61_90": { "CONSUMER": 10000, "FEEDER": 1000, "DT": 1000, "total": 12000 },
      "age_90_plus": { "CONSUMER": 45000, "FEEDER": 3000, "DT": 2000, "total": 50000 },
      "total_stock": 62000
    }
  ]
}
```

**Frontend Usage**

- **Top Summary**: Use `total_stock` for the big number.
- **Stock Ageing Trend (Left Chart)**: Use the `summary` object. The X-axis represents the age bucket classifications. Use the nested sub-keys for stacked series grouping.
- **Comparison By Cluster (Right Chart)**: Use the `comparison` array. Group by `label` and stack bars using the nested sub-keys within the respective age buckets.
---

### KPI 7 — MI vs SAT Summary

Compares Meter Installation against SAT (Site Acceptance Test) completion across 9 stages.

#### `GET /api/mi/mi-vs-sat/summary`

**Parameters**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `duration` | `string` | Aggregation granularity: `daily` / `weekly` / `monthly` (default: `daily`) |
| `level` | `string` | Hierarchy level for comparison grouping: `discom` / `zone` / `circle` / `division` / `subdivision` (default: `discom`) |
| `project` | `string` | Project filter: `all` or specific project (`AGRA`, `KASHI`, `TRIVENI`) |
| `category` | `string` | Optional meter category filter: `total` (default), `consumer`, `feeder`, or `dt` |
| `new_meter_type` | `string` | Optional meter hardware type filter |
| `start_date` / `end_date` | `string` | Date range filter (`YYYY-MM-DD`) |
| Plus all standard geographical filters |

**Behavior Notes**

- **No `category_breakdown` or `period_breakdown`** — removed. Category detail is flattened into `summary` and `comparison`.
- **Summary**: An object where each SAT stage (`sat_1` through `sat_9`) contains category-aware sub-keys.
- **Category-aware keys** (mirrors KPI 4/6 logic):
  - When `category=total`: each stage is `{ CONSUMER, FEEDER, DT, total }`.
  - When `category=consumer`: each stage is `{ 1PH-Consumer_meter, 3PH-Consumer_meter, LTCT-Consumer_meter, HTCT-Consumer_meter, total }`.
  - When `category=feeder` or `category=dt`: each stage is a flat integer (only the count for that category).
- **Comparison chart** — grouping mirrors KPI 1. Each comparison item includes `total_mi`, `total_sat`, `sat_progress_pct`, and SAT stage breakdowns in the same format as `summary`.
- **SAT stage counts**: Each `sat_N` counts meters whose `sat_no` matches the pattern `sat-N%` (SAT completion counts).

**Response (category=total)** — `MIvsSATSummaryOut`

```json
{
  "total_mi": 1086387,
  "total_sat": 696186,
  "sat_progress_pct": 64.08,
  "summary": {
    "sat_1": { "CONSUMER": 167000, "FEEDER": 42000, "DT": 19242, "total": 228242 },
    "sat_2": { "CONSUMER": 125000, "FEEDER": 32000, "DT": 14406, "total": 171406 },
    "sat_3": { "CONSUMER": 123000, "FEEDER": 31000, "DT": 15023, "total": 169023 },
    "sat_4": { "CONSUMER": 42000, "FEEDER": 12000, "DT": 3999, "total": 57999 },
    "sat_5": { "CONSUMER": 21000, "FEEDER": 5500, "DT": 1679, "total": 28179 },
    "sat_6": { "CONSUMER": 15000, "FEEDER": 4000, "DT": 1990, "total": 20990 },
    "sat_7": { "CONSUMER": 14500, "FEEDER": 4000, "DT": 1847, "total": 20347 },
    "sat_8": { "CONSUMER": 0, "FEEDER": 0, "DT": 0, "total": 0 },
    "sat_9": { "CONSUMER": 0, "FEEDER": 0, "DT": 0, "total": 0 }
  },
  "comparison": [
    {
      "label": "AGRA",
      "total_mi": 540000,
      "total_sat": 345600,
      "sat_progress_pct": 64.0,
      "sat_1": { "CONSUMER": 80000, "FEEDER": 20000, "DT": 9000, "total": 109000 },
      "sat_2": { "CONSUMER": 60000, "FEEDER": 15000, "DT": 7000, "total": 82000 },
      "sat_3": { "CONSUMER": 59000, "FEEDER": 14000, "DT": 7000, "total": 80000 },
      "sat_4": { "CONSUMER": 20000, "FEEDER": 6000, "DT": 2000, "total": 28000 },
      "sat_5": { "CONSUMER": 10000, "FEEDER": 2500, "DT": 800, "total": 13300 },
      "sat_6": { "CONSUMER": 7000, "FEEDER": 2000, "DT": 1000, "total": 10000 },
      "sat_7": { "CONSUMER": 7000, "FEEDER": 2000, "DT": 900, "total": 9900 },
      "sat_8": { "CONSUMER": 0, "FEEDER": 0, "DT": 0, "total": 0 },
      "sat_9": { "CONSUMER": 0, "FEEDER": 0, "DT": 0, "total": 0 }
    },
    {
      "label": "KASHI",
      "total_mi": 410000,
      "total_sat": 262400,
      "sat_progress_pct": 64.0,
      "sat_1": { "CONSUMER": 60000, "FEEDER": 15000, "DT": 7000, "total": 82000 },
      "sat_2": { "...": "..." },
      "sat_9": { "CONSUMER": 0, "FEEDER": 0, "DT": 0, "total": 0 }
    }
  ]
}
```

**Response (category=consumer)** — `MIvsSATSummaryOut`

```json
{
  "total_mi": 800000,
  "total_sat": 512000,
  "sat_progress_pct": 64.0,
  "summary": {
    "sat_1": { "1PH-Consumer_meter": 150000, "3PH-Consumer_meter": 10000, "LTCT-Consumer_meter": 5000, "HTCT-Consumer_meter": 2000, "total": 167000 },
    "sat_2": { "1PH-Consumer_meter": 112000, "3PH-Consumer_meter": 8000, "LTCT-Consumer_meter": 3500, "HTCT-Consumer_meter": 1500, "total": 125000 },
    "sat_3": { "...": "..." },
    "sat_9": { "1PH-Consumer_meter": 0, "3PH-Consumer_meter": 0, "LTCT-Consumer_meter": 0, "HTCT-Consumer_meter": 0, "total": 0 }
  },
  "comparison": [
    {
      "label": "AGRA",
      "total_mi": 400000,
      "total_sat": 256000,
      "sat_progress_pct": 64.0,
      "sat_1": { "1PH-Consumer_meter": 72000, "3PH-Consumer_meter": 5000, "LTCT-Consumer_meter": 2000, "HTCT-Consumer_meter": 1000, "total": 80000 },
      "sat_2": { "...": "..." },
      "sat_9": { "1PH-Consumer_meter": 0, "3PH-Consumer_meter": 0, "LTCT-Consumer_meter": 0, "HTCT-Consumer_meter": 0, "total": 0 }
    }
  ]
}
```

**Response (category=feeder)** — `MIvsSATSummaryOut`

```json
{
  "total_mi": 200000,
  "total_sat": 128000,
  "sat_progress_pct": 64.0,
  "summary": {
    "sat_1": 42000,
    "sat_2": 32000,
    "sat_3": 31000,
    "sat_4": 12000,
    "sat_5": 5500,
    "sat_6": 4000,
    "sat_7": 4000,
    "sat_8": 0,
    "sat_9": 0
  },
  "comparison": [
    {
      "label": "AGRA",
      "total_mi": 100000,
      "total_sat": 64000,
      "sat_progress_pct": 64.0,
      "sat_1": 20000,
      "sat_2": 15000,
      "sat_3": 14000,
      "sat_4": 6000,
      "sat_5": 2500,
      "sat_6": 2000,
      "sat_7": 2000,
      "sat_8": 0,
      "sat_9": 0
    }
  ]
}
```

**Frontend Usage**

- **Top Summary**: Use `total_mi`, `total_sat`, `sat_progress_pct` for headline cards.
- **SAT Stage Breakdown Chart**: Use the `summary` object. Each `sat_N` key contains category-aware sub-keys for stacked series grouping.
- **Comparison By Cluster**: Use the `comparison` array. Group by `label`, each item mirrors the `summary` format for SAT stage breakdowns.


### KPI 8 — Non-SAT Ageing Dashboard

Lists installed meters that have not yet completed SAT, with ageing bucket distributions.

#### `GET /api/mi/non-sat-ageing/dashboard`

**Parameters**

- `duration`: `daily` / `weekly` / `monthly` (aggregation granularity)
- `category`: `total` / `consumer` / `feeder` / `dt` (meter category filter)
- `level`: `discom` / `zone` / `circle` / `division` / `subdivision`
- `project`: `all` / `kashi` / `agra` / `triveni`
- `start_date` / `end_date`: `YYYY-MM-DD` (installation date range filter)
- Plus the usual geo filters and `new_meter_type`

**Behavior Notes**

- **No `category_breakdown` or `period_breakdown`** — removed. Category detail is flattened into `summary` and `comparison`.
- **Ageing buckets**: `age_0_30`, `age_31_60`, `age_61_90`, `age_91_120`, `age_120_plus`.
- **Category-aware keys** (mirrors KPI 4 logic):
  - When `category=total`: each ageing bucket is an object containing `{ CONSUMER, FEEDER, DT, total }`.
  - When `category=consumer`: each ageing bucket is an object containing `{ 1PH-Consumer_meter, 3PH-Consumer_meter, LTCT-Consumer_meter, HTCT-Consumer_meter, total }`.
  - When `category=feeder` or `category=dt`: each ageing bucket is a flat integer (only the count for that category).
- Comparison and label rules mirror KPI 1.
- `start_date/end_date` filter on the installation date (`date_value`).

**Response (category=total)** — `NonSATAgeingDashboardOut`

```json
{
  "total_non_sat": 882002,
  "summary": {
    "age_0_30": { "CONSUMER": 0, "FEEDER": 0, "DT": 0, "total": 0 },
    "age_31_60": { "CONSUMER": 0, "FEEDER": 0, "DT": 0, "total": 0 },
    "age_61_90": { "CONSUMER": 265000, "FEEDER": 100, "DT": 21344, "total": 286444 },
    "age_91_120": { "CONSUMER": 275000, "FEEDER": 150, "DT": 23804, "total": 298954 },
    "age_120_plus": { "CONSUMER": 279605, "FEEDER": 31, "DT": 16968, "total": 296604 },
    "total_non_sat": 882002
  },
  "comparison": [
    {
      "label": "KASHI",
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

**Response (category=consumer)** — `NonSATAgeingDashboardOut`

```json
{
  "total_non_sat": 819605,
  "summary": {
    "age_0_30": { "1PH-Consumer_meter": 0, "3PH-Consumer_meter": 0, "LTCT-Consumer_meter": 0, "HTCT-Consumer_meter": 0, "total": 0 },
    "age_31_60": { "1PH-Consumer_meter": 0, "3PH-Consumer_meter": 0, "LTCT-Consumer_meter": 0, "HTCT-Consumer_meter": 0, "total": 0 },
    "age_61_90": { "1PH-Consumer_meter": 260000, "3PH-Consumer_meter": 4000, "LTCT-Consumer_meter": 1000, "HTCT-Consumer_meter": 0, "total": 265000 },
    "age_91_120": { "...": "..." },
    "age_120_plus": { "...": "..." },
    "total_non_sat": 819605
  },
  "comparison": [
    {
      "label": "KASHI",
      "age_0_30": { "1PH-Consumer_meter": 0, "3PH-Consumer_meter": 0, "LTCT-Consumer_meter": 0, "HTCT-Consumer_meter": 0, "total": 0 },
      "age_31_60": { "1PH-Consumer_meter": 0, "3PH-Consumer_meter": 0, "LTCT-Consumer_meter": 0, "HTCT-Consumer_meter": 0, "total": 0 },
      "age_61_90": { "1PH-Consumer_meter": 11000, "3PH-Consumer_meter": 1000, "LTCT-Consumer_meter": 0, "HTCT-Consumer_meter": 0, "total": 12000 },
      "age_91_120": { "...": "..." },
      "age_120_plus": { "...": "..." },
      "total_non_sat": 40000
    }
  ]
}
```

**Response (category=feeder)** — `NonSATAgeingDashboardOut`

```json
{
  "total_non_sat": 281,
  "summary": {
    "age_0_30": 0,
    "age_31_60": 0,
    "age_61_90": 100,
    "age_91_120": 150,
    "age_120_plus": 31,
    "total_non_sat": 281
  },
  "comparison": [
    {
      "label": "KASHI",
      "age_0_30": 0,
      "age_31_60": 0,
      "age_61_90": 50,
      "age_91_120": 100,
      "age_120_plus": 20,
      "total_non_sat": 25000
    }
  ]
}
```

---

### KPI 9 — Meter Journey Dashboard

Average **calendar days** per stage for meters that have **completed PMPM revenue** (`pmpm_collection_date` is not null). Stage averages are rounded **up** to whole days (`ceil`).

**Stage definitions**

| Field | Span |
| :--- | :--- |
| `inventory_to_store` | `gmrtoagencyts::date - didate::date` |
| `store_to_agency` | `agencytosupts::date - gmrtoagencyts::date` |
| `agency_to_meter_installation` | `installedts::date - agencytosupts::date` |
| `meter_installation_to_sat` | `sat_date::date - installedts::date` |
| `sat_to_invoice` | `pmpm_invoice_date::date - sat_date::date` |
| `invoice_to_revenue` | `pmpm_collection_date::date - pmpm_invoice_date::date` |
| `total_journey` | `pmpm_collection_date::date - didate::date` |

#### `GET /api/mi/meter-journey/dashboard`

**Parameters**

| Parameter | Description |
| :--- | :--- |
| `duration` | `daily` / `weekly` / `monthly` (default `daily`) |
| `category` | `total` (default) or `consumer` / `feeder` / `dt` |
| `level` | `discom` (default), `zone`, `circle`, `division`, `subdivision`, `substation`, `feeder`, `dtr` |
| `project` | `all` (default) or a single project code |
| `start_date` / `end_date` | Optional `YYYY-MM-DD` — filter on `period_value` date range |
| Plus optional geo/category filters |

**Behavior Notes**

- **Summary** and **comparison**: weighted mean per stage over all matching rows.
- Comparison label rules mirror KPI 1, with extended level support including `substation`, `feeder`, `dtr`.
- **`category=consumer`**: each stage field and `meter_count` are **nested by meter-type group** (`1PH-Consumer_meter`, `3PH-Consumer_meter`, `LTCT-Consumer_meter`, `HTCT-Consumer_meter`, `total`). Same pattern as KPI 6.
- **`category=total`**: each stage field and `meter_count` are **nested by category** (`CONSUMER`, `FEEDER`, `DT`, `total`).
- **`category=feeder` / `category=dt`**: stage fields are **flat integers** (no nesting). In **comparison** items, **`label` is first** in the JSON object order.

**Response** — `MeterJourneyDashboardOut`

**Example: `category=feeder` or `category=dt`** (flat)

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

**Example: `category=consumer`** (nested by meter-type)

```json
{
  "summary": {
    "inventory_to_store": {
      "1PH-Consumer_meter": 5,
      "3PH-Consumer_meter": 7,
      "LTCT-Consumer_meter": 4,
      "HTCT-Consumer_meter": 6,
      "total": 6
    },
    "store_to_agency": {
      "1PH-Consumer_meter": 3,
      "3PH-Consumer_meter": 4,
      "LTCT-Consumer_meter": 2,
      "HTCT-Consumer_meter": 5,
      "total": 3
    },
    "agency_to_meter_installation": { "1PH-Consumer_meter": 6, "3PH-Consumer_meter": 8, "LTCT-Consumer_meter": 5, "HTCT-Consumer_meter": 7, "total": 6 },
    "meter_installation_to_sat": { "1PH-Consumer_meter": 12, "3PH-Consumer_meter": 14, "LTCT-Consumer_meter": 10, "HTCT-Consumer_meter": 15, "total": 12 },
    "sat_to_invoice": { "1PH-Consumer_meter": 4, "3PH-Consumer_meter": 5, "LTCT-Consumer_meter": 3, "HTCT-Consumer_meter": 6, "total": 4 },
    "invoice_to_revenue": { "1PH-Consumer_meter": 5, "3PH-Consumer_meter": 6, "LTCT-Consumer_meter": 4, "HTCT-Consumer_meter": 7, "total": 5 },
    "total_journey": { "1PH-Consumer_meter": 35, "3PH-Consumer_meter": 44, "LTCT-Consumer_meter": 28, "HTCT-Consumer_meter": 46, "total": 36 },
    "meter_count": { "1PH-Consumer_meter": 3000, "3PH-Consumer_meter": 1200, "LTCT-Consumer_meter": 500, "HTCT-Consumer_meter": 300, "total": 5000 }
  },
  "comparison": [
    {
      "label": "AGRA",
      "inventory_to_store": { "1PH-Consumer_meter": 5, "3PH-Consumer_meter": 7, "LTCT-Consumer_meter": 4, "HTCT-Consumer_meter": 6, "total": 6 },
      "store_to_agency": { "1PH-Consumer_meter": 3, "3PH-Consumer_meter": 4, "LTCT-Consumer_meter": 2, "HTCT-Consumer_meter": 5, "total": 3 },
      "agency_to_meter_installation": { "1PH-Consumer_meter": 6, "3PH-Consumer_meter": 8, "LTCT-Consumer_meter": 5, "HTCT-Consumer_meter": 7, "total": 6 },
      "meter_installation_to_sat": { "1PH-Consumer_meter": 12, "3PH-Consumer_meter": 14, "LTCT-Consumer_meter": 10, "HTCT-Consumer_meter": 15, "total": 12 },
      "sat_to_invoice": { "1PH-Consumer_meter": 4, "3PH-Consumer_meter": 5, "LTCT-Consumer_meter": 3, "HTCT-Consumer_meter": 6, "total": 4 },
      "invoice_to_revenue": { "1PH-Consumer_meter": 5, "3PH-Consumer_meter": 6, "LTCT-Consumer_meter": 4, "HTCT-Consumer_meter": 7, "total": 5 },
      "total_journey": { "1PH-Consumer_meter": 35, "3PH-Consumer_meter": 44, "LTCT-Consumer_meter": 28, "HTCT-Consumer_meter": 46, "total": 36 },
      "meter_count": { "1PH-Consumer_meter": 1000, "3PH-Consumer_meter": 500, "LTCT-Consumer_meter": 200, "HTCT-Consumer_meter": 100, "total": 1800 }
    }
  ]
}
```

**Example: `category=total`** (nested by category)

```json
{
  "summary": {
    "inventory_to_store": { "CONSUMER": 5, "FEEDER": 3, "DT": 4, "total": 5 },
    "store_to_agency": { "CONSUMER": 3, "FEEDER": 2, "DT": 3, "total": 3 },
    "agency_to_meter_installation": { "CONSUMER": 6, "FEEDER": 4, "DT": 5, "total": 6 },
    "meter_installation_to_sat": { "CONSUMER": 12, "FEEDER": 8, "DT": 10, "total": 11 },
    "sat_to_invoice": { "CONSUMER": 4, "FEEDER": 3, "DT": 3, "total": 4 },
    "invoice_to_revenue": { "CONSUMER": 5, "FEEDER": 4, "DT": 4, "total": 5 },
    "total_journey": { "CONSUMER": 35, "FEEDER": 24, "DT": 29, "total": 34 },
    "meter_count": { "CONSUMER": 5000, "FEEDER": 200, "DT": 150, "total": 5350 }
  },
  "comparison": [
    {
      "label": "AGRA",
      "inventory_to_store": { "CONSUMER": 5, "FEEDER": 3, "DT": 4, "total": 5 },
      "store_to_agency": { "CONSUMER": 3, "FEEDER": 2, "DT": 3, "total": 3 },
      "agency_to_meter_installation": { "CONSUMER": 6, "FEEDER": 4, "DT": 5, "total": 6 },
      "meter_installation_to_sat": { "CONSUMER": 12, "FEEDER": 8, "DT": 10, "total": 11 },
      "sat_to_invoice": { "CONSUMER": 4, "FEEDER": 3, "DT": 3, "total": 4 },
      "invoice_to_revenue": { "CONSUMER": 5, "FEEDER": 4, "DT": 4, "total": 5 },
      "total_journey": { "CONSUMER": 35, "FEEDER": 24, "DT": 29, "total": 34 },
      "meter_count": { "CONSUMER": 1800, "FEEDER": 80, "DT": 60, "total": 1940 }
    }
  ]
}
```

---

### KPI 10 — Meter Funnel Summary (Pending PMPM Collection)

Shows a four-stage funnel **only for meters that have not yet had PMPM collection** (`pmpm_collection_date IS NULL`). The response shape matches KPI 9 (`{ "summary", "comparison" }`); there is **no** `category_breakdown` and **no** top-level flat `inventory` / `installed` / etc.

**Metric definitions** (all counts apply only where `pmpm_collection_date IS NULL`)

| Metric | Additional condition |
| :--- | :--- |
| `inventory` | All such meters (same grain as legacy “inventory” row counts, but restricted to pending collection) |
| `installed` | `mi_date IS NOT NULL` AND `sat_no` is not null / non-empty |
| `sat_done` | `sat_date IS NOT NULL` |
| `invoice_done` | `pmpm_invoice_date IS NOT NULL` |

> **Breaking change (vs. older contract):** `revenue_collected` is removed. The fourth stage is `invoice_done` (PMPM invoice raised, collection still pending).

#### `GET /api/mi/meter-stage`

**Parameters**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `project` | `string` | `all` (default) or single project code |
| `category` | `string` | `total` (default) or `consumer` / `feeder` / `dt` |
| `level` | `string` | Comparison grouping: `discom` (default), `zone`, `circle`, `division`, `subdivision`, `substation`, `feeder`, `dtr` |
| Plus any standard geo/category filters |

**Behavior Notes**

- **`summary`** and **`comparison`** each expose the same four keys: `inventory`, `installed`, `sat_done`, `invoice_done`.
- **Nesting by `category`** (same rules as KPI 9 — Meter Journey):
  - `category=total` (default): each of the four fields is an object `{ CONSUMER, FEEDER, DT, total }`.
  - `category=consumer`: each field is an object `{ 1PH-Consumer_meter, 3PH-Consumer_meter, LTCT-Consumer_meter, HTCT-Consumer_meter, total }` (raw `new_meter_type` values from the warehouse are rolled up into these buckets).
  - `category=feeder` or `category=dt`: each field is a **flat integer** (only that category’s counts).
- **`comparison`**: One object per cluster label from the selected `level`; when `project=all` and `level` is below `discom`, labels follow the same composite rules as KPI 1 (e.g. `AGRA | <zone>`).
- `limit` / `offset` are accepted but ignored.

**Response** — `MeterStageFunnelSummaryOut` (`summary: object`, `comparison: array`)

**Example: `category=feeder` or `category=dt`** (flat integers)

```json
{
  "summary": {
    "inventory": 9314,
    "installed": 348,
    "sat_done": 67,
    "invoice_done": 54
  },
  "comparison": [
    {
      "label": "AGRA",
      "inventory": 4179,
      "installed": 139,
      "sat_done": 9,
      "invoice_done": 7
    }
  ]
}
```

**Example: `category=total`** (nested by category)

```json
{
  "summary": {
    "inventory": { "CONSUMER": 1800850, "FEEDER": 9314, "DT": 173718, "total": 1983882 },
    "installed": { "CONSUMER": 1589667, "FEEDER": 348, "DT": 79684, "total": 1669699 },
    "sat_done": { "CONSUMER": 738667, "FEEDER": 67, "DT": 17567, "total": 756301 },
    "invoice_done": { "CONSUMER": 328002, "FEEDER": 54, "DT": 8552, "total": 336608 }
  },
  "comparison": [
    {
      "label": "AGRA",
      "inventory": { "CONSUMER": 650383, "FEEDER": 4179, "DT": 63123, "total": 717685 },
      "installed": { "CONSUMER": 604024, "FEEDER": 139, "DT": 17477, "total": 621640 },
      "sat_done": { "CONSUMER": 314650, "FEEDER": 9, "DT": 6741, "total": 321400 },
      "invoice_done": { "CONSUMER": 125929, "FEEDER": 7, "DT": 3317, "total": 129253 }
    }
  ]
}
```

**Example: `category=consumer`** (nested by consumer meter-type bucket)

```json
{
  "summary": {
    "inventory": {
      "1PH-Consumer_meter": 1769634,
      "3PH-Consumer_meter": 29388,
      "LTCT-Consumer_meter": 1000,
      "HTCT-Consumer_meter": 674,
      "total": 1800696
    },
    "installed": {
      "1PH-Consumer_meter": 1572180,
      "3PH-Consumer_meter": 16143,
      "LTCT-Consumer_meter": 774,
      "HTCT-Consumer_meter": 551,
      "total": 1589648
    },
    "sat_done": {
      "1PH-Consumer_meter": 732328,
      "3PH-Consumer_meter": 5919,
      "LTCT-Consumer_meter": 246,
      "HTCT-Consumer_meter": 170,
      "total": 738663
    },
    "invoice_done": {
      "1PH-Consumer_meter": 325584,
      "3PH-Consumer_meter": 2220,
      "LTCT-Consumer_meter": 109,
      "HTCT-Consumer_meter": 89,
      "total": 328002
    }
  },
  "comparison": [
    {
      "label": "AGRA",
      "inventory": {
        "1PH-Consumer_meter": 640417,
        "3PH-Consumer_meter": 9187,
        "LTCT-Consumer_meter": 604,
        "HTCT-Consumer_meter": 156,
        "total": 650364
      },
      "installed": {
        "1PH-Consumer_meter": 596730,
        "3PH-Consumer_meter": 6717,
        "LTCT-Consumer_meter": 455,
        "HTCT-Consumer_meter": 114,
        "total": 604016
      },
      "sat_done": {
        "1PH-Consumer_meter": 311424,
        "3PH-Consumer_meter": 3020,
        "LTCT-Consumer_meter": 172,
        "HTCT-Consumer_meter": 30,
        "total": 314646
      },
      "invoice_done": {
        "1PH-Consumer_meter": 124848,
        "3PH-Consumer_meter": 997,
        "LTCT-Consumer_meter": 74,
        "HTCT-Consumer_meter": 10,
        "total": 125929
      }
    }
  ]
}
```

**Data source**

- Pre-aggregated table `sql_meter_current_stage`, populated by the ETL job `execute_kpi_10_meter_stage`. Pending columns: `pending_inventory`, `pending_installed`, `pending_sat_done`, `pending_invoice_done`. Legacy columns `inventory` / `installed` / `sat_done` / `revenue_collected` may still exist for other consumers but are **not** returned by this endpoint.

---

### KPI 11 — MI vs SAT vs Invoice Summary

Tracks the funnel from MI → SAT → Invoice, with invoice broken down by type (Lumpsum vs PMPM).

**Formulas**:
- `total_mi` = Count of meters with MI date
- `total_sat` = Count of meters with SAT date
- `total_lumpsum_invoice` = Count of meters with `lumpsum_invoice_date` set
- `total_pmpm_invoice` = Count of meters with `pmpm_invoice_date` set
- `total_invoice` = `total_lumpsum_invoice + total_pmpm_invoice`

#### `GET /api/mi/mi-vs-sat-vs-invoice/summary`

**Parameters**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `duration` | `string` | Aggregation granularity: `daily` / `weekly` / `monthly` (default: `monthly`) |
| `level` | `string` | Hierarchy level for comparison grouping: `discom` / `zone` / `circle` / `division` / `subdivision` (default: `discom`) |
| `category` | `string` | Filter by meter category: `consumer` / `feeder` / `dt` |
| `project` | `string` | Project filter: `all` or specific project |
| `start_date` / `end_date` | `string` | Date range filter (`YYYY-MM-DD`) |
| Plus all standard geographical & category filters |

**Behavior Notes**

- **No `category_breakdown` or `period_breakdown`** — removed. Category detail is flattened into `summary` and `comparison`.
- **Category-aware keys** (mirrors KPI 8 logic):
  - When `category=total`: each stage is an object containing `{ CONSUMER, FEEDER, DT, total }`.
  - When `category=consumer`: each stage is an object containing `{ 1PH-Consumer_meter, 3PH-Consumer_meter, LTCT-Consumer_meter, HTCT-Consumer_meter, total }`.
  - When `category=feeder` or `category=dt`: each stage is a flat integer (only the count for that category).
- **Comparison chart**: Grouped totals by selected `level`, following KPI 1 label rules.

**Response (category=total)** — `MIvsSATvsInvoiceSummaryOut`

```json
{
  "summary": {
    "total_mi": { "CONSUMER": 2500000, "FEEDER": 500000, "DT": 381850, "total": 3381850 },
    "total_sat": { "CONSUMER": 1700000, "FEEDER": 350000, "DT": 243081, "total": 2293081 },
    "total_lumpsum_invoice": { "CONSUMER": 1200000, "FEEDER": 300000, "DT": 373388, "total": 1873388 },
    "total_pmpm_invoice": { "CONSUMER": 1200000, "FEEDER": 300000, "DT": 373388, "total": 1873388 }
  },
  "comparison": [
    {
      "label": "KASHI",
      "total_mi": { "CONSUMER": 800000, "FEEDER": 100000, "DT": 100000, "total": 1000000 },
      "total_sat": { "CONSUMER": 500000, "FEEDER": 100000, "DT": 80000, "total": 680000 },
      "total_lumpsum_invoice": { "CONSUMER": 400000, "FEEDER": 50000, "DT": 50000, "total": 500000 },
      "total_pmpm_invoice": { "CONSUMER": 400000, "FEEDER": 50000, "DT": 50000, "total": 500000 }
    }
  ]
}
```

**Response (category=consumer)** — `MIvsSATvsInvoiceSummaryOut`

```json
{
  "summary": {
    "total_mi": { "1PH-Consumer_meter": 2000000, "3PH-Consumer_meter": 500000, "LTCT-Consumer_meter": 0, "HTCT-Consumer_meter": 0, "total": 2500000 },
    "total_sat": { "1PH-Consumer_meter": 1300000, "3PH-Consumer_meter": 400000, "LTCT-Consumer_meter": 0, "HTCT-Consumer_meter": 0, "total": 1700000 },
    "total_lumpsum_invoice": { "1PH-Consumer_meter": 900000, "3PH-Consumer_meter": 300000, "LTCT-Consumer_meter": 0, "HTCT-Consumer_meter": 0, "total": 1200000 },
    "total_pmpm_invoice": { "1PH-Consumer_meter": 900000, "3PH-Consumer_meter": 300000, "LTCT-Consumer_meter": 0, "HTCT-Consumer_meter": 0, "total": 1200000 }
  },
  "comparison": [
    {
      "label": "KASHI",
      "total_mi": { "1PH-Consumer_meter": 600000, "3PH-Consumer_meter": 200000, "LTCT-Consumer_meter": 0, "HTCT-Consumer_meter": 0, "total": 800000 },
      "total_sat": { "1PH-Consumer_meter": 400000, "3PH-Consumer_meter": 100000, "LTCT-Consumer_meter": 0, "HTCT-Consumer_meter": 0, "total": 500000 },
      "total_lumpsum_invoice": { "1PH-Consumer_meter": 300000, "3PH-Consumer_meter": 100000, "LTCT-Consumer_meter": 0, "HTCT-Consumer_meter": 0, "total": 400000 },
      "total_pmpm_invoice": { "1PH-Consumer_meter": 300000, "3PH-Consumer_meter": 100000, "LTCT-Consumer_meter": 0, "HTCT-Consumer_meter": 0, "total": 400000 }
    }
  ]
}
```

**Response (category=feeder)** — `MIvsSATvsInvoiceSummaryOut`

```json
{
  "summary": {
    "total_mi": 500000,
    "total_sat": 350000,
    "total_lumpsum_invoice": 300000,
    "total_pmpm_invoice": 300000
  },
  "comparison": [
    {
      "label": "KASHI",
      "total_mi": 100000,
      "total_sat": 100000,
      "total_lumpsum_invoice": 50000,
      "total_pmpm_invoice": 50000
    }
  ]
}
```

**Frontend Usage**

- **Funnel metrics**: Use `summary` object. Each key (`total_mi`, etc.) contains category-aware sub-keys for stacked series grouping.
- **Comparison chart**: Bar chart with `label` on X-axis. Group by `label`, each item mirrors the `summary` format.

---

### KPI 12 — Revenue Realized Summary

Aggregates preloaded counts from `sql_revenue_realized` for **lumpsum / PMPM invoice and collection** (four headline metrics). Response shape matches **KPI 10** (`summary` + `comparison` only).

**Metrics** (each value is a count / total from the MI SQL pipeline, not a currency amount):

| Field | Meaning |
| :--- | :--- |
| `total_lumpsum_invoice` | Sum of lumpsum invoice counts in scope |
| `total_pmpm_invoice` | Sum of PMPM invoice counts in scope |
| `total_lumpsum_collection` | Sum of lumpsum collection counts in scope |
| `total_pmpm_collection` | Sum of PMPM collection counts in scope |

#### `GET /api/mi/revenue-realized/summary`

**Parameters**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `category` | `string` | `total` / `all` (default), `consumer`, `feeder`, or `dt`. Controls which `meter_category` rows are included and how the four metrics are shaped in `summary` / `comparison` (nested vs flat; same rules as KPI 10 meter funnel). |
| `duration` | `string` | Optional. Filters `period_type`: `daily` / `weekly` / `monthly`. If omitted, **all** period types are included (`all`). |
| `level` | `string` | Hierarchy level for comparison: `discom` / `zone` / `circle` / `division` / `subdivision` / `substation` / `feeder` / `dtr` (default: `discom`) |
| `project` | `string` | Project filter: `all` or specific project |
| `meter_category` | `string` | Optional dimensional filter (standard MI column); distinct from `category` above |
| `start_date` / `end_date` | `string` | Passed through filters where applicable (repository may not narrow KPI 12 by these; confirm with backend if you rely on date slicing) |
| Plus all standard geographical filters |

**Behavior Notes**

- **`category=total` (default)**: Each of the four metrics in `summary` and each `comparison` row is a nested object: keys `CONSUMER`, `FEEDER`, `DT`, and `total` (sums only rows mapped to those buckets).
- **`category=consumer`**: Each metric is nested by consumer meter-type buckets (`1PH-Consumer_meter`, `3PH-Consumer_meter`, `LTCT-Consumer_meter`, `HTCT-Consumer_meter`, `total`) — same bucketing as KPI 10 / KPI 11 consumer mode.
- **`category=feeder` or `category=dt`**: Each metric is a **plain integer** (only that `meter_category` slice).
- **Comparison**: One object per cluster; `label` follows the same project / `level` convention as other MI comparison endpoints. Each row repeats the same four keys with the same nesting rules as `summary`.
- **Removed** (breaking vs older docs): `category_breakdown`, `period_breakdown`, top-level-only totals, and `comparison[].count` wrappers.

**Response** — `RevenueRealizedSummaryOut`

**Response (`category=total` or omitted)** — nested by `CONSUMER` / `FEEDER` / `DT` / `total`

```json
{
  "summary": {
    "total_lumpsum_invoice": { "CONSUMER": 600000, "FEEDER": 80000, "DT": 70517, "total": 750517 },
    "total_pmpm_invoice": { "CONSUMER": 600000, "FEEDER": 80000, "DT": 70517, "total": 750517 },
    "total_lumpsum_collection": { "CONSUMER": 350000, "FEEDER": 50000, "DT": 66001, "total": 466001 },
    "total_pmpm_collection": { "CONSUMER": 480000, "FEEDER": 65000, "DT": 76264, "total": 621264 }
  },
  "comparison": [
    {
      "label": "AGRA",
      "total_lumpsum_invoice": { "CONSUMER": 250000, "FEEDER": 30000, "DT": 20000, "total": 300000 },
      "total_pmpm_invoice": { "CONSUMER": 250000, "FEEDER": 30000, "DT": 20000, "total": 300000 },
      "total_lumpsum_collection": { "CONSUMER": 150000, "FEEDER": 20000, "DT": 18000, "total": 188000 },
      "total_pmpm_collection": { "CONSUMER": 200000, "FEEDER": 25000, "DT": 22000, "total": 247000 }
    }
  ]
}
```

**Response (`category=consumer`)** — nested by consumer meter-type + `total`

```json
{
  "summary": {
    "total_lumpsum_invoice": { "1PH-Consumer_meter": 500000, "3PH-Consumer_meter": 80000, "LTCT-Consumer_meter": 15000, "HTCT-Consumer_meter": 5000, "total": 600000 },
    "total_pmpm_invoice": { "1PH-Consumer_meter": 500000, "3PH-Consumer_meter": 80000, "LTCT-Consumer_meter": 15000, "HTCT-Consumer_meter": 5000, "total": 600000 },
    "total_lumpsum_collection": { "1PH-Consumer_meter": 290000, "3PH-Consumer_meter": 45000, "LTCT-Consumer_meter": 10000, "HTCT-Consumer_meter": 5000, "total": 350000 },
    "total_pmpm_collection": { "1PH-Consumer_meter": 400000, "3PH-Consumer_meter": 60000, "LTCT-Consumer_meter": 12000, "HTCT-Consumer_meter": 8000, "total": 480000 }
  },
  "comparison": [
    {
      "label": "KASHI",
      "total_lumpsum_invoice": { "1PH-Consumer_meter": 180000, "3PH-Consumer_meter": 30000, "LTCT-Consumer_meter": 5000, "HTCT-Consumer_meter": 2000, "total": 217000 },
      "total_pmpm_invoice": { "1PH-Consumer_meter": 180000, "3PH-Consumer_meter": 30000, "LTCT-Consumer_meter": 5000, "HTCT-Consumer_meter": 2000, "total": 217000 },
      "total_lumpsum_collection": { "1PH-Consumer_meter": 100000, "3PH-Consumer_meter": 18000, "LTCT-Consumer_meter": 3000, "HTCT-Consumer_meter": 1000, "total": 122000 },
      "total_pmpm_collection": { "1PH-Consumer_meter": 140000, "3PH-Consumer_meter": 25000, "LTCT-Consumer_meter": 4000, "HTCT-Consumer_meter": 3000, "total": 172000 }
    }
  ]
}
```

**Response (`category=feeder` or `category=dt`)** — flat integers

```json
{
  "summary": {
    "total_lumpsum_invoice": 80000,
    "total_pmpm_invoice": 80000,
    "total_lumpsum_collection": 50000,
    "total_pmpm_collection": 65000
  },
  "comparison": [
    {
      "label": "AGRA",
      "total_lumpsum_invoice": 30000,
      "total_pmpm_invoice": 30000,
      "total_lumpsum_collection": 20000,
      "total_pmpm_collection": 25000
    }
  ]
}
```

**Frontend usage**

- Read the four metrics from `summary`; for charts, use nested sub-keys when values are objects, or a single bar per metric when values are numbers (`feeder` / `dt`).
- Comparison bars: same structure per `label` as `summary`.

---

### KPI 13 — Revenue Ageing Summary

Tracks aging of revenue collection after SAT. The response matches **KPI 6 (Stock Ageing)** at the top level: **`summary`** plus **`comparison`** only. There is **no** per-period time series on this route (use other data sources if you need a trend over `period_value`).

#### `GET /api/mi/revenue-ageing/summary`

**Parameters**: All geographical + category filters, `project`, `level`, `duration` (default: `monthly`), optional `meter_category` or `category` (`consumer` / `feeder` / `dt` / `total` / `all`), `start_date`, `end_date`.

**Behavior Notes**

- **`summary`**: Keys `age_0_30`, `age_31_60`, `age_61_90`, `age_90_plus`, and `total_pending` (sum across the four buckets).
  - **`category=consumer`** (or equivalent `meter_category`): Each `age_*` is an object with canonical consumer keys `1PH-Consumer_meter`, `3PH-Consumer_meter`, `LTCT-Consumer_meter`, `HTCT-Consumer_meter`, and `total` (same mapping from raw `new_meter_type` as KPI 6).
  - **`category=total`**, **`all`**, or **omitted** (no category filter): Each `age_*` is an object with `CONSUMER`, `FEEDER`, `DT`, and `total`. Rows whose `meter_category` is not one of those three are omitted from the nested keys (same rule as KPI 6).
  - **`category=feeder`** or **`dt`**: Each `age_*` is a **number** (flat aggregate for that filter).
- **`comparison`**: One object per cluster (`label`). Each row repeats the same nesting rules as `summary` for the four age fields, plus `total_pending`.

**Response** — `RevenueAgeingSummaryOut`

Example when `category=consumer`:

```json
{
  "summary": {
    "age_0_30": {
      "1PH-Consumer_meter": 400,
      "3PH-Consumer_meter": 80,
      "LTCT-Consumer_meter": 10,
      "HTCT-Consumer_meter": 10,
      "total": 500
    },
    "age_31_60": {
      "1PH-Consumer_meter": 250,
      "3PH-Consumer_meter": 40,
      "LTCT-Consumer_meter": 5,
      "HTCT-Consumer_meter": 5,
      "total": 300
    },
    "age_61_90": {
      "1PH-Consumer_meter": 100,
      "3PH-Consumer_meter": 30,
      "LTCT-Consumer_meter": 10,
      "HTCT-Consumer_meter": 10,
      "total": 150
    },
    "age_90_plus": {
      "1PH-Consumer_meter": 1500,
      "3PH-Consumer_meter": 300,
      "LTCT-Consumer_meter": 100,
      "HTCT-Consumer_meter": 100,
      "total": 2000
    },
    "total_pending": 2950
  },
  "comparison": [
    {
      "label": "AGRA",
      "age_0_30": {
        "1PH-Consumer_meter": 120,
        "3PH-Consumer_meter": 30,
        "LTCT-Consumer_meter": 0,
        "HTCT-Consumer_meter": 0,
        "total": 150
      },
      "age_31_60": {
        "1PH-Consumer_meter": 70,
        "3PH-Consumer_meter": 15,
        "LTCT-Consumer_meter": 3,
        "HTCT-Consumer_meter": 2,
        "total": 90
      },
      "age_61_90": {
        "1PH-Consumer_meter": 40,
        "3PH-Consumer_meter": 5,
        "LTCT-Consumer_meter": 3,
        "HTCT-Consumer_meter": 2,
        "total": 50
      },
      "age_90_plus": {
        "1PH-Consumer_meter": 600,
        "3PH-Consumer_meter": 150,
        "LTCT-Consumer_meter": 25,
        "HTCT-Consumer_meter": 25,
        "total": 800
      },
      "total_pending": 1090
    }
  ]
}
```

**Frontend usage**

- Read metrics from `summary`; mirror the same structure for each `comparison` row (check whether each `age_*` is a number or a nested object from the active `category` mode).
- This endpoint does not return `period_breakdown`; time-series charts require another contract or endpoint.

---

### KPI 14 — Defective Meters Summary

Tracks defective meters based on complaint data, focusing on **replaced meters only**.

#### `GET /api/mi/defective-meters/summary`

**Parameters**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `duration` | `string` | Aggregation granularity: `daily` / `weekly` / `monthly` (default: `daily`) |
| `level` | `string` | Hierarchy level for comparison: `project`, `discom`, `zone`, `circle`, `division`, `subdivision` (default: `discom`) |
| `project` | `string` | Project filter: `all` or specific project (default: `all`) |
| `meter_category` | `string` | Optional filter: `consumer`, `feeder`, or `dt` |
| `start_date` / `end_date` | `string` | Date range filter (`YYYY-MM-DD`) |
| Plus all standard geographical filters |

**Behavior Notes**

- **Data source**: `unified_complaints` table, filtered to records where **both** `old_smart_meter_number` and `new_smart_meter_number` are present.
- **Complaint categorization**:
  - `Meter Burnt`: "Meter Terminal Burnt", "Meter burnt", "Meter Sparking or Sparking at Meter terminal"
  - `Meter Faulty`: "Meter faulty or not working"
  - `Others`: all other complaint types
- **Trend chart**: Time-series with counts per period for each meter category and defective type.
- **Comparison chart**: Standard label rules from KPI 1.

**Response** — `DefectiveMetersSummaryOut`

```json
{
  "summary": {
    "total_defective": {
      "1PH-Consumer_meter": 200,
      "3PH-Consumer_meter": 50,
      "LTCT-Consumer_meter": 5,
      "HTCT-Consumer_meter": 0,
      "total": 255
    },
    "total_burnt": {
      "1PH-Consumer_meter": 80,
      "3PH-Consumer_meter": 20,
      "LTCT-Consumer_meter": 2,
      "HTCT-Consumer_meter": 0,
      "total": 102
    },
    "total_faulty": {
      "1PH-Consumer_meter": 40,
      "3PH-Consumer_meter": 10,
      "LTCT-Consumer_meter": 1,
      "HTCT-Consumer_meter": 0,
      "total": 51
    },
    "total_others": {
      "1PH-Consumer_meter": 80,
      "3PH-Consumer_meter": 20,
      "LTCT-Consumer_meter": 2,
      "HTCT-Consumer_meter": 0,
      "total": 102
    }
  },
  "period_breakdown": [
    {
      "period_value": "2026-04-16",
      "total_defective": {
        "1PH-Consumer_meter": 50,
        "3PH-Consumer_meter": 10,
        "LTCT-Consumer_meter": 1,
        "HTCT-Consumer_meter": 0,
        "total": 61
      },
      "total_burnt": {
        "1PH-Consumer_meter": 20,
        "3PH-Consumer_meter": 4,
        "LTCT-Consumer_meter": 0,
        "HTCT-Consumer_meter": 0,
        "total": 24
      },
      "total_faulty": {
        "1PH-Consumer_meter": 10,
        "3PH-Consumer_meter": 2,
        "LTCT-Consumer_meter": 0,
        "HTCT-Consumer_meter": 0,
        "total": 12
      },
      "total_others": {
        "1PH-Consumer_meter": 20,
        "3PH-Consumer_meter": 4,
        "LTCT-Consumer_meter": 1,
        "HTCT-Consumer_meter": 0,
        "total": 25
      }
    }
  ],
  "comparison": [
    {
      "label": "AGRA",
      "total_defective": {
        "1PH-Consumer_meter": 100,
        "3PH-Consumer_meter": 25,
        "LTCT-Consumer_meter": 2,
        "HTCT-Consumer_meter": 0,
        "total": 127
      },
      "total_burnt": {
        "1PH-Consumer_meter": 40,
        "3PH-Consumer_meter": 10,
        "LTCT-Consumer_meter": 1,
        "HTCT-Consumer_meter": 0,
        "total": 51
      },
      "total_faulty": {
        "1PH-Consumer_meter": 20,
        "3PH-Consumer_meter": 5,
        "LTCT-Consumer_meter": 0,
        "HTCT-Consumer_meter": 0,
        "total": 25
      },
      "total_others": {
        "1PH-Consumer_meter": 40,
        "3PH-Consumer_meter": 10,
        "LTCT-Consumer_meter": 1,
        "HTCT-Consumer_meter": 0,
        "total": 51
      }
    }
  ]
}
```

**Frontend Usage**

- **Summary cards**: Use `total_defective`, `total_burnt`, `total_faulty`, `total_others`.
- **Trend chart**: Line chart with `period_value` on X-axis.
- **Comparison chart**: Bar chart with `label` on X-axis.
- **Category breakdown**: Nested pie/bar charts.

---

### SAT Dashboard

Regional SAT metrics: stage-wise snapshot (`satBlueData`), monthly throughput (`raw`), and optional combined payload. Preferred split for new clients is **`sat-dash`**; **`command-center`** remains for a single full response.

#### `GET /api/mi/sat-dash/satBlueData`

Returns SAT stage cards for **all** projects in one object.

**Response**: JSON object with keys `kashi`, `agra`, `triveni` (lowercase, fixed order in payload). Each value is an **array** of eight stage rows with the same shape as `satBlueData` in the command-center response. If there is no snapshot row for a project, that key’s value is `[]`.

Each stage row:

| Field | Type | Description |
| :--- | :--- | :--- |
| `stage` | string | `SAT-1` … `SAT-7`, then `SAT-9` for Agra or `SAT-8` for Kashi/Triveni |
| `installedBase` | int | Stage eligibility |
| `cumulativeSat` | int | Stage achievement |
| `efficiencyPct` | float | Throughput % (from ETL) |
| `startSAT` | string \| null | Milestone start date, `MM/DD/YYYY` |

#### `GET /api/mi/sat-dash/{region}`

**Path parameter**: `region` — one of `kashi`, `agra`, `triveni` (case-insensitive).

**Errors**: `400` if `region` is not allowed.

**Response**: JSON **array** at the root (monthly time series only — same as the `raw` field from command-center). Each element:

| Field | Type | Description |
| :--- | :--- | :--- |
| `month` | string | Period label from ETL |
| `received` | int | `inventory_added` |
| `installed` | int | `installed_added` |
| `sat` | object | `s1` … `s7` plus **`s9`** for Agra or **`s8`** for Kashi/Triveni |

#### `GET /api/mi/command-center/{region}`

**Path parameter**: `region` — one of `kashi`, `agra`, `triveni`.

**Response**: Full dashboard object: `inventory`, `installed`, `total_sat`, `total_invoice`, `region`, `satBlueData`, `raw`, `sat_milestones`. Equivalent to calling the two `sat-dash` responses for that region plus snapshot totals and milestones in one payload.

---

## Operations & Maintenance (O&M) KPIs

All O&M endpoints are under the prefix `/api/om`. They share these common parameters:

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `project` | `string` | Project name filter |
| `meter_category` | `string` | `CONSUMER` / `FEEDER` / `DT` |
| `om_category` | `string` | Legacy alias for `meter_category` (auto-mapped) |
| `start_date` / `end_date` | `string` | Date range filter |

Plus all geographical dimensions (`discom`, `zone`, `circle`, `division`, `subdivision`, `feeder`, `dtr`).

---

### O&M-1 — Team Productivity Dashboard

#### `GET /api/om/productivity-team/dashboard`

**Parameters**:
- `duration`: `daily`, `weekly`, `monthly`
- `project`: e.g. `all`, `agra`
- `level`: `discom`, `zone`, `circle`, `division`, `subdivision`
- `category`: `consumer`, `feeder`, `dt`, `total`
- `start_date`, `end_date`

**Formula**:
- **Daily Productivity**: `Closed Tickets (that day) / Distinct Active Technicians (that day)`
- **Weekly/Monthly Productivity**: `AVG(Daily Productivity)` computed across the active days in the period.
- If `technician` is missing for a closed ticket, the `supervisor` is used as a fallback.

**Response** — `OMTeamProductivityDashboardOut`

```json
{
  "summary": {
    "total_closed_tickets": 15000,
    "total_active_technicians": 25,
    "productivity_per_technician_per_day": 20.0
  },
  "insights": {
    "top_performing_technician": {
      "name": "VI2_Avdhesh kumar",
      "productivity_per_technician_per_day": 35.2
    },
    "lowest_performing_technician": {
      "name": "Tech Beta",
      "productivity_per_technician_per_day": 1.2
    }
  },
  "trend": [
    {
      "date": "2026-03-01",
      "total_closed_tickets": 500,
      "active_technicians": 5,
      "productivity_per_technician_per_day": 100.0
    }
  ],
  "comparison": [
    {
      "label": "AGRA",
      "total_closed_tickets": 5000,
      "active_technicians": 8,
      "productivity_per_technician_per_day": 20.83
    }
  ],
  "category_breakdown": {
    "CONSUMER": {
      "total_closed_tickets": 12000,
      "active_technicians": 20,
      "productivity_per_technician_per_day": 18.5
    },
    "FEEDER": {
      "total_closed_tickets": 2000,
      "active_technicians": 10,
      "productivity_per_technician_per_day": 12.0
    },
    "DT": {
      "total_closed_tickets": 1000,
      "active_technicians": 5,
      "productivity_per_technician_per_day": 8.0
    }
  }
}
```

---

### O&M-2 — Productivity Trend Dashboard

#### `GET /api/om/productivity-trend/dashboard`

Dashboard endpoint returning structured monthly productivity metrics. Uses the same underlying data as O&M-1.

**Parameters**:
- `duration`: Reserved (currently always monthly trend)
- `project`: e.g. `all`, `agra`
- `level`: `discom`, `zone`, `circle`, `division`, `subdivision`
- `category`: `consumer`, `feeder`, `dt`, `total`
- `start_date`, `end_date`
- Plus geo filters

**Metric Definitions**:
- **`avg_active_technicians`**: Average number of technicians who worked per day in that month
- **`productivity_per_technician_per_day`**: Average daily productivity per technician in that month
- **`avg_monthly_productivity_per_technician_per_day`**: Average number of tickets a technician closes per day, calculated over the selected date range

**Response** — `OMProductivityTrendDashboardOut`

```json
{
  "summary": {
    "total_closed_tickets": 150000,
    "total_active_months": 12,
    "avg_monthly_productivity_per_technician_per_day": 22.5
  },
  "trend": [
    {
      "month": "2025-01",
      "total_closed_tickets": 12000,
      "active_days": 26,
      "avg_active_technicians": 45,
      "productivity_per_technician_per_day": 10.25
    },
    {
      "month": "2025-02",
      "total_closed_tickets": 13500,
      "active_days": 24,
      "avg_active_technicians": 48,
      "productivity_per_technician_per_day": 11.72
    }
  ],
  "comparison": [
    {
      "label": "AGRA",
      "productivity_per_technician_per_day": 12.5
    },
    {
      "label": "KASHI",
      "productivity_per_technician_per_day": 11.2
    },
    {
      "label": "TRIVENI",
      "productivity_per_technician_per_day": 10.8
    }
  ],
  "category_breakdown": {
    "CONSUMER": {
      "avg_monthly_productivity_per_technician_per_day": 18.2
    },
    "FEEDER": {
      "avg_monthly_productivity_per_technician_per_day": 9.5
    },
    "DT": {
      "avg_monthly_productivity_per_technician_per_day": 6.1
    }
  }
}
```

---

### O&M-3 — Open Ticket Ageing Dashboard

#### `GET /api/om/open-ageing/dashboard`

**Parameters**:
- `duration`: `daily`, `weekly`, `monthly` (used for trend grouping)
- `project`: e.g. `all`, `agra`
- `level`: `discom`, `zone`, `circle`, `division`, `subdivision`
- `category`: `consumer`, `feeder`, `dt`, `total`
- `start_date`, `end_date`
- Plus geo filters

**Response** — `OMOpenAgeingDashboardOut`

```json
{
  "summary": {
    "total": 100,
    "auto_ticketing": 40,
    "1912_helpdesk": 30,
    "others": 30,
    "age_buckets": {
      "age_less_than_3_days": {
        "total": 10,
        "auto_ticketing": 4,
        "1912_helpdesk": 3,
        "others": 3
      },
      "age_less_than_7_days": {
        "total": 20,
        "auto_ticketing": 10,
        "1912_helpdesk": 5,
        "others": 5
      },
      "age_less_than_15_days": {
        "total": 15,
        "auto_ticketing": 6,
        "1912_helpdesk": 4,
        "others": 5
      },
      "age_less_than_30_days": {
        "total": 15,
        "auto_ticketing": 5,
        "1912_helpdesk": 5,
        "others": 5
      },
      "age_less_than_3_months": {
        "total": 20,
        "auto_ticketing": 10,
        "1912_helpdesk": 5,
        "others": 5
      },
      "age_less_than_6_months": {
        "total": 15,
        "auto_ticketing": 4,
        "1912_helpdesk": 6,
        "others": 5
      },
      "age_6_months_and_above": {
        "total": 5,
        "auto_ticketing": 1,
        "1912_helpdesk": 2,
        "others": 2
      }
    }
  },
  "trend": [
    {
      "period_value": "2024-08",
      "total": 50,
      "auto_ticketing": 20,
      "1912_helpdesk": 15,
      "others": 15
    }
  ],
  "comparison": [
    {
      "label": "AGRA",
      "total": 100,
      "auto_ticketing": 40,
      "1912_helpdesk": 30,
      "others": 30,
      "age_buckets": { "...": "..." }
    }
  ],
  "category_breakdown": {
    "CONSUMER": {
      "total": 100,
      "auto_ticketing": 40,
      "1912_helpdesk": 30,
      "others": 30,
      "age_buckets": { "...": "..." }
    }
  }
}
```

---

### O&M-4 — Average Closure Time Dashboard

#### `GET /api/om/avg-closure-time/dashboard`

**Parameters**:
- `duration`: `daily`, `weekly`, `monthly` (default: `monthly`)
- `project`: e.g. `all`, `agra`
- `level`: `discom`, `zone`, `circle`, `division`, `subdivision`
- `category`: `consumer`, `feeder`, `dt`, `total` (or `all`)
- `start_date`, `end_date`

**Response** — `OMAvgClosureTimeDashboardOut`

`category` controls the metric shape (KPI-9 pattern):

| `category` | `summary.total_closed_tickets` / `summary.avg_resolution_days` |
| :--- | :--- |
| `total` or `all` | Nested objects with keys `CONSUMER`, `FEEDER`, `DT`, `total` |
| `consumer` | Nested objects with keys `1PH-Consumer_meter`, `3PH-Consumer_meter`, `LTCT-Consumer_meter`, `HTCT-Consumer_meter`, `total` |
| `feeder` or `dt` | Flat scalars (`int` / `float`) |

For `total` / `consumer`, `category_breakdown` is returned as an empty object `{}`.

Example (`category=feeder` / flat):

```json
{
  "summary": {
    "total_closed_tickets": 15000,
    "avg_resolution_days": 2.5
  },
  "trend": [
    {
      "period_value": "2024-08",
      "total_closed_tickets": 1200,
      "avg_resolution_days": 2.8
    }
  ],
  "comparison": [
    {
      "label": "AGRA",
      "total_closed_tickets": 5000,
      "avg_resolution_days": 2.4
    }
  ],
  "category_breakdown": {
    "CONSUMER": {
      "total_closed_tickets": 12000,
      "avg_resolution_days": 2.6
    }
  }
}
```

Example (`category=total` / nested by meter_category):

```json
{
  "summary": {
    "total_closed_tickets": { "CONSUMER": 12000, "FEEDER": 2000, "DT": 1000, "total": 15000 },
    "avg_resolution_days": { "CONSUMER": 2.6, "FEEDER": 2.0, "DT": 1.8, "total": 2.5 }
  },
  "trend": [
    {
      "period_value": "2024-08",
      "total_closed_tickets": { "CONSUMER": 1000, "FEEDER": 120, "DT": 80, "total": 1200 },
      "avg_resolution_days": { "CONSUMER": 2.8, "FEEDER": 2.2, "DT": 2.0, "total": 2.7 }
    }
  ],
  "comparison": [
    {
      "label": "AGRA",
      "total_closed_tickets": { "CONSUMER": 4200, "FEEDER": 500, "DT": 300, "total": 5000 },
      "avg_resolution_days": { "CONSUMER": 2.4, "FEEDER": 2.1, "DT": 1.9, "total": 2.3 }
    }
  ],
  "category_breakdown": {}
}
```

---

### O&M-5 — Closed Ticket Analysis Dashboard (by Source)

#### `GET /api/om/closed-analysis/dashboard`

Closed-ticket dashboard split into exactly three buckets:
`auto_ticketing`, `1912_helpdesk`, `others`.

**Parameters**:
- `duration`: `daily`, `weekly`, `monthly` (used for trend grouping)
- `project`: e.g. `all`, `agra`
- `level`: `discom`, `zone`, `circle`, `division`, `subdivision`
- `category`: `consumer`, `feeder`, `dt`, `total`
- `start_date`, `end_date`
- Plus geo filters

**Response** — `OMClosedAnalysisDashboardOut`:

```json
{
  "summary": {
    "auto_ticketing": 40,
    "1912_helpdesk": 30,
    "others": 30
  },
  "trend": [
    {
      "period_value": "2024-08",
      "auto_ticketing": 20,
      "1912_helpdesk": 15,
      "others": 15
    }
  ],
  "comparison": [
    {
      "label": "AGRA",
      "auto_ticketing": 40,
      "1912_helpdesk": 30,
      "others": 30
    }
  ],
  "category_breakdown": {
    "CONSUMER": {
      "auto_ticketing": 40,
      "1912_helpdesk": 30,
      "others": 30
    }
  }
}
```

Notes:
- No total fields are returned (e.g. no `total_closed`, `total_closed_tickets`).
- No `age_buckets` are returned in any section.

---

## O&M — Average Ticket Closure Time Dashboard (O&M-4)

#### `GET /api/om/avg-closure-time/dashboard`

**Parameters**: `duration` (`daily` / `weekly` / `monthly`), `level`, `project`, `category`, `start_date` / `end_date`, plus geo filters (`discom`, `zone`, …).

**`category` response shape** (KPI-9 pattern):

| `category` | `summary` / each `trend[]` / each `comparison[]` |
| :--- | :--- |
| `total` or `all` | `total_closed_tickets` and `avg_resolution_days` are objects with keys `CONSUMER`, `FEEDER`, `DT`, `total` (weighted `avg_resolution_days` per bucket). |
| `consumer` | Same two fields nested by `1PH-Consumer_meter`, `3PH-Consumer_meter`, `LTCT-Consumer_meter`, `HTCT-Consumer_meter`, `total`. |
| `feeder` or `dt` | Flat integers: `total_closed_tickets`, `avg_resolution_days`. `category_breakdown` by raw `meter_category` is included. |

For `total` / `consumer`, `category_breakdown` is an empty object.

---

## Quick Reference for Frontend

| Pattern | When to Use | Example |
| :--- | :--- | :--- |
| `/endpoint/dashboard` or `/endpoint/summary` | Dashboard cards, charts, KPI tiles | `/api/mi/progress/dashboard?project=AGRA` |
| `category_breakdown` | Pie charts, grouped bar charts | Keys: `meter_category` → `new_meter_type` → values |
| `period_breakdown` / `trend` | Time-series line/area charts | Keys: `period_value` → values |
| `comparison` | Clustered bar charts | Array of `{ label, ...metrics }` |

### Common Comparison Label Rules

| Condition | Label Format | Example |
| :--- | :--- | :--- |
| `project=all` + `level=discom` | Project name | `AGRA`, `KASHI`, `TRIVENI` |
| `project=all` + `level=zone/circle/...` | `PROJECT \| level_value` | `AGRA \| AGRA I` |
| `project=AGRA` + `level=zone` | Raw level value | `AGRA I`, `AGRA II` |

### Date Format Notes

| Context | Format | Example |
| :--- | :--- | :--- |
| Query param `start_date` / `end_date` | `YYYY-MM-DD` | `2024-08-01` |
| Monthly `period_value` | `YYYY-MM` or `DD-MM-YY` | `2024-08` or `01-08-24` |
| Daily `period_value` | `DD-MM-YY` or `YYYY-MM-DD` | `01-08-24` |
| Weekly `period_value` | `YYYY-MM-DD` (Monday) | `2024-08-05` |
