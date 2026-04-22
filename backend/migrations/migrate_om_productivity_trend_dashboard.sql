-- ============================================================
-- O&M-2 Productivity Trend Dashboard Enhancement
-- Created: 2026-04-22
-- Purpose: Add active_days and avg_active_technicians columns
--          to enable dashboard-style response for O&M-2 KPI
-- ============================================================

-- Add new columns to sql_om_productivity_trend
ALTER TABLE sql_om_productivity_trend
    ADD COLUMN IF NOT EXISTS active_days INTEGER,
    ADD COLUMN IF NOT EXISTS avg_active_technicians FLOAT;

-- Create index on closed_month for faster trend aggregation
CREATE INDEX IF NOT EXISTS idx_om_productivity_trend_month
    ON sql_om_productivity_trend (closed_month);

-- Create index on composite key for filtering
CREATE INDEX IF NOT EXISTS idx_om_productivity_trend_filters
    ON sql_om_productivity_trend (project, discom, zone, circle, division, subdivision, meter_category);