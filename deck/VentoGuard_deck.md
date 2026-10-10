# Stop paying for surprise gearbox failures
VentoGuard: predictive drivetrain reliability for a 120-turbine onshore wind fleet

- **€4.2 M** net annual benefit
- **+1.5 pp** technical availability
- **13 days** median early warning

Prepared for: COO (executive sponsor) · Head of Asset Management (domain owner)

---

## The outcome: turn €11 M of surprise failures into planned, cheaper repairs
- **€11.3 M/yr**: today's cost of unplanned drivetrain failures (22 failures in 192 days, repair + lost revenue)
- **€4.2 M/yr** net benefit with VentoGuard (75 % catch rate, false-alarm inspections deducted)
- **664 turbine-days** of downtime avoided per year = **+1.5 pp** technical availability
- What changes: failures are flagged 13 days ahead, so a five-week outage becomes a one-week planned swap in a low-wind window
- Evidence: 8/8 hold-out failures caught ≥3 days ahead; today's top-4 risk turbines are the 4 degrading now
- Ask: 8-week pilot on Hunsrück Höhe (availability 95.0 %)

---

## The problem in your KPIs: gearboxes and main bearings drive 90 % of the cost
| Component | Failures | Avg days down | Total cost | Per event |
|---|---|---|---|---|
| gearbox | 8 | 36.4 | €3,424 k | €428 k |
| main_bearing | 5 | 43.6 | €1,886 k | €377 k |
| generator_bearing | 5 | 11.4 | €521 k | €104 k |
| pitch_hydraulics | 4 | 3.1 | €127 k | €32 k |

- Hunsrück Höhe availability 95.0 % vs 97 % target (fleet 97.6 %)
- Each surprise gearbox costs about €430 k and 5+ weeks waiting for a crane
- Degradation was visible 2–5 weeks ahead in SCADA and in German technician notes, but nobody combined them
- SCADA threshold alarms fire too late

---

## Monday 07:00: what the reliability lead sees
1. Risk board (Lakebase): 3 CRITICAL, 1 HIGH turbines, each with likely component and € at stake
2. AI maintenance brief for F03-T07: "F03-T07 Gearbox Bearing Failure Imminent Within Days". Gearbox bearing temperature is elevated +6.09°C above fleet average and vibration increased +1.58mm/s, consistent with technician observations of metallic noise and oil analysis showing elevated iron content and particles on 2026-10-03 and 2026-10-04. Power curve ratio has degraded -0.05 vs fleet over 7 days, indicating mechanical deterioration. Business case: Planned intervention avoids EUR 206,523 in additional damage costs versus unplanned failure (EUR 385,000 corrective vs EUR 205,000 planned repair).
3. One click → work order written to Lakebase
4. Asset manager asks Genie in plain language and sees the SQL behind the answer

---

## Proof
Back-test (hold-out Aug–Sep):
| Turbine | Component | Failed | First alert |
|---|---|---|---|
| F01-T06 | gearbox | 2026-08-08 | 7 days ahead |
| F03-T04 | gearbox | 2026-08-06 | 5 days ahead |
| F03-T28 | gearbox | 2026-08-15 | 14 days ahead |
| F01-T21 | gearbox | 2026-08-28 | 14 days ahead |
| F01-T27 | main_bearing | 2026-09-15 | 14 days ahead |
| F03-T12 | generator_bearing | 2026-09-21 | 13 days ahead |
| F04-T04 | generator_bearing | 2026-08-13 | 12 days ahead |
| F01-T25 | pitch_hydraulics | 2026-09-04 | 13 days ahead |

ROC-AUC 0.999, PR-AUC 0.94, precision 81 %, 13 false-alarm turbine-weeks.

Live check vs hidden future failures:
| Turbine | Will fail | When | VentoGuard today |
|---|---|---|---|
| F03-T09 | gearbox | in 4 d | CRITICAL (99 %) |
| F03-T07 | gearbox | in 10 d | CRITICAL (100 %) |
| F01-T20 | gearbox | in 14 d | CRITICAL (96 %) |
| F04-T16 | main_bearing | in 19 d | HIGH (55 %) |

Caveat: synthetic data; expect lower precision on real fleet data, so the value case assumes a 75 % catch rate.

---

## For the COO: €4 M+ a year, paid back within one quarter
| Value driver (annualised) | € |
|---|---|
| Unplanned failure cost today | €11.3 M |
| Avoidable at 100 % catch | €5.8 M |
| Avoidable at 75 % catch | €4.4 M |
| Less false-alarm inspections | −€194 k |
| **Net annual benefit** | **€4.2 M** |
| Sensitivity: 50 % caught | €2.7 M |

- EBITDA: less corrective O&M; Revenue: +1.5 pp availability; Risk: fewer disputes; Run cost: serverless + scale-to-zero, payback within the first avoided gearbox

---

## For the Head of Asset Management: from firefighting to a planned maintenance calendar
- 13-day horizon matches crane booking, spare-pool and weather-window lead times
- Explainable: component + top-3 sensor residuals vs fleet
- 519 German/English technician notes classified by an LLM (component, severity, precursor)
- One workflow: risk board → AI brief → work order
- Genie self-service: availability, cost by component, supplier and age cohorts
- KPIs: technical availability, MTTR, corrective/planned ratio, O&M €/MWh, all from governed gold tables
- Insight: older Hansa Drives gearboxes in Hunsrück fail disproportionately often

---

## How it works: one governed platform
Lakeflow (Auto Loader + declarative pipeline, expectations) → Unity Catalog (tags, GDPR mask, lineage, grants) → ML + GenAI (MLflow model in UC with champion gate; ai_query + Claude for notes and briefs) → Lakebase (synced tables + transactional work orders) → Databricks App (React + FastAPI) + Genie space.
Orchestrated by one Lakeflow Job, deployed via Declarative Automation Bundle, scheduled daily 05:00 CET.

---

## Trust by design
- Data quality: expectations dropped 7,717 bad readings
- GDPR: technician names tagged class.name + UC column mask
- Model governance: quality gate before @champion
- Grounded GenAI: briefs only from score, residuals and notes; tagged ai_generated
- Lineage: raw Volume → risk board
- Least privilege for the app service principal

---

## Next step: an 8-week pilot on Hunsrück Höhe
| Weeks | Milestone |
|---|---|
| 1–2 | Connect SCADA + SAP PM/CMMS via Lakeflow Connect, replay 24 months |
| 3–4 | Retrain on real failures, calibrate with reliability lead, add CMS spectra |
| 5–8 | Live shadow mode with field verdict on every alert |
| 8 | Go/no-go on measured precision, lead time, € avoided |

Success criteria: ≥60 % of major failures flagged ≥7 days ahead; ≤1 false alarm / 10 turbines / month; ≥1 documented planned-instead-of-unplanned repair; daily app use.
Decisions needed: sponsor + pilot farm; 24 months of SCADA/CMMS exports.
