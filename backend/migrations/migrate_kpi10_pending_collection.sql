-- KPI 10: Add "pending PMPM collection" funnel columns to sql_meter_current_stage
-- These four columns count meters where pmpm_collection_date IS NULL,
-- enabling the refactored "Pending Collection Funnel" response shape.
--
-- pending_inventory     = COUNT(*) WHERE pmpm_collection_date IS NULL
-- pending_installed     = + AND mi_date IS NOT NULL AND sat_no IS NOT NULL/non-empty
-- pending_sat_done      = + AND sat_date IS NOT NULL
-- pending_invoice_done  = + AND pmpm_invoice_date IS NOT NULL

ALTER TABLE sql_meter_current_stage
    ADD COLUMN IF NOT EXISTS pending_inventory     BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS pending_installed     BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS pending_sat_done      BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS pending_invoice_done  BIGINT NOT NULL DEFAULT 0;
