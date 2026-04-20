-- ============================================================
-- Non-SAT Ageing Dashboard Summary Table
-- Created: 2025-04-17
-- Purpose: Pre-aggregated Non-SAT Ageing metrics for dashboard queries
-- ============================================================

-- Create table
CREATE TABLE IF NOT EXISTS sql_non_sat_ageing_dashboard (
    id BIGSERIAL PRIMARY KEY,
    -- Dimensions (inherits MIDimensionMixin)
    project VARCHAR(200),
    discom VARCHAR(200),
    zone VARCHAR(200),
    circle VARCHAR(200),
    division VARCHAR(200),
    subdivision VARCHAR(200),
    substation VARCHAR(200),
    feeder VARCHAR(200),
    dtr VARCHAR(200),
    new_meter_type VARCHAR(200),
    meter_category VARCHAR(100),
    -- Period
    period_type VARCHAR(20),          -- 'daily' | 'weekly' | 'monthly'
    period_value VARCHAR(50),         -- display string (DD-MM-YY or YYYY-MM)
    date_value DATE,                  -- actual date for filtering
    -- Metrics
    total_non_sat BIGINT DEFAULT 0,
    age_gt_30 BIGINT DEFAULT 0,
    age_gt_60 BIGINT DEFAULT 0,
    age_gt_90 BIGINT DEFAULT 0,
    age_gt_120 BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_non_sat_ageing_dash_date ON sql_non_sat_ageing_dashboard (date_value);
CREATE INDEX IF NOT EXISTS idx_non_sat_ageing_dash_period_type ON sql_non_sat_ageing_dashboard (period_type);
CREATE INDEX IF NOT EXISTS idx_non_sat_ageing_dash_project ON sql_non_sat_ageing_dashboard (project);
CREATE INDEX IF NOT EXISTS idx_non_sat_ageing_dash_discom ON sql_non_sat_ageing_dashboard (discom);
CREATE INDEX IF NOT EXISTS idx_non_sat_ageing_dash_zone ON sql_non_sat_ageing_dashboard (zone);
CREATE INDEX IF NOT EXISTS idx_non_sat_ageing_dash_circle ON sql_non_sat_ageing_dashboard (circle);
CREATE INDEX IF NOT EXISTS idx_non_sat_ageing_dash_division ON sql_non_sat_ageing_dashboard (division);
CREATE INDEX IF NOT EXISTS idx_non_sat_ageing_dash_subdivision ON sql_non_sat_ageing_dashboard (subdivision);
CREATE INDEX IF NOT EXISTS idx_non_sat_ageing_dash_substation ON sql_non_sat_ageing_dashboard (substation);
CREATE INDEX IF NOT EXISTS idx_non_sat_ageing_dash_feeder ON sql_non_sat_ageing_dashboard (feeder);
CREATE INDEX IF NOT EXISTS idx_non_sat_ageing_dash_dtr ON sql_non_sat_ageing_dashboard (dtr);
CREATE INDEX IF NOT EXISTS idx_non_sat_ageing_dash_new_meter_type ON sql_non_sat_ageing_dashboard (new_meter_type);
CREATE INDEX IF NOT EXISTS idx_non_sat_ageing_dash_meter_category ON sql_non_sat_ageing_dashboard (meter_category);

-- Trigger to update updated_at on row change
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_sql_non_sat_ageing_dashboard_updated_at
    BEFORE UPDATE ON sql_non_sat_ageing_dashboard
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed)
-- GRANT SELECT ON sql_non_sat_ageing_dashboard TO readonly_user;
-- GRANT ALL ON sql_non_sat_ageing_dashboard TO write_user;
