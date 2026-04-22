-- ============================================================
-- MI Productivity per Technician (Dashboard) - Pre-aggregated Table
-- Created: 2026-04-22
-- Purpose: Stores daily aggregated verified installations per technician
-- NOTE: Additive migration (does NOT drop any existing tables)
-- ============================================================

-- Create table (additive)
CREATE TABLE IF NOT EXISTS sql_mi_technician_productivity (
    id BIGSERIAL PRIMARY KEY,
    installation_date DATE NOT NULL,
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
    technician VARCHAR(200),
    total_installations BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_daily_technician_record UNIQUE (
        installation_date, project, discom, zone, circle, division, subdivision,
        substation, feeder, dtr, new_meter_type, meter_category, technician
    )
);

-- Indexes for fast query performance
CREATE INDEX IF NOT EXISTS idx_mi_tech_prod_date ON sql_mi_technician_productivity (installation_date);
CREATE INDEX IF NOT EXISTS idx_mi_tech_prod_project ON sql_mi_technician_productivity (project);
CREATE INDEX IF NOT EXISTS idx_mi_tech_prod_discom ON sql_mi_technician_productivity (discom);
CREATE INDEX IF NOT EXISTS idx_mi_tech_prod_zone ON sql_mi_technician_productivity (zone);
CREATE INDEX IF NOT EXISTS idx_mi_tech_prod_circle ON sql_mi_technician_productivity (circle);
CREATE INDEX IF NOT EXISTS idx_mi_tech_prod_division ON sql_mi_technician_productivity (division);
CREATE INDEX IF NOT EXISTS idx_mi_tech_prod_subdivision ON sql_mi_technician_productivity (subdivision);
CREATE INDEX IF NOT EXISTS idx_mi_tech_prod_technician ON sql_mi_technician_productivity (technician);

-- Trigger to update updated_at on row change (use dedicated function to avoid name collisions)
CREATE OR REPLACE FUNCTION update_mi_technician_productivity_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_sql_mi_technician_productivity_updated_at ON sql_mi_technician_productivity;
CREATE TRIGGER update_sql_mi_technician_productivity_updated_at
    BEFORE UPDATE ON sql_mi_technician_productivity
    FOR EACH ROW
    EXECUTE FUNCTION update_mi_technician_productivity_updated_at();

