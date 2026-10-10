-- Cost of unplanned failures by component (repair incl. crane + lost revenue during downtime)
SELECT component, count(*) AS failures, round(avg(downtime_hours) / 24, 1) AS avg_downtime_days,
       round(sum(repair_cost_eur)) AS repair_cost_eur, round(sum(lost_revenue_eur)) AS lost_revenue_eur,
       round(sum(total_event_cost_eur)) AS total_event_cost_eur
FROM serverless_stable_7zqte5_catalog.ventoguard_gold.gold_failure_history GROUP BY component ORDER BY total_event_cost_eur DESC
