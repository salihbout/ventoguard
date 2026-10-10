-- Bronze: hourly day-ahead power prices (DE-LU)
CREATE OR REFRESH STREAMING TABLE bronze_market_prices
COMMENT 'Raw hourly EPEX day-ahead prices for bidding zone DE-LU (CSV). Synthetic.'
TBLPROPERTIES ('quality' = 'bronze')
AS SELECT *, _metadata.file_path AS _source_file, current_timestamp() AS _ingested_at
FROM STREAM read_files('${landing_root}/market_prices', format => 'csv', header => true, inferColumnTypes => true);
