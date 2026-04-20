-- ============================================================
-- MI Productivity per Team (Agency) - Pre-aggregated Table
-- Created: 2025-04-15
-- Purpose: Stores daily aggregated installations per agency for KPI dashboard
-- ============================================================

-- Create table
CREATE TABLE IF NOT EXISTS sql_mi_agency_productivity (
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
    agency VARCHAR(200),
    total_installations BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_daily_agency_record UNIQUE (
        installation_date, project, discom, zone, circle, division, subdivision,
        substation, feeder, dtr, new_meter_type, meter_category, agency
    )
);

-- Create indexes for fast query performance
CREATE INDEX IF NOT EXISTS idx_mi_agency_prod_date ON sql_mi_agency_productivity (installation_date);
CREATE INDEX IF NOT EXISTS idx_mi_agency_prod_project ON sql_mi_agency_productivity (project);
CREATE INDEX IF NOT EXISTS idx_mi_agency_prod_discom ON sql_mi_agency_productivity (discom);
CREATE INDEX IF NOT EXISTS idx_mi_agency_prod_zone ON sql_mi_agency_productivity (zone);
CREATE INDEX IF NOT EXISTS idx_mi_agency_prod_circle ON sql_mi_agency_productivity (circle);
CREATE INDEX IF NOT EXISTS idx_mi_agency_prod_division ON sql_mi_agency_productivity (division);
CREATE INDEX IF NOT EXISTS idx_mi_agency_prod_subdivision ON sql_mi_agency_productivity (subdivision);
CREATE INDEX IF NOT EXISTS idx_mi_agency_prod_agency ON sql_mi_agency_productivity (agency);

-- Create trigger to update updated_at on row change
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_sql_mi_agency_productivity_updated_at
    BEFORE UPDATE ON sql_mi_agency_productivity
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed)
-- GRANT SELECT ON sql_mi_agency_productivity TO readonly_user;
-- GRANT ALL ON sql_mi_agency_productivity TO write_user;
