-- Fix KPI 12: Align sql_revenue_realized with code (single total_realized column)

ALTER TABLE sql_revenue_realized 
    DROP COLUMN IF EXISTS total_lumpsum_invoice,
    DROP COLUMN IF EXISTS total_pmpm_invoice,
    DROP COLUMN IF EXISTS total_lumpsum_collection,
    DROP COLUMN IF EXISTS total_pmpm_collection;

ALTER TABLE sql_revenue_realized 
    ADD COLUMN IF NOT EXISTS total_realized BIGINT NOT NULL DEFAULT 0;
