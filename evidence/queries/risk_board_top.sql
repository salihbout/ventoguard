-- Operational risk board (latest score date) — the table synced to Lakebase and shown in the app
SELECT turbine_id, farm_name, risk_tier, failure_prob_14d, likely_component, recommended_window, top_signals,
       round(avoidable_cost_if_caught_eur) AS avoidable_cost_if_caught_eur, model_version, score_date
FROM serverless_stable_7zqte5_catalog.wind_reliability.turbine_risk_scores ORDER BY failure_prob_14d DESC LIMIT 10
