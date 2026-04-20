-- ============================================================
-- KPI 12: Revenue Realized - Column Refinement
-- Created: 2025-04-17
-- Purpose: Replace total_realized with split invoice/collection counts
--         total_lumpsum_invoice, total_pmpm_invoice,
--          total_lumpsum_collection, total_pmpm_collection
-- Supports: daily, weekly, monthly period granularity
-- ============================================================

-- Add new metric columns
ALTER TABLE sql_revenue_realized
    ADD COLUMN IF NOT EXISTS total_lumpsum_invoice BIGINT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS total_pmpm_invoice BIGINT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS total_lumpsum_collection BIGINT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS total_pmpm_collection BIGINT DEFAULT 0;

-- Remove deprecated column
ALTER TABLE sql_revenue_realized
    DROP COLUMN IF EXISTS total_realized;
