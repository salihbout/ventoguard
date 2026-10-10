-- GenAI maintenance briefs (ai_query + Claude) for at-risk turbines
SELECT turbine_id, risk_tier, round(failure_prob_14d, 3) AS p, headline, diagnosis, recommended_action, urgency_days, business_case, llm_endpoint
FROM serverless_stable_7zqte5_catalog.wind_reliability.turbine_ai_briefs ORDER BY failure_prob_14d DESC
