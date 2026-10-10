-- Bronze: CMMS work-order notes (free text, German/English)
CREATE OR REFRESH STREAMING TABLE bronze_maintenance_logs
COMMENT 'Raw CMMS maintenance work-order notes written by field technicians (JSON). Synthetic.'
TBLPROPERTIES ('quality' = 'bronze')
AS SELECT *, _metadata.file_path AS _source_file, current_timestamp() AS _ingested_at
FROM STREAM read_files('${landing_root}/maintenance_logs', format => 'json');
