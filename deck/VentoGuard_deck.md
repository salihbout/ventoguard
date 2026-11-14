# Stop paying for surprise gearbox failures
VentoGuard: predictive drivetrain reliability for a 120-turbine onshore wind fleet

- **€4.2 M** net annual benefit
- **+1.5 pp** technical availability
- **13 days** median early warning

Prepared for: COO (executive sponsor) · Head of Asset Management (domain owner)

---

_Setting the scene_

## Why we're here: 120 turbines, €11 M a year of surprises, and a 30-minute look at the fix
**Customer:** German onshore wind operator, 4 farms / 120 turbines. In the room: COO (EBITDA, availability) and Head of Asset Management (O&M, maintenance calendar).

**Problem:** unplanned gearbox and bearing failures cost €11.3 M/yr; Hunsrück Höhe at 95.0 % availability vs 97 % target; warning signs sat in SCADA and technician notes, never combined.

**Agenda:** (1) outcome and € case, 3 min; (2) live demo, Monday morning from alert to booked repair, 8 min; (3) proof, value per stakeholder, architecture, 5 min; (4) questions, then one decision: an 8-week pilot on Hunsrück Höhe.

---

_The outcome_

## The outcome: turn €11 M of surprise failures into planned, cheaper repairs
- **€11.3 M/yr**: today's cost of unplanned drivetrain failures (22 failures in 192 days, repair + lost revenue)
- **€4.2 M/yr** net benefit with VentoGuard (75 % catch rate, false-alarm inspections deducted)
- **664 turbine-days** of downtime avoided per year = **+1.5 pp** technical availability
- What changes: failures are flagged 13 days ahead, so a five-week outage becomes a one-week planned swap in a low-wind window
- Evidence: 8/8 hold-out failures caught ≥3 days ahead; today's top-4 risk turbines are the 4 degrading now
- Ask: 8-week pilot on Hunsrück Höhe (availability 95.0 %)

---

_The problem_

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

_Live demo · what you'll see_

## What I'll show you: Monday 07:00 at the reliability desk
1. Risk board (Lakebase): 3 CRITICAL, 1 HIGH turbines, each with likely component and € at stake
2. AI maintenance brief for F03-T07: "F03-T07 Gearbox Imminent Failure: 99.5% Probability Within 14 Days". Gearbox intermediate stage shows critical degradation with vibration elevated +1.58mm/s, bearing temperature +6.09°C above fleet average, and power curve ratio reduced by -0.05. Technician reports confirm metallic whine, high oil temperature, and elevated iron content with particles in oil. Business case: Planned intervention avoids EUR 206,523 in additional costs versus unplanned failure (EUR 385,000 corrective vs EUR 205,000 planned repair).
3. One click → work order written to Lakebase
4. Asset manager asks Genie in plain language and sees the SQL behind the answer

---

_Live demo · what it means_

## What you just saw: a five-week surprise turned into a planned one-week job, in four clicks
| What you saw | What it changes | KPI it moves |
|---|---|---|
| Risk board: 3 critical, 1 high, ranked by € | Week starts with the 4 turbines that matter | Availability; €806 k avoidable if acted on now |
| AI brief for F03-T07 | Decision in minutes, not a morning of digging | ~€207 k saved by planned vs unplanned repair |
| One-click work order (Lakebase) | Crane, spare and crew booked into a low-wind window | Corrective/planned ratio; MTTR |
| Genie question with SQL shown | Self-service fleet answers, no BI backlog | Time to insight; supplier/retrofit decisions |

Across the fleet: €4.2 M/yr net, +1.5 pp availability.

---

_Proof_

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

_Value · executive sponsor_

## For the COO: €4 M+ a year net, and the first avoided gearbox pays for the platform
| Value driver (annualised) | € |
|---|---|
| Unplanned failure cost today | €11.3 M |
| Avoidable at 100 % catch | €5.8 M |
| Avoidable at 75 % catch | €4.4 M |
| Less false-alarm inspections | −€194 k |
| **Net annual benefit** | **€4.2 M** |
| Sensitivity: 50 % caught | €2.7 M |

- EBITDA: less corrective O&M; Revenue: +1.5 pp availability; Risk: fewer disputes; Run cost: serverless + scale-to-zero, measured in the pilot; one avoided gearbox (≈ €430 k) covers it

---

_Value · domain owner_

## For the Head of Asset Management: from firefighting to a planned maintenance calendar
- 13-day horizon matches crane booking, spare-pool and weather-window lead times
- Explainable: component + top-3 sensor residuals vs fleet
- 519 German/English technician notes classified by an LLM (component, severity, precursor)
- One workflow: risk board → AI brief → work order
- Genie self-service: availability, cost by component, supplier and age cohorts
- KPIs: technical availability, MTTR, corrective/planned ratio, O&M €/MWh, all from governed gold tables
- Insight: older Hansa Drives gearboxes in Hunsrück fail disproportionately often

---

_How it works_

## How it works: one governed platform
Lakeflow (Auto Loader + declarative pipeline, expectations) → Unity Catalog (bronze / silver / gold / serving schemas; tags, GDPR mask, lineage, grants) → ML + GenAI (MLflow model in UC with champion gate; ai_query + Claude for notes and briefs) → Lakebase (synced tables + transactional work orders) → Databricks App (React + FastAPI) + Genie space.
Orchestrated by one Lakeflow Job, deployed via Declarative Automation Bundle, scheduled daily 05:00 CET.

---

_Trust_

## Trust by design
- Data quality: expectations dropped 7,717 bad readings
- GDPR: technician names tagged class.name + UC column mask
- Model governance: quality gate before @champion
- Grounded GenAI: briefs only from score, residuals and notes; tagged ai_generated
- Lineage: raw Volume → risk board
- Least privilege for the app service principal

---

_The ask_

## Next step: an 8-week pilot on Hunsrück Höhe
| Weeks | Milestone |
|---|---|
| 1–2 | Connect SCADA + SAP PM/CMMS via Lakeflow Connect, replay 24 months |
| 3–4 | Retrain on real failures, calibrate with reliability lead, add CMS spectra |
| 5–8 | Live shadow mode with field verdict on every alert |
| 8 | Go/no-go on measured precision, lead time, € avoided |

Success criteria: ≥60 % of major failures flagged ≥7 days ahead; ≤1 false alarm / 10 turbines / month; ≥1 documented planned-instead-of-unplanned repair; daily app use.
Decisions needed: sponsor + pilot farm; 24 months of SCADA/CMMS exports.

---

_Appendix · business questions_

## Backup: cost, risk and time to value
- **Cost:** serverless jobs + SQL, scale-to-zero Lakebase, one app; no always-on cluster. Exact run cost measured in the pilot from billing system tables. One avoided gearbox ≈ €430 k. Downside (50 % caught): €2.7 M/yr.
- **Risk:** precision lower on real data → value case assumes 75 %, shadow mode with field verdicts; alert fatigue → tiers + € ranking, target ≤1 false alarm/10 turbines/month; adoption → work order in the same screen, daily use is a go/no-go criterion.
- **Time to value:** weeks 1–2 data connected; week 5 first live alerts; week 8 go/no-go; then same bundle to all 4 farms (configuration, not rebuild).

---

_Appendix · technical questions_

## Backup: architecture and integration
- Ingest: Auto Loader from UC Volume; production = SCADA historian (file drops or Zerobus), SAP PM/CMMS via Lakeflow Connect
- Transform: Lakeflow declarative pipeline bronze → silver → gold, expectations at silver, incremental streaming tables
- Serve: gold → Lakebase synced tables (snapshot after daily scoring); app writes work orders to its own `vg_ops` schema; pilot pushes work orders to SAP PM (system of record)
- Orchestration: one Lakeflow Job, 6 tasks, daily 05:00 CET, deployed via Declarative Automation Bundle (dev/prod targets)
- Scale: ~3.3 M rows of 10-minute SCADA, aggregated to turbine-day features; more turbines/sensors/CMS spectra scale out on serverless
- Freshness: daily fits the 14-day horizon; sync can go triggered/continuous
- Open formats: Delta + UC, Postgres, MLflow

---

_Appendix · technical questions_

## Backup: data quality, model validation and GenAI guard-rails
- Data quality: expectations drop impossible readings (7,717 this run), visible in the event log; fleet-relative features remove weather/seasonality effects
- Model: gradient-boosted 14-day classifier, time-split validation (train < Aug, test Aug–Sep), quality gate (PR-AUC ≥ 0.30, ≥ 60 % caught ≥ 3 d ahead) before @champion; metrics + back-test logged in MLflow; pilot adds drift monitoring + monthly retrain
- GenAI: Claude via Databricks Foundation Model APIs (`ai_query`); grounded on score, residuals and the technician's notes; no invented numbers; tagged `ai_generated`; a human approves every work order
- Security: UC grants + lineage; technician names tagged `class.name` and masked in every tool incl. Genie; app runs as least-privilege service principal
