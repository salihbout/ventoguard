# Genie space conversations: execution evidence

Space `01f1c4d953cb132e838ecd828813a354` (*VentoGuard Reliability: Wind Fleet Analytics*), asked via the Genie Conversation API on 2026-10-10 20:27 UTC. Everything below is returned verbatim by Genie (answer text, generated SQL, result rows).

## Q: Which wind farm lost the most revenue to unplanned failures, and which component caused it?

_status: COMPLETED · conversation 01f1c4e8fe3b12b8814e217fc7fea99d_

**Genie:** You want to know which wind farm lost the most revenue due to unplanned failures and identify the component responsible for the highest lost revenue within that top farm.

```sql
WITH `farm_component_revenue` AS (
  SELECT
    `farm_name`,
    `component`,
    SUM(`lost_revenue_eur`) AS `component_lost_revenue_eur`
  FROM `serverless_stable_7zqte5_catalog`.`ventoguard_gold`.`gold_failure_history`
  WHERE `farm_name` IS NOT NULL
    AND `component` IS NOT NULL
  GROUP BY `farm_name`, `component`
), `farm_totals` AS (
  SELECT
    `farm_name`,
    SUM(`component_lost_revenue_eur`) AS `farm_lost_revenue_eur`,
    RANK() OVER (ORDER BY SUM(`component_lost_revenue_eur`) DESC) AS `farm_rank`
  FROM `farm_component_revenue`
  GROUP BY `farm_name`
), `component_ranked` AS (
  SELECT
    `fcr`.`farm_name`,
    `fcr`.`component`,
    `fcr`.`component_lost_revenue_eur`,
    `ft`.`farm_lost_revenue_eur`,
    RANK() OVER (PARTITION BY `fcr`.`farm_name` ORDER BY `fcr`.`component_lost_revenue_eur` DESC) AS `component_rank`
  FROM `farm_component_revenue` AS `fcr`
  INNER JOIN `farm_totals` AS `ft`
    ON `fcr`.`farm_name` = `ft`.`farm_name`
  WHERE `ft`.`farm_rank` <= 1
)
SELECT
  `farm_name`,
  `farm_lost_revenue_eur`,
  `component`,
  `component_lost_revenue_eur`
FROM `component_ranked`
WHERE `component_rank` <= 1
ORDER BY `farm_lost_revenue_eur` DESC, `component_lost_revenue_eur` DESC;
```

| farm_name | farm_lost_revenue_eur | component | component_lost_revenue_eur |
|---|---|---|---|
| Uckermark Nord | 275262.0 | gearbox | 208583.0 |

**Genie:** **Uckermark Nord** lost the most revenue to unplanned failures, with total lost revenue of **EUR 275,262**. The biggest contributing component at **Uckermark Nord** was the **gearbox**, which accounted for **EUR 208,583** in lost revenue; in this result, the gearbox made up most of the farm’s unplanned failure revenue loss.


## Q: Show the 10 turbines with the highest failure probability and their likely component

_status: COMPLETED · conversation 01f1c4e909cd13ffa649ffc899a7a1a9_

**Genie:** You want to see the 10 turbines with the highest 14-day failure probability along with the wind farm they belong to and the component most likely to fail.

```sql
WITH ranked_turbines AS (
  SELECT
    `turbine_id`,
    `farm_name`,
    `failure_prob_14d`,
    `likely_component`,
    RANK() OVER (ORDER BY `failure_prob_14d` DESC) AS `risk_rank`
  FROM `serverless_stable_7zqte5_catalog`.`ventoguard_gold`.`turbine_risk_scores`
  WHERE `failure_prob_14d` IS NOT NULL
    AND `likely_component` IS NOT NULL
)
SELECT
  `turbine_id`,
  `farm_name`,
  `failure_prob_14d`,
  `likely_component`
FROM ranked_turbines
WHERE `risk_rank` <= 10
ORDER BY `failure_prob_14d` DESC, `turbine_id`
```

| turbine_id | farm_name | failure_prob_14d | likely_component |
|---|---|---|---|
| F03-T07 | Hunsrueck Hoehe | 0.9953 | gearbox |
| F03-T09 | Hunsrueck Hoehe | 0.9912 | gearbox |
| F01-T20 | Uckermark Nord | 0.9578 | gearbox |
| F04-T16 | Eifel West | 0.5529 | main_bearing |
| F01-T06 | Uckermark Nord | 0.2516 | generator_bearing |
| F03-T14 | Hunsrueck Hoehe | 0.1439 | pitch_hydraulics |
| F02-T07 | Ostfriesland Kueste | 0.1032 | pitch_hydraulics |
| F02-T15 | Ostfriesland Kueste | 0.0979 | gearbox |
| F03-T16 | Hunsrueck Hoehe | 0.0932 | generator_bearing |
| F03-T02 | Hunsrueck Hoehe | 0.0707 | pitch_hydraulics |

**Genie:** Here are the **10 turbines with the highest 14-day failure probability** and their likely component; the highest-risk units are dominated by **gearbox** issues, with the top three all above **95%**.

- **F03-T07** (Hunsrueck Hoehe) — **99.53%** — **gearbox**
- **F03-T09** (Hunsrueck Hoehe) — **99.12%** — **gearbox**
- **F01-T20** (Uckermark Nord) — **95.78%** — **gearbox**
- **F04-T16** (Eifel West) — **55.29%** — **main_bearing**
- **F01-T06** (Uckermark Nord) — **25.16%** — **generator_bearing**

Across all 10 turbines returned, **gearbox** is the most frequent likely component and **Hunsrueck Hoehe** appears most often, with **5 of the 10** turbines in this top-risk group.


## Q: What was technical availability per farm by month?

_status: COMPLETED · conversation 01f1c4e912381083a5f6ccc997dbbbbe_

**Genie:** You want to see the average technical availability percentage for each wind farm broken down by month.

```sql
SELECT `farm_name`, DATE_TRUNC('MONTH', `reading_date`) AS `month`, ROUND(AVG(`technical_availability`) * 100, 2) AS `technical_availability_pct`
FROM `serverless_stable_7zqte5_catalog`.`ventoguard_gold`.`gold_farm_daily`
WHERE `farm_name` IS NOT NULL
  AND `reading_date` IS NOT NULL
  AND `technical_availability` IS NOT NULL
GROUP BY `farm_name`, DATE_TRUNC('MONTH', `reading_date`)
ORDER BY `month`, `farm_name`
```

| farm_name | month | technical_availability_pct |
|---|---|---|
| Eifel West | 2026-04-01T00:00:00.000Z | 100.0 |
| Hunsrueck Hoehe | 2026-04-01T00:00:00.000Z | 100.0 |
| Ostfriesland Kueste | 2026-04-01T00:00:00.000Z | 100.0 |
| Uckermark Nord | 2026-04-01T00:00:00.000Z | 100.0 |
| Eifel West | 2026-05-01T00:00:00.000Z | 100.0 |
| Hunsrueck Hoehe | 2026-05-01T00:00:00.000Z | 97.02 |
| Ostfriesland Kueste | 2026-05-01T00:00:00.000Z | 100.0 |
| Uckermark Nord | 2026-05-01T00:00:00.000Z | 98.86 |
| Eifel West | 2026-06-01T00:00:00.000Z | 99.18 |
| Hunsrueck Hoehe | 2026-06-01T00:00:00.000Z | 96.95 |
| Ostfriesland Kueste | 2026-06-01T00:00:00.000Z | 99.1 |
| Uckermark Nord | 2026-06-01T00:00:00.000Z | 97.63 |
| Eifel West | 2026-07-01T00:00:00.000Z | 95.83 |
| Hunsrueck Hoehe | 2026-07-01T00:00:00.000Z | 93.64 |
| Ostfriesland Kueste | 2026-07-01T00:00:00.000Z | 96.88 |

_… 13 more rows_

**Genie:** Technical availability by farm is available for **April to October 2026** (28 monthly farm records total). Examples include:
- **April 2026:** all four farms were at **100.00%**
- **July 2026:** **Eifel West 95.83%**, **Hunsrueck Hoehe 93.64%**, **Ostfriesland Kueste 96.88%**, **Uckermark Nord 95.43%**
- **August 2026:** **Hunsrueck Hoehe** fell to **87.20%**, the lowest value in the period
- **September 2026:** **Eifel West** and **Ostfriesland Kueste** were both at **100.00%**
- **October 2026:** **Eifel West 100.00%**, **Hunsrueck Hoehe 98.92%**, **Ostfriesland Kueste 100.00%**, **Uckermark Nord 96.05%**
Across the period, **Ostfriesland Kueste** was the most consistently strong performer, while **Hunsrueck Hoehe** showed the most volatility and had the only month below **90%**.


## Q: How much money is at stake on turbines currently at risk?

_status: COMPLETED · conversation 01f1c4e91a6f11f7b7ef19f871777d56_

**Genie:** You want to know the number of turbines currently at risk of failure and the total expected and full avoidable costs in euros associated with these turbines.

```sql
SELECT COUNT(*) AS at_risk_turbines,
       ROUND(SUM(turbine_risk_scores.expected_avoidable_cost_eur)) AS expected_money_at_stake_eur,
       ROUND(SUM(turbine_risk_scores.avoidable_cost_if_caught_eur)) AS full_avoidable_cost_if_caught_eur
FROM serverless_stable_7zqte5_catalog.ventoguard_gold.turbine_risk_scores
WHERE turbine_risk_scores.risk_tier IN ('CRITICAL', 'HIGH')
  AND turbine_risk_scores.expected_avoidable_cost_eur IS NOT NULL
  AND turbine_risk_scores.avoidable_cost_if_caught_eur IS NOT NULL
```

| at_risk_turbines | expected_money_at_stake_eur | full_avoidable_cost_if_caught_eur |
|---|---|---|
| 4 | 718865.0 | 805598.0 |

**Genie:** There are **4** turbines currently at risk, with **EUR 718,865** in expected money at stake. If all of those failures were prevented, the full avoidable cost across the **4** at-risk turbines would be **EUR 805,598**.


## Q: Which technician notes mention failure precursors in the last 30 days?

_status: COMPLETED · conversation 01f1c4e9222c1ee2bf47bb83332d8731_

**Genie:** You want to see technician notes from the last 30 days that mention failure precursors.

```sql
SELECT `created_ts`, `turbine_id`, `category`, `ai_component`, `ai_severity`, `ai_summary_en`, `note_text` FROM `serverless_stable_7zqte5_catalog`.`ventoguard_gold`.`maintenance_log_insights` WHERE `created_ts` >= date_sub(current_date(), 29) AND `created_ts` < date_add(current_date(), 1) AND `ai_failure_precursor` = true ORDER BY `created_ts` DESC
```

| created_ts | turbine_id | category | ai_component | ai_severity | ai_summary_en | note_text |
|---|---|---|---|---|---|---|
| 2026-10-04T18:36:32.000Z | F03-T07 | inspection | gearbox | 4 | High gearbox oil temperature with metallic whine from intermediate stage. Oil analysis pending. | Customer remote alarm: gearbox oil temperature high warnings during full load. On site noticed faint metallic whine from intermediate stage. Oil sample sent to lab. |
| 2026-10-03T09:51:45.000Z | F03-T07 | inspection | gearbox | 3 | Elevated iron content and particles in oil. Recommend endoscopy inspection before failure. | Ölprobe Getriebe: erhöhter Eisengehalt (Fe 74 ppm) und Partikel auf Magnetstopfen. Leichte Geräusche bei Volllast. Empfehle Endoskopie. |
| 2026-10-02T09:09:51.000Z | F03-T09 | inspection | gearbox | 4 | Gearbox high oil temperature with metallic whine from intermediate stage. Oil analysis pending. | Customer remote alarm: gearbox oil temperature high warnings during full load. On site noticed faint metallic whine from intermediate stage. Oil sample sent to lab. |

**Genie:** I found **3 technician notes** in the last 30 days that were flagged as mentioning failure precursors, and all of them relate to the **gearbox** during **inspection** activities.

- **2026-10-04** — Turbine **F03-T07**; severity **4**; note mentions **high gearbox oil temperature** and a **metallic whine**, with oil analysis pending.
- **2026-10-03** — Turbine **F03-T07**; severity **3**; note mentions **elevated iron content**, **particles in oil**, and a recommendation for **endoscopy inspection before failure**.
- **2026-10-02** — Turbine **F03-T09**; severity **4**; note mentions **high gearbox oil temperature** and a **metallic whine**, with oil analysis pending.

Across all 3 notes, the precursor signals consistently point to **gearbox deterioration**, with **F03-T07** appearing twice.


## Q: Do Hansa Drives gearboxes fail more often than NordGear ones?

_status: COMPLETED · conversation 01f1c4e92dec17b6b48caf5fbaf86e07_

**Genie:** You want to compare how often gearboxes from Hansa Drives fail compared to those from NordGear. The query shows the number of turbines for each supplier, the count of gearbox failures, the failure rate per 100 turbines, and the average age of turbines for each supplier.

```sql
SELECT
  `t`.`gearbox_supplier`,
  COUNT(DISTINCT `t`.`turbine_id`) AS `turbines`,
  COUNT(`f`.`failure_id`) AS `gearbox_failures`,
  ROUND(try_divide(COUNT(`f`.`failure_id`) * 100.0,COUNT(DISTINCT `t`.`turbine_id`)), 1) AS `failures_per_100_turbines`,
  ROUND(AVG(`t`.`turbine_age_years`), 1) AS `avg_turbine_age_years`
FROM `serverless_stable_7zqte5_catalog`.`ventoguard_silver`.`silver_turbines` AS `t`
LEFT JOIN `serverless_stable_7zqte5_catalog`.`ventoguard_gold`.`gold_failure_history` AS `f`
  ON `f`.`turbine_id` = `t`.`turbine_id`
  AND `f`.`component` = 'gearbox'
WHERE `t`.`gearbox_supplier` IN ('Hansa Drives', 'NordGear')
  AND `t`.`gearbox_supplier` IS NOT NULL
GROUP BY `t`.`gearbox_supplier`
ORDER BY `failures_per_100_turbines` DESC
```

| gearbox_supplier | turbines | gearbox_failures | failures_per_100_turbines | avg_turbine_age_years |
|---|---|---|---|---|
| Hansa Drives | 64 | 8 | 12.5 | 10.5 |
| NordGear | 56 | 0 | 0.0 | 7.0 |

**Genie:** **Yes** — in this data, **Hansa Drives** gearboxes fail more often than **NordGear** ones. Hansa Drives has **8** gearbox failures across **64** turbines (**12.5 failures per 100 turbines**), while NordGear has **0** failures across **56** turbines (**0.0 per 100 turbines**). Hansa Drives turbines are also older on average (**10.5 years** vs **7.0 years**), which is a notable difference in this comparison.

