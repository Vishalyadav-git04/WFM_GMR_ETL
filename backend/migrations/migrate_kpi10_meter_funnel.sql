-- KPI 10: Convert sql_meter_current_stage from stage-based to pre-aggregated funnel metrics
-- Replaces: current_stage (VARCHAR) + meter_count (BIGINT)
-- With: inventory, installed, sat_done, revenue_collected (all BIGINT)

-- Step 0: Remove all existing rows (old stage-based data)
TRUNCATE TABLE sql_meter_current_stage;

-- Step 1: Drop old columns if they exist
ALTER TABLE sql_meter_current_stage 
    DROP COLUMN IF EXISTS current_stage,
    DROP COLUMN IF EXISTS meter_count;

-- Step 2: Add new funnel metric columns
ALTER TABLE sql_meter_current_stage 
    ADD COLUMN IF NOT EXISTS inventory BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS installed BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS sat_done BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS revenue_collected BIGINT NOT NULL DEFAULT 0;

-- Step 3: Drop old unique constraint if it exists (name may vary)
ALTER TABLE sql_meter_current_stage 
    DROP CONSTRAINT IF EXISTS uq_meter_current_stage_gain;
ALTER TABLE sql_meter_current_stage 
    DROP CONSTRAINT IF EXISTS uq_meter_current_stage_grain;

-- Step 4: Recreate unique constraint on grouping grain only (after clean insert)
ALTER TABLE sql_meter_current_stage 
    ADD CONSTRAINT uq_meter_funnel_grain 
    UNIQUE (project, discom, zone, circle, division, subdivision, substation, feeder, dtr, new_meter_type, meter_category);

-- Step 5: Indexes for common filter patterns
CREATE INDEX IF NOT EXISTS idx_funnel_project ON sql_meter_current_stage(project);
CREATE INDEX IF NOT EXISTS idx_funnel_geo ON sql_meter_current_stage(discom, zone, circle, division, subdivision);
CREATE INDEX IF NOT EXISTS idx_funnel_category ON sql_meter_current_stage(meter_category);
CREATE INDEX IF NOT EXISTS idx_funnel_meter_type ON sql_meter_current_stage(new_meter_type);
