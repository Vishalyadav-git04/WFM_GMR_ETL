-- KPI 9: Meter journey average time — new stage columns and meter_count
-- Replaces legacy di_to_gmr / gmr_to_agency / agency_to_sup / sup_to_install / install_to_sat / sat_to_revenue

ALTER TABLE sql_meter_journey_avg_time
    DROP COLUMN IF EXISTS di_to_gmr,
    DROP COLUMN IF EXISTS gmr_to_agency,
    DROP COLUMN IF EXISTS agency_to_sup,
    DROP COLUMN IF EXISTS sup_to_install,
    DROP COLUMN IF EXISTS install_to_sat,
    DROP COLUMN IF EXISTS sat_to_revenue;

ALTER TABLE sql_meter_journey_avg_time
    ADD COLUMN IF NOT EXISTS inventory_to_store DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS store_to_agency DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS agency_to_meter_installation DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS meter_installation_to_sat DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS sat_to_invoice DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS invoice_to_revenue DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS meter_count BIGINT;

-- total_journey retained; if missing on old DBs, add (normally already present)
ALTER TABLE sql_meter_journey_avg_time
    ADD COLUMN IF NOT EXISTS total_journey DOUBLE PRECISION;
