-- Bronze: asset register
CREATE OR REFRESH STREAMING TABLE bronze_turbines
COMMENT 'Raw asset register export (CSV): one row per turbine. Synthetic.'
TBLPROPERTIES ('quality' = 'bronze')
AS SELECT *, _metadata.file_path AS _source_file, current_timestamp() AS _ingested_at
FROM STREAM read_files('${landing_root}/turbines', format => 'csv', header => true, inferColumnTypes => true);
