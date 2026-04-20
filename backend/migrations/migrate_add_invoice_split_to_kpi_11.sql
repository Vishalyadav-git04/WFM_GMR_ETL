-- ============================================================
-- KPI 11: MI vs SAT vs Invoice - Split Invoice Columns
-- Created: 2025-04-17
-- Purpose: Add total_lumpsum_invoice and total_pmpm_invoice columns
--          to sql_mi_sat_invoice table for separate invoice tracking
-- ============================================================

-- Add new columns for split invoice counts
ALTER TABLE sql_mi_sat_invoice
    ADD COLUMN IF NOT EXISTS total_lumpsum_invoice BIGINT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS total_pmpm_invoice BIGINT DEFAULT 0;

-- Note: total_invoice column already exists and should be maintained as:
--   total_invoice = total_lumpsum_invoice + total_pmpm_invoice
-- The ETL process will populate all three columns accordingly.
