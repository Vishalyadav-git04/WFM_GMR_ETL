-- Add complaint_by column to sql_om_open_ageing table
ALTER TABLE sql_om_open_ageing ADD COLUMN IF NOT EXISTS complaint_by VARCHAR(200);
