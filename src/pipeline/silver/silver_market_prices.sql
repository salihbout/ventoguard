CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.silver_market_prices
COMMENT 'Hourly day-ahead price, EUR/MWh, bidding zone DE-LU.'
TBLPROPERTIES ('quality' = 'silver')
AS SELECT to_timestamp(hour_start_utc) AS hour_start_utc, bidding_zone, CAST(price_eur_mwh AS DOUBLE) AS price_eur_mwh
FROM bronze_market_prices;
