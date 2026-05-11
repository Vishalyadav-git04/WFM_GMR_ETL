# Smart Meter ETL — KPI Column Reference

> Complete listing of every source column used to calculate MI and O&M KPIs.

---

## 1. MI KPIs — Columns from `Master Data File`

### 1.1 Geography / Dimension Columns

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `project` | String | Project name |
| 2 | `discom` | String | Distribution company |
| 3 | `zone` | String | Zone |
| 4 | `circle` | String | Circle |
| 5 | `division` | String | Division |
| 6 | `subdivision` | String | Subdivision |
| 7 | `substation` | String | Substation |
| 8 | `feeder` | String | Feeder |
| 9 | `dtr` | String | Distribution Transformer |

### 1.2 Meter Classification Columns

| # | Column | Type | Description |
|---|--------|------|-------------|
| 10 | `metertype` | String | Meter type code (e.g. 3PLTCTSM, HTCTPTSM) — mapped to `new_meter_type` in output |
| 11 | `connection_type` | String | Connection type string — mapped to `meter_category` in output |
| 12 | `consumerno` | String | Consumer number — used in fallback logic to derive meter_category as DT / FEEDER / CONSUMER |
| 13 | `meterserialnumber` | String | Meter serial number |

### 1.3 People Column

| # | Column | Type | Description |
|---|--------|------|-------------|
| 14 | `technicianname` | String | Technician who performed the installation |
| 15 | `supervisor` | String | Supervisor name (fallback when technician is empty) |

### 1.4 Date / Timestamp Columns

| # | Column | Type | Description |
|---|--------|------|-------------|
| 15 | `didate` | Date | Dispatch / inventory receipt date |
| 16 | `mi_date` | Date | Meter installation date |
| 17 | `installedts` | Timestamp | Installation timestamp |
| 18 | `sat_no` | String | SAT stage identifier (e.g. sat-1 … sat-9) |
| 19 | `sat_date` | Date | SAT completion date |
| 20 | `gmrtoagencyts` | Timestamp | GMR-to-agency handover timestamp |
| 21 | `agencytosupts` | Timestamp | Agency-to-supervisor handover timestamp |
| 22 | `lumpsum_invoice_date` | Date | Lumpsum invoice date |
| 23 | `pmpm_invoice_date` | Date | PMPM invoice date |
| 24 | `lumpsum_collection_date` | Date | Lumpsum collection date |
| 25 | `pmpm_collection_date` | Date | PMPM collection date |

---

## 2. O&M KPIs — Columns from `O&M Complaint File`

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `project` | String | Project name |
| 2 | `discom` | String | Distribution company |
| 3 | `zone` | String | Zone |
| 4 | `circle` | String | Circle |
| 5 | `division` | String | Division |
| 6 | `sub_division` | String | Subdivision |
| 7 | `feeder` | String | Feeder |
| 8 | `dtr` | String | Distribution Transformer |
| 9 | `meter_category` | String | Meter category (e.g. CONSUMER, DT, FEEDER) |
| 10 | `technician` | String | Technician assigned to the ticket |
| 11 | `supervisor` | String | Supervisor (fallback when technician is empty) |
| 12 | `closed_date` | Timestamp | Ticket closure date |
| 13 | `created_date` | Timestamp | Ticket creation date |
| 14 | `ticket_id` | String | Unique ticket identifier |
| 15 | `agency` | String | Agency responsible for the ticket |
| 16 | `complaint_by` | String | Source of the complaint |
| 17 | `complaint_type` | String | Type of complaint |
| 18 | `complaint_category` | String | Complaint category |
| 19 | `old_smart_meter_number` | String | Old meter serial number (join key to Master Data File) |
| 20 | `new_smart_meter_number` | String | New replacement meter serial number |

---

## 3. All MI Columns (Master Data File) — 25 columns

`project`, `discom`, `zone`, `circle`, `division`, `subdivision`, `substation`,
`feeder`, `dtr`, `metertype`, `connection_type`, `consumerno`, `meterserialnumber`,
`technicianname`, `supervisor`, `didate`, `mi_date`, `installedts`, `sat_no`,
`sat_date`, `gmrtoagencyts`, `agencytosupts`, `lumpsum_invoice_date`,
`pmpm_invoice_date`, `lumpsum_collection_date`, `pmpm_collection_date`

---

## 4. All O&M Columns (O&M Complaint File) — 20 columns

`project`, `discom`, `zone`, `circle`, `division`, `sub_division`, `feeder`,
`dtr`, `meter_category`, `technician`, `supervisor`, `closed_date`, `created_date`,
`ticket_id`, `agency`, `complaint_by`, `complaint_type`, `complaint_category`,
`old_smart_meter_number`, `new_smart_meter_number`

---

## 5. Summary

| Domain | Source File | Unique Columns |
|--------|------------|:--------------:|
| MI KPIs | `Master Data File` | 25 |
| O&M KPIs | `O&M Complaint File` | 20 |
