CREATE OR REFRESH STREAMING TABLE silver_maintenance_logs (
  CONSTRAINT has_text EXPECT (length(note_text) > 5) ON VIOLATION DROP ROW
)
COMMENT 'Technician work-order notes (German/English free text). technician_name is personal data and is masked for non-reliability users.'
TBLPROPERTIES ('quality' = 'silver')
AS SELECT
  log_id, turbine_id, to_timestamp(created_ts) AS created_ts, category, technician_name, note_text
FROM STREAM(bronze_maintenance_logs);
