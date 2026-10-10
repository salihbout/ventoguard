-- GenAI extraction from technician notes: precursor notes, with technician_name masked by the UC column mask
SELECT log_id, turbine_id, created_ts, technician_name, note_text, ai_component, ai_severity, ai_failure_precursor, ai_summary_en
FROM serverless_stable_7zqte5_catalog.ventoguard_gold.maintenance_log_insights WHERE ai_failure_precursor ORDER BY created_ts DESC LIMIT 15
