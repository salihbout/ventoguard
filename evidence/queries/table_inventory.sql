-- Every VentoGuard table with its layer schema and row count (default catalog)
SELECT 'ventoguard_bronze' AS schema, 'bronze_scada' AS table_name, count(*) AS row_count FROM serverless_stable_7zqte5_catalog.ventoguard_bronze.bronze_scada
UNION ALL SELECT 'ventoguard_silver' AS schema, 'silver_scada' AS table_name, count(*) AS row_count FROM serverless_stable_7zqte5_catalog.ventoguard_silver.silver_scada
UNION ALL SELECT 'ventoguard_bronze' AS schema, 'bronze_maintenance_logs' AS table_name, count(*) AS row_count FROM serverless_stable_7zqte5_catalog.ventoguard_bronze.bronze_maintenance_logs
UNION ALL SELECT 'ventoguard_silver' AS schema, 'silver_maintenance_logs' AS table_name, count(*) AS row_count FROM serverless_stable_7zqte5_catalog.ventoguard_silver.silver_maintenance_logs
UNION ALL SELECT 'ventoguard_silver' AS schema, 'silver_turbines' AS table_name, count(*) AS row_count FROM serverless_stable_7zqte5_catalog.ventoguard_silver.silver_turbines
UNION ALL SELECT 'ventoguard_silver' AS schema, 'silver_failure_events' AS table_name, count(*) AS row_count FROM serverless_stable_7zqte5_catalog.ventoguard_silver.silver_failure_events
UNION ALL SELECT 'ventoguard_silver' AS schema, 'silver_market_prices' AS table_name, count(*) AS row_count FROM serverless_stable_7zqte5_catalog.ventoguard_silver.silver_market_prices
UNION ALL SELECT 'ventoguard_gold' AS schema, 'gold_turbine_daily' AS table_name, count(*) AS row_count FROM serverless_stable_7zqte5_catalog.ventoguard_gold.gold_turbine_daily
UNION ALL SELECT 'ventoguard_gold' AS schema, 'gold_farm_daily' AS table_name, count(*) AS row_count FROM serverless_stable_7zqte5_catalog.ventoguard_gold.gold_farm_daily
UNION ALL SELECT 'ventoguard_gold' AS schema, 'gold_failure_history' AS table_name, count(*) AS row_count FROM serverless_stable_7zqte5_catalog.ventoguard_gold.gold_failure_history
UNION ALL SELECT 'ventoguard_gold' AS schema, 'turbine_health_features' AS table_name, count(*) AS row_count FROM serverless_stable_7zqte5_catalog.ventoguard_gold.turbine_health_features
UNION ALL SELECT 'ventoguard_gold' AS schema, 'turbine_risk_history' AS table_name, count(*) AS row_count FROM serverless_stable_7zqte5_catalog.ventoguard_gold.turbine_risk_history
UNION ALL SELECT 'ventoguard_gold' AS schema, 'turbine_risk_scores' AS table_name, count(*) AS row_count FROM serverless_stable_7zqte5_catalog.ventoguard_gold.turbine_risk_scores
UNION ALL SELECT 'ventoguard_gold' AS schema, 'maintenance_log_insights' AS table_name, count(*) AS row_count FROM serverless_stable_7zqte5_catalog.ventoguard_gold.maintenance_log_insights
UNION ALL SELECT 'ventoguard_gold' AS schema, 'turbine_ai_briefs' AS table_name, count(*) AS row_count FROM serverless_stable_7zqte5_catalog.ventoguard_gold.turbine_ai_briefs
UNION ALL SELECT 'ventoguard_serving', 'turbine_risk_scores (Lakebase synced)', count(*) FROM serverless_stable_7zqte5_catalog.ventoguard_serving.turbine_risk_scores
