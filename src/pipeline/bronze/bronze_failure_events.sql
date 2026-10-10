-- Bronze: confirmed component failures from CMMS
CREATE OR REFRESH STREAMING TABLE bronze_failure_events
COMMENT 'Raw confirmed component failure events from CMMS (CSV). Synthetic.'
TBLPROPERTIES ('quality' = 'bronze')
AS SELECT *, _metadata.file_path AS _source_file, current_timestamp() AS _ingested_at
FROM STREAM read_files('${landing_root}/failure_events', format => 'csv', header => true, inferColumnTypes => true);
