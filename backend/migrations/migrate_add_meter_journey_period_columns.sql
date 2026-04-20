-- KPI 9: time buckets on sql_meter_journey_avg_time (daily / weekly / monthly by pmpm_collection_date)

ALTER TABLE sql_meter_journey_avg_time
    ADD COLUMN IF NOT EXISTS period_type VARCHAR(20),
    ADD COLUMN IF NOT EXISTS period_value VARCHAR(50);

CREATE INDEX IF NOT EXISTS idx_meter_journey_period
    ON sql_meter_journey_avg_time (period_type, period_value);
