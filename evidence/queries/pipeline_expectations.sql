-- Expectation pass/fail counts (silver layer)
SELECT x.dataset, x.name AS expectation, sum(x.passed_records) AS passed_records, sum(x.failed_records) AS failed_records
FROM event_log(TABLE(serverless_stable_7zqte5_catalog.ventoguard_silver.silver_scada)) e
LATERAL VIEW explode(from_json(e.details:flow_progress:data_quality:expectations,
  'array<struct<name:string,dataset:string,passed_records:bigint,failed_records:bigint>>')) t AS x
WHERE e.event_type = 'flow_progress'
GROUP BY ALL ORDER BY 1, 2;
