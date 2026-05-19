# KPI Formulas & Calculation Logic

> **Version**: 1.0 &nbsp;|&nbsp; **Last Updated**: 2026-04-23  
> This document describes the exact formulas, data sources, aggregation methods, and special rules used to compute each KPI in the Smart Meter system.

---

## Table of Contents

1. [Shared Logic](#shared-logic)
2. [MI KPIs](#mi-kpis)
   - [KPI 1 — MI Progress Dashboard](#kpi-1--mi-progress-dashboard)
   - [KPI 2.5 — MI Productivity per Team Dashboard](#kpi-25--mi-productivity-per-team-dashboard)
   - [KPI 3.5 — Monthly Productivity Trend Dashboard](#kpi-35--monthly-productivity-trend-dashboard)
   - [KPI 4 — Inventory Utilization Summary](#kpi-4--inventory-utilization-summary)
   - [KPI 5 — Pace vs Stock Summary](#kpi-5--pace-vs-stock-summary)
   - [KPI 6 — Stock Ageing Dashboard](#kpi-6--stock-ageing-dashboard)
   - [KPI 7 — MI vs SAT Summary](#kpi-7--mi-vs-sat-summary)
   - [KPI 8 — Non-SAT Ageing Dashboard](#kpi-8--non-sat-ageing-dashboard)
   - [KPI 9 — Meter Journey Dashboard](#kpi-9--meter-journey-dashboard)
   - [KPI 10 — Meter Funnel Summary](#kpi-10--meter-funnel-summary)
   - [KPI 11 — MI vs SAT vs Invoice Summary](#kpi-11--mi-vs-sat-vs-invoice-summary)
   - [KPI 12 — Revenue Realized Summary](#kpi-12--revenue-realized-summary)
   - [KPI 13 — Revenue Ageing Summary](#kpi-13--revenue-ageing-summary)
   - [KPI 14 — Defective Meters Summary](#kpi-14--defective-meters-summary)
   - [SAT Dashboard](#sat-dashboard)
3. [O&M KPIs](#om-kpis)
   - [O&M-1 — Team Productivity Dashboard](#om-1--team-productivity-dashboard)
   - [O&M-2 — Productivity Trend Dashboard](#om-2--productivity-trend-dashboard)
   - [O&M-3 — Open Ticket Ageing Dashboard](#om-3--open-ticket-ageing-dashboard)
   - [O&M-4 — Average Closure Time Dashboard](#om-4--average-closure-time-dashboard)
4. [Quick Reference Table](#quick-reference-table)

---

## Shared Logic

These rules apply across all dashboard endpoints.

### Comparison Label Derivation

All dashboard endpoints that return a `comparison` array use the same labeling rules based on the `project` and `level` query parameters:

| Condition | Label Expression |
| :--- | :--- |
| `project=all` AND `level=discom` | `UPPER(TRIM(project))` — yields project names: `AGRA`, `KASHI`, `TRIVENI` |
| `project=all` AND `level` is zone/circle/division/subdivision | `UPPER(TRIM(project)) || ' \| ' || COALESCE(level_column, 'Unknown')` |
| Single project (e.g. `project=AGRA`) | `COALESCE(level_column, 'Unknown')` — raw geographic value, no prefix |

Invalid `level` values fall back to `discom`. Rows where the chosen level column is `NULL` are excluded from the comparison array.

### Date Parsing (`_period_value_as_date`)

The stored `period_value` column uses different formats depending on `period_type`. The system parses them as follows:

| Period Type | Stored Format | SQL Conversion |
| :--- | :--- | :--- |
| `monthly` (length = 7) | `YYYY-MM` | `to_date(period_value \|\| '-01', 'YYYY-MM-DD')` |
| `monthly` (length != 7) | `DD-MM-YY` | `to_date(period_value, 'DD-MM-YY')` |
| `daily` / `weekly` / others | `DD-MM-YY` | `to_date(period_value, 'DD-MM-YY')` |

Query parameters `start_date` / `end_date` are always in `YYYY-MM-DD` format and compared against the parsed date.

### Standard Filter Application

All dimension filters (`discom`, `zone`, `circle`, `division`, `subdivision`, `substation`, `feeder`, `dtr`, `meter_category`, `new_meter_type`, `project`) are applied as **case-insensitive substring matches** using PostgreSQL `ILIKE`.

### Default Project Set

When `project=all`, the system restricts to the three known projects: **AGRA**, **KASHI**, **TRIVENI** (via `UPPER(TRIM(project)) IN ('AGRA', 'KASHI', 'TRIVENI')`).

---

## MI KPIs

---

### KPI 1 — MI Progress Dashboard

**Endpoint**: `GET /api/mi/progress/dashboard`  
**Data Source**: `sql_mi_progress` table  
**Repository Method**: `get_mi_progress_dashboard`

#### Metrics

| Field | Formula |
| :--- | :--- |
| `total_progress` | `SUM(total_mi_progress)` over all filtered rows |
| `trend[]` | Per `period_value`: `total` and dynamic category-aware sub-keys (e.g. `CONSUMER`, `1PH-Consumer_meter`) |
| `comparison[]` | Per label: `total` and dynamic category-aware sub-keys |

#### Aggregation

- All aggregates are **plain `SUM`** — no rates or averages.
- Filtered by `period_type = duration` (daily/weekly/monthly, default `daily`).
- `category=total` includes all three categories; otherwise filters to the specified one.

#### Date Filtering

Uses `_period_value_as_date(MIProgress, duration)` for `start_date` / `end_date` range comparison.

---

### KPI 2.5 — MI Productivity per Team Dashboard

**Endpoint**: `GET /api/mi/productivity/team/dashboard`  
**Data Source**: `sql_mi_technician_productivity` table  
**Repository Method**: `get_productivity_team_dashboard`

#### Core Formula (Avg-of-Daily)

```
Step 1 — Per calendar day (installation_date):
    daily_prod = SUM(total_installations) / COUNT(DISTINCT technician)

Step 2 — Summary productivity:
    productivity_per_technician_per_day = AVG(daily_prod) across all days in range
```

This is **NOT** `total_installations / total_technicians` over the whole range. It is the **mean of per-day ratios**, giving equal weight to each day regardless of volume.

#### Metrics

| Field | Formula |
| :--- | :--- |
| `summary.total_installations` | `SUM(total_installations)` across all filtered rows |
| `summary.total_active_technicians` | `COUNT(DISTINCT technician)` across entire filtered range |
| `summary.total_active_days` | Count of distinct `installation_date` values with data |
| `summary.productivity_per_technician_per_day` | `AVG(daily_prod)` |
| `trend[].productivity_per_technician_per_day` | `AVG(daily_prod)` within each duration bucket |
| `trend[].active_technicians` | `COUNT(DISTINCT technician)` within the bucket |
| `comparison[].productivity_per_technician_per_day` | `AVG(daily_prod)` per comparison label |
| `insights.top_performing_technician` | Technician with highest `AVG(daily total installations)` |
| `insights.lowest_performing_technician` | Technician with lowest `AVG(daily total installations)` |

#### Duration Bucketing

| Duration | Bucket Expression |
| :--- | :--- |
| `daily` | `to_char(installation_date, 'YYYY-MM-DD')` |
| `weekly` | `to_char(date_trunc('week', installation_date), 'YYYY-MM-DD')` |
| `monthly` | `to_char(installation_date, 'YYYY-MM')` |

#### Special Rules

- **Verified installations only**: Only rows where `sat_no IS NOT NULL` and non-empty are included.
- **Date filtering**: Applies on `installation_date` (a DATE column), not `period_value`.

---

### KPI 3.5 — Monthly Productivity Trend Dashboard

**Endpoint**: `GET /api/mi/productivity/trend/dashboard`  
**Data Source**: `sql_mi_technician_productivity` table (same as KPI 2.5)  
**Repository Method**: `get_productivity_trend_dashboard`

#### Differences from KPI 2.5

| Aspect | KPI 2.5 | KPI 3.5 |
| :--- | :--- | :--- |
| Default `duration` | `daily` | `monthly` |
| Summary metric name | `productivity_per_technician_per_day` | `productivity_per_technician_per_day` |
| Summary extra field | `total_active_days` | `total_active_months` = `COUNT(DISTINCT YYYY-MM)` |
| Trend key name | `date` | `month` |
| Trend extra fields | — | `active_days`, `avg_active_technicians` = `AVG(daily distinct technicians)` |

#### Formula

Same avg-of-daily logic as KPI 2.5:

```
daily_prod = SUM(total_installations) / COUNT(DISTINCT technician)   [per day]
bucket_productivity = AVG(daily_prod)                                 [per bucket]
```

---

### KPI 4 — Inventory Utilization Summary

**Endpoint**: `GET /api/mi/inventory-utilization/summary`  
**Data Source**: `sql_inventory_utilization` table  
**Repository Method**: `get_inventory_utilization_summary`

#### Metrics

| Field | Formula |
| :--- | :--- |
| `total_inventory` | `SUM(total_inventory)` |
| `total_installed` | `SUM(total_installed)` |
| `remaining_stock` | `SUM(remaining_stock)` from table |
| `utilization_rate_pct` | `ROUND(total_installed / total_inventory * 100, 2)` if `total_inventory > 0`, else `0` |

#### Breakdown & Comparison Computation

Each item in `period_breakdown` and `comparison` has:

```
utilization_rate_pct = ROUND(total_installed / total_inventory * 100, 2)
                       if total_inventory > 0, else 0
```

Nested within each period/comparison row are dynamic category-aware objects (e.g., `CONSUMER`, `1PH-Consumer_meter`), each tracking its own `inventory`, `installed`, and computed `utilization_rate_pct`.

#### Filtered by

- `period_type = duration` (daily/weekly/monthly, default `daily`).
- Date filtering via `_period_value_as_date`.

---

### KPI 5 — Pace vs Stock Summary

**Endpoint**: `GET /api/mi/pace-vs-stock/summary`  
**Data Source**: `sql_inventory_utilization` table (same as KPI 4)  
**Repository Method**: `get_pace_vs_stock_summary` → delegates to `get_inventory_utilization_summary` with `is_pace_vs_stock=True`

#### Difference from KPI 4

The **only** difference is the `is_pace_vs_stock` flag, which changes how breakdown nodes are computed:

| Context | KPI 4 (Utilization) | KPI 5 (Pace vs Stock) |
| :--- | :--- | :--- |
| Breakdown leaf metric | `utilization_rate_pct = ROUND(inst/inv*100, 2)` | `remaining_stock = MAX(0, inventory - installed)` |
| Comparison item metric | `utilization_rate_pct` | `remaining_stock` |
| Top-level fields | Both have `utilization_rate_pct` AND `remaining_stock` | Same |

The route sets `filters["is_pace_vs_stock"] = True` before calling the shared method.

---

### KPI 6 — Stock Ageing Dashboard

**Endpoint**: `GET /api/mi/stock-ageing/dashboard`  
**Data Source**: `sql_stock_ageing` table  
**Repository Method**: `get_stock_ageing_dashboard`

#### Ageing Buckets

| Bucket | Column |
| :--- | :--- |
| 0–30 days | `age_0_30` |
| 31–60 days | `age_31_60` |
| 61–90 days | `age_61_90` |
| 90+ days | `age_90_plus` |

All buckets are pre-computed in the ETL and stored as integer columns. The API aggregates them via `SUM`.

#### Metrics

| Field | Formula |
| :--- | :--- |
| `total_stock` | `SUM(age_0_30 + age_31_60 + age_61_90 + age_90_plus)` |
| `summary.age_*` | Object with age buckets. Each bucket contains dynamic category-aware keys (e.g., `CONSUMER`, `1PH-Consumer_meter`) |
| `comparison[].age_*` | Same structure as `summary`, grouped by label |

#### Filtered by

- `period_type = duration` (daily/weekly/monthly, default `monthly`).
- Date filtering via `_period_value_as_date(StockAgeing, duration)`.

---

### KPI 7 — MI vs SAT Summary

**Endpoint**: `GET /api/mi/mi-vs-sat/summary`  
**Data Source**: `sql_mi_vs_sat` table  
**Repository Method**: `get_mi_vs_sat_summary`

#### Metrics

| Field | Formula |
| :--- | :--- |
| `total_mi` | `SUM(total_mi)` |
| `total_sat` | `SUM(total_sat)` |
| `sat_progress_pct` | `ROUND(total_sat / total_mi * 100, 2)` if `total_mi > 0`, else `0` |
| `summary.sat_*` | Object mapping each SAT stage (`sat_1` to `sat_9`) to category-aware sub-keys |
| `comparison[]` | Each entry has `total_mi`, `total_sat`, `sat_progress_pct`, and the same `sat_*` category breakdowns as `summary` |

---

### KPI 8 — Non-SAT Ageing Dashboard

**Endpoint**: `GET /api/mi/non-sat-ageing/dashboard`  
**Data Source**: `sql_non_sat_ageing` table (row-level data with `meter_serial_number`, `installation_date`, `ageing_days`)  
**Repository Method**: `get_non_sat_ageing_dashboard`

#### Ageing Buckets

Computed via `SUM(CASE WHEN ... THEN 1 ELSE 0 END)` on the `ageing_days` column:

| Bucket | Condition |
| :--- | :--- |
| `age_0_30` | `ageing_days <= 30` |
| `age_31_60` | `ageing_days > 30 AND ageing_days <= 60` |
| `age_61_90` | `ageing_days > 60 AND ageing_days <= 90` |
| `age_91_120` | `ageing_days > 90 AND ageing_days <= 120` |
| `age_120_plus` | `ageing_days > 120` |

#### Metrics

| Field | Formula |
| :--- | :--- |
| `total_non_sat` | `COUNT(*)` of all filtered rows |
| `summary.age_*` | Object containing age buckets (`age_0_30`, etc.), each with category-aware sub-keys (e.g. `CONSUMER` or `1PH-Consumer_meter`) |
| `comparison[].age_*` | Same structure as `summary`, grouped by label |

#### Date Filtering

Applied on `installation_date` (not `period_value`).

---

### KPI 9 — Meter Journey Dashboard

**Endpoint**: `GET /api/mi/meter-journey/dashboard`  
**Data Source**: `sql_meter_journey_avg_time` table (pre-aggregated by ETL at geography x meter_type x meter_category x period grain)  
**Repository Method**: `get_meter_journey_dashboard`

#### Stage Definitions (ETL Level)

| Stage | Date Span |
| :--- | :--- |
| `inventory_to_store` | `gmrtoagencyts::date - didate::date` |
| `store_to_agency` | `agencytosupts::date - gmrtoagencyts::date` |
| `agency_to_meter_installation` | `installedts::date - agencytosupts::date` |
| `meter_installation_to_sat` | `sat_date::date - installedts::date` |
| `sat_to_invoice` | `pmpm_invoice_date::date - sat_date::date` |
| `invoice_to_revenue` | `pmpm_collection_date::date - pmpm_invoice_date::date` |
| `total_journey` | `pmpm_collection_date::date - didate::date` |

Only meters that have **completed PMPM revenue** (`pmpm_collection_date IS NOT NULL`) are included in the cohort.

#### Weighted Average Formula

Each row in the pre-aggregated table has a `stage_avg` and `meter_count`. The dashboard computes a **weighted average** across rows:

```
For each stage column:
    numerator   = SUM(CASE WHEN stage IS NOT NULL THEN stage * meter_count ELSE 0 END)
    denominator = SUM(CASE WHEN stage IS NOT NULL THEN meter_count ELSE 0 END)
    weighted_avg = numerator / NULLIF(denominator, 0)
```

#### Display Rounding

All stage averages in the JSON response are **rounded up to whole days**:

```python
displayed_value = int(math.ceil(float(weighted_avg)))
# Examples: 23.01 -> 24,  23.99 -> 24,  23.0 -> 23
```

#### Metrics

| Field | Formula |
| :--- | :--- |
| `summary.*` | Weighted average per stage across all matching rows |
| `summary.meter_count` | `COALESCE(SUM(meter_count), 0)` |
| `trend[].period_value` | Per period bucket: weighted averages + `meter_count` |
| `comparison[].label` | Per cluster: weighted averages + `meter_count` |

#### Duration Normalization

`as_on` and `latest_sat` aliases are normalized to `daily`. Filter: `period_type = normalized_duration`.

---

### KPI 10 — Meter Funnel Summary

**Endpoint**: `GET /api/mi/meter-stage`  
**Data Source**: `sql_meter_current_stage` table  
**Repository Method**: `get_meter_stage_dashboard`

#### Metric Definitions

| Metric | Condition (at meter level in ETL) |
| :--- | :--- |
| `inventory` | Total meters (all rows) |
| `installed` | `mi_date IS NOT NULL` AND `sat_no` is not empty |
| `sat_done` | `sat_date IS NOT NULL` |
| `revenue_collected` | `pmpm_collection_date IS NOT NULL` |

#### Aggregation

```
SUM(inventory), SUM(installed), SUM(sat_done), SUM(revenue_collected)
```

No conversion rates or percentages are computed in this endpoint.

#### Special Notes

- No time dimension — this is a **snapshot** table with no `period_type` / `period_value`.
- `start_date` / `end_date` are not applicable.
- `limit` / `offset` are accepted but ignored.

---

### KPI 11 — MI vs SAT vs Invoice Summary

**Endpoint**: `GET /api/mi/mi-vs-sat-vs-invoice/summary`  
**Data Source**: `sql_mi_sat_invoice` table  
**Repository Method**: `get_mi_sat_invoice_summary`

#### Metrics

| Field | Formula |
| :--- | :--- |
| `total_mi` | `SUM(total_mi)` across category rows |
| `total_sat` | `SUM(total_sat)` |
| `total_lumpsum_invoice` | `SUM(total_lumpsum_invoice)` |
| `total_pmpm_invoice` | `SUM(total_pmpm_invoice)` |
| `total_invoice` | `total_lumpsum_invoice + total_pmpm_invoice` (arithmetic sum; may exceed distinct meter count if a meter has both invoice types) |
| `summary.<metric>` | Each of the 4 key metrics above is an object with category-aware sub-keys |
| `comparison[].<metric>`| Same structure as `summary`, grouped by label |

#### Date Filtering

Uses `to_date(period_value, 'DD-MM-YY')` — not the `_period_value_as_date` monthly branch. The `duration` parameter is read but **not used** to filter `period_type`.

#### Period Key Normalization

Period keys in `period_breakdown` are rewritten from `DD-MM-YY` to `YYYY-MM-DD` format where parsing succeeds.

---

### KPI 12 — Revenue Realized Summary

**Endpoint**: `GET /api/mi/revenue-realized/summary`  
**Data Source**: `sql_revenue_realized` table  
**Repository Method**: `get_revenue_realized_summary`

#### Metrics

| Field | Formula |
| :--- | :--- |
| `total_lumpsum_invoice` | `SUM(total_lumpsum_invoice)` |
| `total_pmpm_invoice` | `SUM(total_pmpm_invoice)` |
| `total_lumpsum_collection` | `SUM(total_lumpsum_collection)` |
| `total_pmpm_collection` | `SUM(total_pmpm_collection)` |

#### Breakdown Keys

Value keys in `summary` and `comparison`: `total_lumpsum_invoice`, `total_pmpm_invoice`, `total_lumpsum_collection`, `total_pmpm_collection`. Each is nested with category-aware sub-keys (e.g., `CONSUMER`, `1PH-Consumer_meter`) based on filter.

#### Duration Handling

- Default `duration` = `all` → **no** `period_type` filter is applied (all period types included).
- If a specific duration is provided → `period_type = duration`.

#### Special Notes

No derived ratios (collection vs invoice percentage) are computed in this method.

---

### KPI 13 — Revenue Ageing Summary

**Endpoint**: `GET /api/mi/revenue-ageing/summary`  
**Data Source**: `sql_revenue_ageing` table  
**Repository Method**: `get_revenue_ageing_summary`

#### Ageing Buckets

| Bucket | Column |
| :--- | :--- |
| 0–30 days | `age_0_30` |
| 31–60 days | `age_31_60` |
| 61–90 days | `age_61_90` |
| 90+ days | `age_90_plus` |

#### Metrics

| Field | Formula |
| :--- | :--- |
| `summary.age_*` | Object containing age buckets (`age_0_30`, etc.), each with category-aware sub-keys (e.g. `CONSUMER` or `1PH-Consumer_meter`) |
| `summary.total_pending` | Sum of all age buckets |
| `comparison[]` | Same structure as `summary`, grouped by label |

#### Duration Handling

- Default `duration` = `as_on`; aliases `as`, `ason`, `snapshot` are mapped to `as_on`.
- Filter: `period_type = duration`.

#### Category Filter

`category` parameter maps `dtr` → `DT`. If no category is set, no forced CONSUMER/FEEDER/DT filter is applied.

---

### KPI 14 — Defective Meters Summary

**Endpoint**: `GET /api/mi/defective-meters/summary`  
**Data Source**: `sql_defective_meters` table (pre-aggregated from `unified_complaints`)  
**Repository Method**: `get_defective_meters_summary`

#### Complaint Classification

| Category | Matching `defective_type` Values |
| :--- | :--- |
| `meter_burnt` | "Meter Terminal Burnt", "Meter burnt", "Meter Sparking or Sparking at Meter terminal" |
| `meter_faulty` | "Meter faulty or not working" |
| `others` | All other complaint types |

#### Data Selection

Only complaints where **both** `old_smart_meter_number` and `new_smart_meter_number` are present (indicates meter replacement).

#### Metrics

| Field | Formula |
| :--- | :--- |
| `total_defective` | `SUM(burnt + faulty + others)` across all rows |
| `total_burnt` | `SUM(burnt)` |
| `total_faulty` | `SUM(faulty)` |
| `total_others` | `SUM(others)` |
| `summary.<metric>` | Each of the 4 top-level defect sums is an object with category-aware sub-keys |
| `period_breakdown[]` | Per `period_value`: Contains the same 4 metrics structured identically to `summary` |
| `comparison[]` | Same structure as `summary`, grouped by label |

#### Date Filtering

Uses `to_date(period_value, 'DD-MM-YY')` for `start_date` / `end_date` comparison. Filter: `period_type = duration` (default `monthly`).

---

### SAT Dashboard

**Endpoints** (same ETL sources for all):

| Endpoint | Returns |
| :--- | :--- |
| `GET /api/mi/sat-dash/satBlueData` | Object `kashi` / `agra` / `triveni` → each value is that project’s `satBlueData` array (empty array if no snapshot). |
| `GET /api/mi/sat-dash/{region}` | JSON array (root): monthly `raw` only for `kashi`, `agra`, or `triveni`. |
| `GET /api/mi/command-center/{region}` | Full combined payload: snapshot KPIs, `satBlueData`, `raw`, `sat_milestones` (backward compatible). |

**Data Sources**:
- `dashboard_command_center` — snapshot row per project
- `dashboard_command_center_trend` — monthly trend (`period_type = 'monthly'`)
- `dashboard_command_center_milestone` — SAT stage milestone dates

**Repository**: `get_sat_dash_sat_blue_data`, `get_sat_dash_region_monthly`, `get_command_center_dashboard` in `sqlalchemy_mi_repo.py`.

#### Snapshot Metrics

Read directly from the snapshot row: `inventory`, `installed`, `total_sat`, `total_invoice`. No formulas — values are loaded as-is from ETL.

#### SAT Stage Data (`satBlueData`)

For SAT stages 1–7:
- `installedBase` = `sat_n_eligibility`
- `cumulativeSat` = `sat_n_achievement`
- `efficiencyPct` = `sat_n_throughput_pct`

Last stage selection:
- **AGRA**: Uses `sat_9_*` columns (stage key `s9`)
- **KASHI / TRIVENI**: Uses `sat_8_*` columns (stage key `s8`)

#### Trend Data

Per month: `received` = `inventory_added`, `installed` = `installed_added`, SAT = sum of `s1_added` through `s7_added` plus `s9_added` (AGRA) or `s8_added`.

Monthly rows are returned in **chronological** order: the API orders by `to_date(trim(period_value), 'Mon-YY')` (ETL stores `Mon-YY` from `TO_CHAR`), with a `YYYY-MM` + `-01` branch when `length(trim(period_value)) = 7`, not by lexicographic `period_value`.

#### Milestones

Per stage: dates for `start`, `lumpsumInv`, `pmpInv`, `lumpsumCol`, `scCol` (formatted as `MM/DD/YYYY`).

Throughput percentages are stored as-is — no computation at the API layer.

---

## O&M KPIs

---

### O&M-1 — Team Productivity Dashboard

**Endpoint**: `GET /api/om/productivity-team/dashboard`  
**Data Source**: `sql_om_team_productivity_dashboard` table  
**Repository Method**: `get_productivity_team_dashboard`  
**Ultimate Source**: `unified_complaints` (ETL pre-aggregation)

#### ETL Pre-aggregation

```sql
SELECT
    UPPER(TRIM(project)),
    discom, zone, circle, division, sub_division,
    UPPER(TRIM(meter_category)),
    COALESCE(NULLIF(TRIM(technician), ''), supervisor) as technician,
    closed_date::date as closed_day,
    COUNT(*) as closed_tickets
FROM unified_complaints
WHERE closed_date IS NOT NULL
  AND COALESCE(NULLIF(TRIM(technician), ''), supervisor) IS NOT NULL
GROUP BY 1,2,3,4,5,6,7,8,9
```

Key: if `technician` is empty/whitespace, **`supervisor`** is used as fallback. Rows with both missing are excluded.

#### Core Formula (Avg-of-Daily)

```
Step 1 — Per calendar day (closed_day):
    daily_prod = SUM(closed_tickets) / COUNT(DISTINCT technician)

Step 2 — Summary:
    productivity_per_technician_per_day = AVG(daily_prod) across all days
    total_closed_tickets = SUM(closed_tickets)
    total_active_technicians = COUNT(DISTINCT technician) across entire range
```

This matches the MI KPI 2.5 approach: **mean of per-day ratios**, not a single ratio over the full range.

#### Duration Bucketing

| Duration | Bucket Expression |
| :--- | :--- |
| `daily` (default) | `to_char(closed_day, 'YYYY-MM-DD')` |
| `weekly` | `to_char(date_trunc('week', closed_day), 'YYYY-MM-DD')` |
| `monthly` | `to_char(closed_day, 'YYYY-MM')` |

For weekly/monthly trend, the reported `productivity_per_technician_per_day` is `AVG(daily_prod)` across the days within that bucket — not `total_tickets / distinct_techs` for the whole bucket.

#### Insights (Top / Bottom Technician)

Per technician: compute `SUM(closed_tickets)` per day, then `AVG` across days for that technician. Ordered descending; first = top, last = bottom.

#### Date Filtering

Applied on `closed_day` (`>= start_date`, `<= end_date`).

---

### O&M-2 — Productivity Trend Dashboard

**Endpoint**: `GET /api/om/productivity-trend/dashboard`  
**Data Source**: `sql_om_team_productivity_dashboard` table (same as O&M-1)  
**Repository Method**: `get_productivity_trend_dashboard`

#### Relationship to O&M-1

Uses the same source table but presents a **monthly-level** view by default.

#### Formula

```
Step A — Per calendar day within a month:
    day_tickets = SUM(closed_tickets)
    daily_prod  = SUM(closed_tickets) / COUNT(DISTINCT technician)

Step B — Per month:
    month_tickets = SUM(day_tickets)
    active_days   = COUNT(closed_day) in that month
    monthly_prod  = AVG(daily_prod) across days in that month
```

#### Summary Metrics

| Field | Formula |
| :--- | :--- |
| `total_closed_tickets` | `SUM(month_tickets)` across all months |
| `total_active_months` | Count of distinct month buckets |
| `avg_monthly_productivity_per_technician_per_day` | `AVG(monthly_prod)` across months (unweighted mean of monthly averages) |

#### Trend Metrics (per month)

| Field | Formula |
| :--- | :--- |
| `total_closed_tickets` | `SUM(day_tickets)` in that month |
| `active_days` | Count of distinct days with data |
| `avg_active_technicians` | `AVG(daily distinct technician count)` within the month |
| `productivity_per_technician_per_day` | `AVG(daily_prod)` within the month |

#### Comparison and Category Breakdown

- **Comparison**: `AVG(daily_prod)` per label over all days (not per-month series).
- **Category breakdown**: `AVG(daily_prod)` per `meter_category` over all days. The metric key is `avg_monthly_productivity_per_technician_per_day`.

---

### O&M-3 — Open Ticket Ageing Dashboard

**Endpoint**: `GET /api/om/open-ageing/dashboard`  
**Data Source**: `sql_om_open_ageing` table  
**Repository Method**: `get_open_ageing_dashboard`  
**Ultimate Source**: `unified_complaints` where `closed_date IS NULL`

#### Ageing Calculation (ETL)

```sql
ageing_days = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_date)) / 86400.0
```

Computed at **ETL run time** as a float (fractional days). The API does **not** recalculate ageing at query time.

#### Ageing Buckets

| API Key | Day Range |
| :--- | :--- |
| `age_less_than_3_days` | `ageing_days < 3` |
| `age_less_than_7_days` | `3 <= ageing_days < 7` |
| `age_less_than_15_days` | `7 <= ageing_days < 15` |
| `age_less_than_30_days` | `15 <= ageing_days < 30` |
| `age_less_than_3_months` | `30 <= ageing_days < 90` |
| `age_less_than_6_months` | `90 <= ageing_days < 180` |
| `age_6_months_and_above` | `ageing_days >= 180` |

Each bucket includes sub-counts by ticket source.

#### Ticket Source Categorization

| Source | Condition on `complaint_by` |
| :--- | :--- |
| `auto_ticketing` | `ILIKE '%auto%ticketing%'` |
| `1912_helpdesk` | `ILIKE '%1912%helpdesk%'` |
| `others` | Everything else (including NULL/empty) |

If a value matches both patterns, `auto_ticketing` takes precedence.

#### Metrics

| Field | Formula |
| :--- | :--- |
| `summary.total` | `COUNT(*)` of all filtered open tickets |
| `summary.auto_ticketing` | `SUM(CASE WHEN auto_ticketing THEN 1 ELSE 0 END)` |
| `summary.1912_helpdesk` | `SUM(CASE WHEN helpdesk THEN 1 ELSE 0 END)` |
| `summary.others` | `SUM(CASE WHEN others THEN 1 ELSE 0 END)` |
| `summary.age_buckets` | Each bucket: `{total, auto_ticketing, 1912_helpdesk, others}` |
| `trend[].period_value` | Per period: `total` and 3 source counts (no per-bucket breakdown in trend) |

#### Duration Bucketing

| Duration | Bucket Expression |
| :--- | :--- |
| `daily` (default) | `to_char(created_date, 'YYYY-MM-DD')` |
| `weekly` | `to_char(date_trunc('week', created_date), 'YYYY-MM-DD')` |
| `monthly` | `to_char(date_trunc('month', created_date), 'YYYY-MM')` |

#### Date Filtering

Applied on `created_date` (`>= start_date`, `<= end_date`).

---

### O&M-4 — Average Closure Time Dashboard

**Endpoint**: `GET /api/om/avg-closure-time/dashboard`  
**Data Source**: `sql_om_avg_closure_time` table  
**Repository Method**: `get_avg_closure_time_dashboard`  
**Ultimate Source**: `unified_complaints` where `closed_date IS NOT NULL`

#### ETL Pre-aggregation

```sql
avg_resolution_days = AVG(EXTRACT(EPOCH FROM (closed_date - created_date)) / 86400.0)
closed_tickets = COUNT(*)
-- Grouped by: project, discom, zone, circle, division, subdivision,
--             meter_category, closed_date
```

Each row holds the **per-group average** resolution in fractional days and the ticket count.

#### Weighted Average Formula (API Layer)

```
numerator   = SUM(avg_resolution_days * closed_tickets)
denominator = SUM(CASE WHEN closed_tickets > 0 THEN closed_tickets ELSE 1 END)
weighted_avg_resolution = ROUND(numerator / denominator, 2)
```

The `ELSE 1` handles the edge case of a row with 0 tickets (prevents division by zero; contributes 1 to denominator).

#### Metrics

| Field | Formula |
| :--- | :--- |
| `summary.total_closed_tickets` | `SUM(closed_tickets)` |
| `summary.avg_resolution_days` | `ROUND(weighted_avg, 2)` |
| `trend[].period_value` | Per bucket: `total_closed_tickets` + `avg_resolution_days` |
| `comparison[].label` | Per cluster: same two metrics |
| `category_breakdown` | Empty for `total`/`consumer`. Per `meter_category` for `feeder`/`dt`. |

#### Duration Bucketing

| Duration | Bucket Expression |
| :--- | :--- |
| `daily` | `to_char(closed_date, 'YYYY-MM-DD')` |
| `weekly` | `to_char(date_trunc('week', closed_date), 'YYYY-MM-DD')` |
| `monthly` (default) | `to_char(closed_date, 'YYYY-MM')` |

#### Date Filtering

Applied on `closed_date` (`>= start_date`, `<= end_date`).

---

## Quick Reference Table

| KPI | Endpoint | Source Table | Key Formula |
| :--- | :--- | :--- | :--- |
| **KPI 1** | `/api/mi/progress/dashboard` | `sql_mi_progress` | `SUM(total_mi_progress)` |
| **KPI 2.5** | `/api/mi/productivity/team/dashboard` | `sql_mi_technician_productivity` | `AVG(daily: installs / distinct techs)` |
| **KPI 3.5** | `/api/mi/productivity/trend/dashboard` | `sql_mi_technician_productivity` | Same as 2.5, monthly default |
| **KPI 4** | `/api/mi/inventory-utilization/summary` | `sql_inventory_utilization` | `installed / inventory * 100` |
| **KPI 5** | `/api/mi/pace-vs-stock/summary` | `sql_inventory_utilization` | `MAX(0, inventory - installed)` |
| **KPI 6** | `/api/mi/stock-ageing/dashboard` | `sql_stock_ageing` | `SUM(age_0_30 + ... + age_90_plus)` |
| **KPI 7** | `/api/mi/mi-vs-sat/summary` | `sql_mi_vs_sat` | `total_sat / total_mi * 100` |
| **KPI 8** | `/api/mi/non-sat-ageing/dashboard` | `sql_non_sat_ageing` | `CASE` on `ageing_days` into 5 buckets |
| **KPI 9** | `/api/mi/meter-journey/dashboard` | `sql_meter_journey_avg_time` | `SUM(stage * count) / SUM(count)`, `ceil()` |
| **KPI 10** | `/api/mi/meter-stage` | `sql_meter_current_stage` | `SUM(inventory/installed/sat_done/revenue_collected)` |
| **KPI 11** | `/api/mi/mi-vs-sat-vs-invoice/summary` | `sql_mi_sat_invoice` | `SUM` of mi, sat, lumpsum_invoice, pmpm_invoice |
| **KPI 12** | `/api/mi/revenue-realized/summary` | `sql_revenue_realized` | `SUM` of 4 revenue counters |
| **KPI 13** | `/api/mi/revenue-ageing/summary` | `sql_revenue_ageing` | `SUM(age_0_30 + ... + age_90_plus)` |
| **KPI 14** | `/api/mi/defective-meters/summary` | `sql_defective_meters` | `SUM(burnt + faulty + others)` |
| **SAT** | `/api/mi/sat-dash/satBlueData`, `/api/mi/sat-dash/{region}`, `/api/mi/command-center/{region}` | `dashboard_command_center*` | Stored as-is from ETL |
| **O&M-1** | `/api/om/productivity-team/dashboard` | `sql_om_team_productivity_dashboard` | `AVG(daily: tickets / distinct techs)` |
| **O&M-2** | `/api/om/productivity-trend/dashboard` | `sql_om_team_productivity_dashboard` | `AVG(monthly AVG(daily prod))` |
| **O&M-3** | `/api/om/open-ageing/dashboard` | `sql_om_open_ageing` | `(now - created_date) / 86400` into 7 buckets |
| **O&M-4** | `/api/om/avg-closure-time/dashboard` | `sql_om_avg_closure_time` | `SUM(avg_days * tickets) / SUM(tickets)` |
