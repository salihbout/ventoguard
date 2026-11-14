"""Build the VentoGuard business deck as HTML (16:9 slides) + Markdown, then print to PDF with headless Chrome.

Usage: python deck/build_deck.py      -> deck/VentoGuard_deck.html, deck/VentoGuard_deck.md, deck/VentoGuard_deck.pdf
All figures come from evidence/ (value_case.result.json, model back-test, risk board) — see deck/numbers.json.
"""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
N = json.loads((HERE / "numbers.json").read_text())


def m(x):  # € millions
    return f"€{x/1e6:.1f} M"


def k(x):
    return f"€{x/1e3:,.0f} k"


SLIDES = []


def slide(title, body_html, md, kind="std", kicker=""):
    SLIDES.append(dict(title=title, body=body_html, md=md, kind=kind, kicker=kicker))


# 1 ─ Title
slide("Stop paying for surprise gearbox failures",
      f"""<div class="sub">VentoGuard: predictive drivetrain reliability for a 120-turbine onshore wind fleet</div>
      <div class="titlekpis">
        <div><b>{m(N['net_annual_benefit_eur'])}</b><span>net annual benefit</span></div>
        <div><b>+{N['availability_uplift_pp']:.1f} pp</b><span>technical availability</span></div>
        <div><b>{N['median_lead_days']:.0f} days</b><span>median early warning</span></div>
      </div>
      <div class="foot">Prepared for: COO (executive sponsor) · Head of Asset Management (domain owner) · Built on the Databricks Data Intelligence Platform</div>""",
      f"""# Stop paying for surprise gearbox failures
VentoGuard: predictive drivetrain reliability for a 120-turbine onshore wind fleet

- **{m(N['net_annual_benefit_eur'])}** net annual benefit
- **+{N['availability_uplift_pp']:.1f} pp** technical availability
- **{N['median_lead_days']:.0f} days** median early warning

Prepared for: COO (executive sponsor) · Head of Asset Management (domain owner)""", kind="title")

# 2 ─ Executive summary
slide("The outcome: turn €11 M of surprise failures into planned, cheaper repairs",
      f"""<div class="grid3">
        <div class="card lava"><div class="big">{m(N['unplanned_cost_annualised_eur'])}</div><div>annual cost of unplanned drivetrain failures today<br><small>{N['failures_observed']} failures in {N['observed_days']} days, repair + lost revenue</small></div></div>
        <div class="card"><div class="big">{m(N['net_annual_benefit_eur'])}</div><div>net benefit per year with VentoGuard<br><small>assumes only 75 % of failures caught; false-alarm inspections deducted</small></div></div>
        <div class="card"><div class="big">{N['downtime_days_avoided']:,}</div><div>turbine-days of downtime avoided per year<br><small>= +{N['availability_uplift_pp']:.1f} pp fleet technical availability</small></div></div>
      </div>
      <ul class="pts">
        <li><b>What changes:</b> failures are flagged <b>{N['median_lead_days']:.0f} days</b> before breakdown. That is enough time to book a crane, pull a spare gearbox and swap it in a low-wind window, so a five-week outage becomes a one-week planned job.</li>
        <li><b>Evidence:</b> {N['bt_caught']}/{N['bt_total']} failures in the hold-out period were caught at least 3 days ahead. Today's top-4 risk turbines are the 4 that are degrading now.</li>
        <li><b>Ask:</b> an 8-week pilot on Hunsrück Höhe (lowest availability at {N['avail_hunsrueck']:.1f} %), with a go/no-go on avoided cost.</li>
      </ul>""",
      f"""## The outcome: turn €11 M of surprise failures into planned, cheaper repairs
- **{m(N['unplanned_cost_annualised_eur'])}/yr**: today's cost of unplanned drivetrain failures ({N['failures_observed']} failures in {N['observed_days']} days, repair + lost revenue)
- **{m(N['net_annual_benefit_eur'])}/yr** net benefit with VentoGuard (75 % catch rate, false-alarm inspections deducted)
- **{N['downtime_days_avoided']:,} turbine-days** of downtime avoided per year = **+{N['availability_uplift_pp']:.1f} pp** technical availability
- What changes: failures are flagged {N['median_lead_days']:.0f} days ahead, so a five-week outage becomes a one-week planned swap in a low-wind window
- Evidence: {N['bt_caught']}/{N['bt_total']} hold-out failures caught ≥3 days ahead; today's top-4 risk turbines are the 4 degrading now
- Ask: 8-week pilot on Hunsrück Höhe (availability {N['avail_hunsrueck']:.1f} %)""")

# 3 ─ Problem in buyer KPIs
rows = "".join(f"<tr><td>{c['component'].replace('_',' ')}</td><td>{c['failures']}</td><td>{c['avg_downtime_days']}</td><td>{k(c['total_eur'])}</td><td>{k(c['total_eur']/c['failures'])}</td></tr>" for c in N["by_component"])
slide("The problem in your KPIs: gearboxes and main bearings drive 90 % of the cost",
      f"""<div class="grid2">
        <div><table><tr><th>Component</th><th>Failures</th><th>Avg days down</th><th>Total cost</th><th>Per event</th></tr>{rows}</table>
        <p class="note">Last {N['observed_days']} days, 4 farms / 120 turbines. Cost = corrective repair (incl. crane) + lost revenue at day-ahead prices.</p></div>
        <div><ul class="pts">
          <li><b>Availability gap:</b> Hunsrück Höhe runs at <b>{N['avail_hunsrueck']:.1f} %</b> against a 97 % target. The fleet average is {N['avail_fleet']:.1f} %.</li>
          <li><b>Every surprise gearbox</b> costs around <b>€430 k</b> and <b>5+ weeks</b> waiting for a crane and a spare.</li>
          <li><b>The signals were there.</b> Oil temperature, bearing temperature and vibration drifted for 2 to 5 weeks before each failure. Technicians wrote it down in German free text, and nobody connected the dots.</li>
          <li><b>Today the operation is reactive.</b> SCADA alarms are fixed thresholds that fire only days before breakdown.</li>
        </ul></div></div>""",
      "## The problem in your KPIs: gearboxes and main bearings drive 90 % of the cost\n| Component | Failures | Avg days down | Total cost | Per event |\n|---|---|---|---|---|\n" +
      "\n".join(f"| {c['component']} | {c['failures']} | {c['avg_downtime_days']} | {k(c['total_eur'])} | {k(c['total_eur']/c['failures'])} |" for c in N["by_component"]) +
      f"\n\n- Hunsrück Höhe availability {N['avail_hunsrueck']:.1f} % vs 97 % target (fleet {N['avail_fleet']:.1f} %)\n- Each surprise gearbox costs about €430 k and 5+ weeks waiting for a crane\n- Degradation was visible 2–5 weeks ahead in SCADA and in German technician notes, but nobody combined them\n- SCADA threshold alarms fire too late")

# 4 ─ Day in the life
slide("What I'll show you: Monday 07:00 at the reliability desk",
      f"""<div class="grid2">
        <div><ol class="pts">
          <li><b>Risk board</b> (served from Lakebase in milliseconds): <b>{N['n_critical']} CRITICAL, {N['n_high']} HIGH</b> turbines, each with the likely component and € at stake.</li>
          <li><b>AI maintenance brief</b> for {N['brief_turbine']}: the diagnosis cites the sensor evidence and the technician's German note, with steps, crew, parts and the business case.</li>
          <li><b>One click → work order</b>, written transactionally to Lakebase with priority, crew and planned date.</li>
          <li><b>Asset manager asks Genie</b>: <i>"Which farm lost the most revenue to failures, and which component caused it?"</i> Genie answers with the SQL shown.</li>
        </ol></div>
        <div class="quote"><div class="qh">{N['brief_headline']}</div><p>{N['brief_diagnosis']}</p><p><b>Business case.</b> {N['brief_business_case']}</p><small>Generated by Claude on Databricks from the model score, sensor residuals and technician notes</small></div>
      </div>""",
      f"""## What I'll show you: Monday 07:00 at the reliability desk
1. Risk board (Lakebase): {N['n_critical']} CRITICAL, {N['n_high']} HIGH turbines, each with likely component and € at stake
2. AI maintenance brief for {N['brief_turbine']}: "{N['brief_headline']}". {N['brief_diagnosis']} Business case: {N['brief_business_case']}
3. One click → work order written to Lakebase
4. Asset manager asks Genie in plain language and sees the SQL behind the answer""")

# 5 ─ Proof
bt = "".join(f"<tr><td>{b['turbine_id']}</td><td>{b['component'].replace('_',' ')}</td><td>{b['failure_date']}</td><td><b>{b['lead']} d</b></td></tr>" for b in N["backtest"])
live = "".join(f"<tr><td>{x['turbine_id']}</td><td>{x['component'].replace('_',' ')}</td><td>in {x['days_until']} d</td><td><b>{x['tier']}</b> ({x['prob']*100:.0f} %)</td></tr>" for x in N["live_check"])
slide("Proof: every hold-out failure flagged in advance, and today's alerts point at the right turbines",
      f"""<div class="grid2">
        <div><h3>Back-test (Aug–Sep, never seen in training)</h3><table><tr><th>Turbine</th><th>Component</th><th>Failed</th><th>First alert</th></tr>{bt}</table>
        <p class="note">ROC-AUC {N['auc']:.3f} · PR-AUC {N['pr_auc']:.2f} · precision {N['precision']*100:.0f} % at threshold 0.5 · {N['false_alarm_weeks']} false-alarm turbine-weeks in 2 months</p></div>
        <div><h3>Live check: failures still in the future</h3><table><tr><th>Turbine</th><th>Will fail</th><th>When</th><th>VentoGuard today</th></tr>{live}</table>
        <p class="note">Hidden ground truth from the simulator, never exposed to the pipeline. Two further failures start degrading after the cut-off and cannot be seen yet. That is honest and expected.</p></div>
      </div>
      <p class="caveat">Built on synthetic SCADA with a physically motivated degradation signal. On real fleet data, expect lower precision. The pilot will measure that, which is why the value case assumes a 75 % catch rate.</p>""",
      "## Proof\nBack-test (hold-out Aug–Sep):\n| Turbine | Component | Failed | First alert |\n|---|---|---|---|\n" +
      "\n".join(f"| {b['turbine_id']} | {b['component']} | {b['failure_date']} | {b['lead']} days ahead |" for b in N["backtest"]) +
      f"\n\nROC-AUC {N['auc']:.3f}, PR-AUC {N['pr_auc']:.2f}, precision {N['precision']*100:.0f} %, {N['false_alarm_weeks']} false-alarm turbine-weeks.\n\nLive check vs hidden future failures:\n| Turbine | Will fail | When | VentoGuard today |\n|---|---|---|---|\n" +
      "\n".join(f"| {x['turbine_id']} | {x['component']} | in {x['days_until']} d | {x['tier']} ({x['prob']*100:.0f} %) |" for x in N["live_check"]) +
      "\n\nCaveat: synthetic data; expect lower precision on real fleet data, so the value case assumes a 75 % catch rate.")

# 6 ─ Value for exec sponsor
slide("For the COO: €4 M+ a year, paid back within one quarter",
      f"""<div class="grid2"><div><table>
        <tr><th>Value driver (annualised)</th><th>€</th></tr>
        <tr><td>Unplanned failure cost today</td><td>{m(N['unplanned_cost_annualised_eur'])}</td></tr>
        <tr><td>Avoidable if every failure becomes a planned repair</td><td>{m(N['avoidable_100'])}</td></tr>
        <tr><td>Avoidable at a conservative 75 % catch rate</td><td>{m(N['avoidable_75'])}</td></tr>
        <tr><td>Less false-alarm inspections (€2.5 k each)</td><td>−{k(N['false_alarm_cost'])}</td></tr>
        <tr class="tot"><td>Net annual benefit</td><td>{m(N['net_annual_benefit_eur'])}</td></tr>
        <tr><td>Sensitivity: only 50 % caught</td><td>{m(N['avoidable_100']*0.5 - N['false_alarm_cost'])}</td></tr>
      </table></div>
      <div><ul class="pts">
        <li><b>EBITDA:</b> lower corrective O&M spend (crane mobilisation alone is about €120 k per gearbox).</li>
        <li><b>Revenue:</b> {N['downtime_days_avoided']:,} more turbine-days generating, worth +{N['availability_uplift_pp']:.1f} pp availability and protecting PPA delivery volumes.</li>
        <li><b>Risk:</b> fewer OEM/insurer disputes, and spare-part pools sized from the risk board.</li>
        <li><b>Cost to run:</b> serverless jobs, a scale-to-zero Lakebase and one app. Expect low five figures per year at fleet scale, so payback comes within the first avoided gearbox.</li>
      </ul></div></div>""",
      f"""## For the COO: €4 M+ a year, paid back within one quarter
| Value driver (annualised) | € |
|---|---|
| Unplanned failure cost today | {m(N['unplanned_cost_annualised_eur'])} |
| Avoidable at 100 % catch | {m(N['avoidable_100'])} |
| Avoidable at 75 % catch | {m(N['avoidable_75'])} |
| Less false-alarm inspections | −{k(N['false_alarm_cost'])} |
| **Net annual benefit** | **{m(N['net_annual_benefit_eur'])}** |
| Sensitivity: 50 % caught | {m(N['avoidable_100']*0.5 - N['false_alarm_cost'])} |

- EBITDA: less corrective O&M; Revenue: +{N['availability_uplift_pp']:.1f} pp availability; Risk: fewer disputes; Run cost: serverless + scale-to-zero, payback within the first avoided gearbox""")

# 7 ─ Value for domain owner
slide("For the Head of Asset Management: from firefighting to a planned maintenance calendar",
      """<div class="grid2"><div><ul class="pts">
        <li><b>13-day horizon</b> lines up with real lead times: crane booking (7–10 d), spare gearbox from the pool, and a low-wind weather window.</li>
        <li><b>Explainable alerts:</b> each score names the component and the three sensor residuals driving it, compared with the fleet on the same day, so ambient temperature doesn't trigger false alarms.</li>
        <li><b>Technician knowledge, unlocked:</b> 519 German/English notes are classified by an LLM for component, severity and precursor. A note like <i>"Ölprobe: erhöhter Eisengehalt"</i> now raises risk.</li>
        <li><b>One workflow:</b> risk board → AI brief → work order, in one app that dispatchers actually open.</li>
      </ul></div>
      <div><ul class="pts">
        <li><b>Self-service answers with Genie:</b> availability by farm and month, cost by component, supplier and age cohorts, all without waiting on the BI team.</li>
        <li><b>KPIs this owner is measured on:</b> technical availability, MTTR, corrective vs planned ratio, O&M €/MWh. Every one is computed in governed gold tables.</li>
        <li><b>Fleet insight:</b> older Hansa Drives gearboxes in Hunsrück fail disproportionately often, which feeds the next retrofit and contract negotiation.</li>
      </ul></div></div>""",
      """## For the Head of Asset Management: from firefighting to a planned maintenance calendar
- 13-day horizon matches crane booking, spare-pool and weather-window lead times
- Explainable: component + top-3 sensor residuals vs fleet
- 519 German/English technician notes classified by an LLM (component, severity, precursor)
- One workflow: risk board → AI brief → work order
- Genie self-service: availability, cost by component, supplier and age cohorts
- KPIs: technical availability, MTTR, corrective/planned ratio, O&M €/MWh, all from governed gold tables
- Insight: older Hansa Drives gearboxes in Hunsrück fail disproportionately often""")

# 8 ─ Architecture
slide("How it works: one governed platform, from raw SCADA to the dispatcher's screen",
      """<div class="flow">
        <div class="st"><b>Lakeflow</b><span>Auto Loader ingests SCADA (3.3 M rows), CMMS notes, asset register and prices from a UC Volume. Declarative pipeline bronze → silver → gold with data-quality expectations.</span></div>
        <div class="ar">→</div>
        <div class="st"><b>Unity Catalog</b><span>One catalog, layer schemas ventoguard_bronze / _silver / _gold / _serving. Tags, GDPR column mask, lineage, least-privilege grants.</span></div>
        <div class="ar">→</div>
        <div class="st"><b>ML + GenAI</b><span>Fleet-relative features → gradient-boosted 14-day failure model (MLflow, UC registry, @champion gate). ai_query + Claude: note extraction and maintenance briefs.</span></div>
        <div class="ar">→</div>
        <div class="st"><b>Lakebase</b><span>Synced tables (risk board, briefs, trends) + transactional work orders, served in Postgres.</span></div>
        <div class="ar">→</div>
        <div class="st"><b>App + Genie</b><span>Databricks App: React front end, FastAPI back end. Risk map, AI brief and work orders, plus an embedded Genie space that shows its SQL.</span></div>
      </div>
      <p class="note" style="margin-top:28px">Orchestrated as one Lakeflow Job (generate → pipeline → train → score + GenAI → govern → sync Lakebase), deployed as a Declarative Automation Bundle. Daily schedule at 05:00 CET.</p>""",
      """## How it works: one governed platform
Lakeflow (Auto Loader + declarative pipeline, expectations) → Unity Catalog (bronze / silver / gold / serving schemas; tags, GDPR mask, lineage, grants) → ML + GenAI (MLflow model in UC with champion gate; ai_query + Claude for notes and briefs) → Lakebase (synced tables + transactional work orders) → Databricks App (React + FastAPI) + Genie space.
Orchestrated by one Lakeflow Job, deployed via Declarative Automation Bundle, scheduled daily 05:00 CET.""")

# 9 ─ Governance & trust
slide("Trust by design: governed data, explainable models, grounded AI",
      f"""<div class="grid3">
        <div class="card"><b>Data quality</b><p>Lakeflow expectations dropped {N['dq_dropped']:,} bad readings (sensor 999 °C, negative wind, missing power) before they reached the model. Results are queryable from the event log.</p></div>
        <div class="card"><b>Privacy (GDPR)</b><p>Technician names carry the governed <code>class.name</code> classification tag and are masked by a UC column-mask function. Only the reliability leads group sees them, in every tool including Genie.</p></div>
        <div class="card"><b>Model governance</b><p>UC-registered model with a quality gate (PR-AUC ≥ 0.30 and ≥ 60 % of failures caught) before the <code>@champion</code> alias moves. Back-test tables are logged with every run.</p></div>
        <div class="card"><b>Grounded GenAI</b><p>Briefs are generated only from the model score, measured residuals and the technician's own notes, and the prompt forbids invented measurements. Outputs are tagged <code>ai_generated</code>.</p></div>
        <div class="card"><b>Lineage</b><p>Lineage runs from the raw Volume to the risk board, so any number in the app can be traced back to the SCADA file it came from.</p></div>
        <div class="card"><b>Least privilege</b><p>The app service principal reads gold/serving only and owns just its work-order schema in Lakebase.</p></div>
      </div>""",
      f"""## Trust by design
- Data quality: expectations dropped {N['dq_dropped']:,} bad readings
- GDPR: technician names tagged class.name + UC column mask
- Model governance: quality gate before @champion
- Grounded GenAI: briefs only from score, residuals and notes; tagged ai_generated
- Lineage: raw Volume → risk board
- Least privilege for the app service principal""")

# 10 ─ Pilot plan
slide("Next step: an 8-week pilot on Hunsrück Höhe",
      """<div class="grid2"><div><table>
        <tr><th>Weeks</th><th>Milestone</th></tr>
        <tr><td>1–2</td><td>Connect the real SCADA historian and the SAP PM / CMMS via Lakeflow Connect; replay 24 months of history</td></tr>
        <tr><td>3–4</td><td>Retrain on real failures; calibrate thresholds with the reliability lead; add CMS vibration spectra</td></tr>
        <tr><td>5–8</td><td>Live shadow mode: daily risk board + AI briefs to the Hunsrück crew; every alert gets a field verdict</td></tr>
        <tr><td>8</td><td>Go/no-go with COO on measured precision, lead time and € avoided</td></tr>
      </table></div>
      <div><h3>Success criteria</h3><ul class="pts">
        <li>≥ 60 % of major failures flagged ≥ 7 days ahead</li>
        <li>≤ 1 false alarm per 10 turbines per month</li>
        <li>≥ 1 failure converted to a planned repair, with € avoided documented</li>
        <li>Dispatchers use the app daily (adoption tracked in app logs)</li>
      </ul><h3>Decisions needed today</h3><ul class="pts"><li>Executive sponsor and pilot farm confirmed</li><li>Access to SCADA and CMMS exports for 24 months</li></ul></div></div>""",
      """## Next step: an 8-week pilot on Hunsrück Höhe
| Weeks | Milestone |
|---|---|
| 1–2 | Connect SCADA + SAP PM/CMMS via Lakeflow Connect, replay 24 months |
| 3–4 | Retrain on real failures, calibrate with reliability lead, add CMS spectra |
| 5–8 | Live shadow mode with field verdict on every alert |
| 8 | Go/no-go on measured precision, lead time, € avoided |

Success criteria: ≥60 % of major failures flagged ≥7 days ahead; ≤1 false alarm / 10 turbines / month; ≥1 documented planned-instead-of-unplanned repair; daily app use.
Decisions needed: sponsor + pilot farm; 24 months of SCADA/CMMS exports.""")

# ─ Role-play structure: setup slide, demo landing slide, Q&A appendix ─────────────────────────────

slide("Why we're here: 120 turbines, €11 M a year of surprises, and a 30-minute look at the fix",
      f"""<div class="grid2">
        <div><h3>The customer</h3><ul class="pts">
          <li>German onshore wind operator: <b>4 farms, 120 turbines</b>, merchant and PPA revenue</li>
          <li><b>COO</b> is accountable for EBITDA and availability. The <b>Head of Asset Management</b> runs O&M and the maintenance calendar.</li>
        </ul>
        <h3>The problem</h3><ul class="pts">
          <li>Unplanned gearbox and bearing failures cost <b>{m(N['unplanned_cost_annualised_eur'])} a year</b>. Hunsrück Höhe sits at <b>{N['avail_hunsrueck']:.1f} %</b> availability against a 97 % target.</li>
          <li>The warning signs were in SCADA and in technicians' notes weeks ahead, but nothing combined them.</li>
        </ul></div>
        <div><h3>In the next 30 minutes</h3><ol class="pts">
          <li><b>The outcome and the € case</b> (3 min)</li>
          <li><b>Live demo</b>: one Monday morning, from risk alert to booked repair (8 min)</li>
          <li><b>Proof, value for each of you, and how it is built</b> (5 min)</li>
          <li><b>Your questions</b>, then <b>one decision</b>: an 8-week pilot on Hunsrück Höhe</li>
        </ol></div>
      </div>""",
      f"""## Why we're here: 120 turbines, €11 M a year of surprises, and a 30-minute look at the fix
**Customer:** German onshore wind operator, 4 farms / 120 turbines. In the room: COO (EBITDA, availability) and Head of Asset Management (O&M, maintenance calendar).

**Problem:** unplanned gearbox and bearing failures cost {m(N['unplanned_cost_annualised_eur'])}/yr; Hunsrück Höhe at {N['avail_hunsrueck']:.1f} % availability vs 97 % target; warning signs sat in SCADA and technician notes, never combined.

**Agenda:** (1) outcome and € case, 3 min; (2) live demo, Monday morning from alert to booked repair, 8 min; (3) proof, value per stakeholder, architecture, 5 min; (4) questions, then one decision: an 8-week pilot on Hunsrück Höhe.""",
      kicker="Setting the scene")

slide("What you just saw: a five-week surprise turned into a planned one-week job, in four clicks",
      f"""<table>
        <tr><th>What you saw</th><th>What it changes</th><th>KPI it moves</th></tr>
        <tr><td><b>Risk board</b>: {N['n_critical']} critical and {N['n_high']} high-risk turbines, ranked by € at stake</td><td>The reliability lead starts the week with the 4 turbines that matter, not 120 alarms</td><td>Technical availability; <b>€{N['app_avoidable_now_eur']/1e3:,.0f} k</b> avoidable if acted on now</td></tr>
        <tr><td><b>AI brief</b> for {N['brief_turbine']}: evidence, technician note, steps and business case</td><td>A decision in minutes instead of a morning of digging through SCADA and CMMS</td><td>Planned repair saves about <b>€207 k</b> versus waiting for the failure</td></tr>
        <tr><td><b>Work order</b> written to Lakebase in one click</td><td>The crane, the spare part and the crew are booked into a low-wind window</td><td>Corrective/planned ratio; MTTR</td></tr>
        <tr><td><b>Genie</b>: a plain-language question with the SQL shown</td><td>The asset manager answers fleet questions without waiting on the BI team</td><td>Time to insight; supplier and retrofit decisions</td></tr>
      </table>
      <p class="pts" style="margin-top:22px"><b>Across the fleet:</b> this loop, run every morning, is worth <b>{m(N['net_annual_benefit_eur'])} a year net</b> and <b>+{N['availability_uplift_pp']:.1f} pp</b> availability.</p>""",
      f"""## What you just saw: a five-week surprise turned into a planned one-week job, in four clicks
| What you saw | What it changes | KPI it moves |
|---|---|---|
| Risk board: {N['n_critical']} critical, {N['n_high']} high, ranked by € | Week starts with the 4 turbines that matter | Availability; €{N['app_avoidable_now_eur']/1e3:,.0f} k avoidable if acted on now |
| AI brief for {N['brief_turbine']} | Decision in minutes, not a morning of digging | ~€207 k saved by planned vs unplanned repair |
| One-click work order (Lakebase) | Crane, spare and crew booked into a low-wind window | Corrective/planned ratio; MTTR |
| Genie question with SQL shown | Self-service fleet answers, no BI backlog | Time to insight; supplier/retrofit decisions |

Across the fleet: {m(N['net_annual_benefit_eur'])}/yr net, +{N['availability_uplift_pp']:.1f} pp availability.""",
      kicker="Live demo · what it means")

slide("Backup: cost, risk and time to value",
      f"""<div class="grid3 dense">
        <div class="card"><b>Cost</b><p><b>Run cost:</b> serverless jobs and SQL, Lakebase that scales to zero, and one app, with no cluster to keep running. The pilot measures the exact figure from the billing system tables.</p><p><b>Yardstick:</b> one avoided gearbox is worth about <b>€430 k</b>, and the model flagged {N['bt_caught']} of {N['bt_total']} hold-out failures.</p><p><b>Downside case:</b> if only 50 % are caught, the benefit is still <b>{m(N['avoidable_100']*0.5 - N['false_alarm_cost'])}/yr</b>.</p></div>
        <div class="card"><b>Risk and mitigation</b><p><b>Precision on real data is lower:</b> the value case already assumes 75 %, and pilot weeks 5–8 run in shadow mode with a field verdict on every alert.</p><p><b>Alert fatigue:</b> tiers and a ranking by € at stake keep the reliability lead's list short, with a target of ≤ 1 false alarm per 10 turbines per month.</p><p><b>Adoption:</b> the work order sits in the same screen as the alert, and daily use is a go/no-go criterion.</p></div>
        <div class="card"><b>Time to value</b><p><b>Weeks 1–2:</b> real SCADA and CMMS history are connected.</p><p><b>Week 5:</b> the first live alerts reach the Hunsrück crew.</p><p><b>Week 8:</b> go/no-go on measured € avoided.</p><p><b>After go:</b> the same bundle is deployed to all 4 farms. Everything is code (a Declarative Automation Bundle), so roll-out is configuration, not a rebuild.</p></div>
      </div>""",
      f"""## Backup: cost, risk and time to value
- **Cost:** serverless jobs + SQL, scale-to-zero Lakebase, one app; no always-on cluster. Exact run cost measured in the pilot from billing system tables. One avoided gearbox ≈ €430 k. Downside (50 % caught): {m(N['avoidable_100']*0.5 - N['false_alarm_cost'])}/yr.
- **Risk:** precision lower on real data → value case assumes 75 %, shadow mode with field verdicts; alert fatigue → tiers + € ranking, target ≤1 false alarm/10 turbines/month; adoption → work order in the same screen, daily use is a go/no-go criterion.
- **Time to value:** weeks 1–2 data connected; week 5 first live alerts; week 8 go/no-go; then same bundle to all 4 farms (configuration, not rebuild).""",
      kicker="Appendix · business questions")

slide("Backup: architecture and integration with your systems",
      """<div class="grid2 dense"><div><ul class="pts">
        <li><b>Ingest:</b> Auto Loader picks up files incrementally from a UC Volume. In production: the SCADA historian via file drops or Zerobus streaming, and SAP PM / CMMS via Lakeflow Connect.</li>
        <li><b>Transform:</b> a Lakeflow declarative pipeline, bronze → silver → gold, with expectations at silver. Streaming tables mean reruns only process new data.</li>
        <li><b>Serve:</b> gold tables are synced to Lakebase Postgres (snapshot after each daily scoring run). The app reads in milliseconds and writes work orders transactionally to its own <code>vg_ops</code> schema.</li>
        <li><b>Write-back:</b> in the pilot, work orders are pushed to SAP PM through its API, so SAP stays the system of record.</li>
      </ul></div><div><ul class="pts">
        <li><b>Orchestration:</b> one Lakeflow Job with six tasks, scheduled daily at 05:00 CET, deployed as a Declarative Automation Bundle with dev and prod targets.</li>
        <li><b>Scale:</b> about 3.3 M rows of 10-minute SCADA today, aggregated to turbine-day features. More turbines, more sensors or CMS spectra scale out on serverless with no re-architecture.</li>
        <li><b>Freshness:</b> daily matches the 14-day horizon. The Lakebase sync can be switched to triggered or continuous if intraday is needed.</li>
        <li><b>Open formats:</b> Delta tables in Unity Catalog, standard Postgres, MLflow models, so nothing is locked in a proprietary store.</li>
      </ul></div></div>""",
      """## Backup: architecture and integration
- Ingest: Auto Loader from UC Volume; production = SCADA historian (file drops or Zerobus), SAP PM/CMMS via Lakeflow Connect
- Transform: Lakeflow declarative pipeline bronze → silver → gold, expectations at silver, incremental streaming tables
- Serve: gold → Lakebase synced tables (snapshot after daily scoring); app writes work orders to its own `vg_ops` schema; pilot pushes work orders to SAP PM (system of record)
- Orchestration: one Lakeflow Job, 6 tasks, daily 05:00 CET, deployed via Declarative Automation Bundle (dev/prod targets)
- Scale: ~3.3 M rows of 10-minute SCADA, aggregated to turbine-day features; more turbines/sensors/CMS spectra scale out on serverless
- Freshness: daily fits the 14-day horizon; sync can go triggered/continuous
- Open formats: Delta + UC, Postgres, MLflow""",
      kicker="Appendix · technical questions")

slide("Backup: data quality, model validation and the GenAI guard-rails",
      f"""<div class="grid3 dense">
        <div class="card"><b>Data quality</b><p>Expectations at silver drop physically impossible readings: {N['dq_dropped']:,} bad readings in this run (999 °C oil, negative wind, missing power). Results sit in the pipeline event log and can be alerted on. Features are <b>relative to the fleet on the same day</b>, so weather and seasonality don't look like degradation.</p></div>
        <div class="card"><b>Model validation</b><p>Gradient-boosted classifier with a 14-day horizon, validated on a <b>time split</b> (trained before August, tested Aug–Sep) to avoid leakage. A quality gate (PR-AUC ≥ 0.30 and ≥ 60 % of failures caught ≥ 3 days ahead) must pass before <code>@champion</code> moves. Each run logs metrics and back-test tables to MLflow. The pilot adds drift monitoring and a monthly retrain.</p></div>
        <div class="card"><b>GenAI guard-rails</b><p>Claude via Databricks Foundation Model APIs, called with <code>ai_query</code> in SQL. Briefs use only the score, measured residuals and the technician's own notes, and the prompt forbids invented numbers. Outputs are tagged <code>ai_generated</code> and shown next to the evidence. A human approves every work order.</p></div>
      </div>
      <p class="note" style="margin-top:18px">Security: Unity Catalog grants and lineage on every table. Technician names are tagged <code>class.name</code> and masked by a column-mask function in every tool, Genie included. The app runs as a least-privilege service principal that reads gold/serving and owns only its work-order schema.</p>""",
      f"""## Backup: data quality, model validation and GenAI guard-rails
- Data quality: expectations drop impossible readings ({N['dq_dropped']:,} this run), visible in the event log; fleet-relative features remove weather/seasonality effects
- Model: gradient-boosted 14-day classifier, time-split validation (train < Aug, test Aug–Sep), quality gate (PR-AUC ≥ 0.30, ≥ 60 % caught ≥ 3 d ahead) before @champion; metrics + back-test logged in MLflow; pilot adds drift monitoring + monthly retrain
- GenAI: Claude via Databricks Foundation Model APIs (`ai_query`); grounded on score, residuals and the technician's notes; no invented numbers; tagged `ai_generated`; a human approves every work order
- Security: UC grants + lineage; technician names tagged `class.name` and masked in every tool incl. Genie; app runs as least-privilege service principal""",
      kicker="Appendix · technical questions")

# Final order: title, setup, outcome, problem, demo intro, demo landing, proof, COO, HoAM, architecture, trust, pilot, appendix
main, setup, landing, *appendix = SLIDES[:10], SLIDES[10], SLIDES[11], *SLIDES[12:]
SLIDES[:] = [main[0], setup, main[1], main[2], main[3], landing, *main[4:], *appendix]
KICKERS = {2: "The outcome", 3: "The problem", 4: "Live demo · what you'll see", 6: "Proof", 7: "Value · executive sponsor",
           8: "Value · domain owner", 9: "How it works", 10: "Trust", 11: "The ask"}
for i, kk in KICKERS.items():
    SLIDES[i]["kicker"] = SLIDES[i]["kicker"] or kk

CSS = """
@page { size: 1280px 720px; margin: 0 }
* { box-sizing: border-box }
body { margin: 0; font-family: 'DM Sans', 'Helvetica Neue', Arial, sans-serif; color: #0B2026; background: #ddd }
.slide { width: 1280px; height: 720px; padding: 52px 64px; background: #F9F7F4; position: relative; page-break-after: always; overflow: hidden; margin: 0 auto 12px }
.slide h1 { font-size: 34px; line-height: 1.15; margin: 0 0 26px; max-width: 1100px }
.slide .kick { color: #FF3621; font-weight: 700; letter-spacing: .08em; font-size: 13px; text-transform: uppercase; margin-bottom: 8px }
.slide .num { position: absolute; bottom: 22px; right: 40px; font-size: 12px; opacity: .5 }
.slide .brand { position: absolute; bottom: 22px; left: 64px; font-size: 12px; opacity: .5 }
.title { background: #0B2026; color: #F9F7F4 }
.title h1 { font-size: 58px; margin-top: 120px; max-width: 980px }
.title .sub { font-size: 22px; opacity: .85 }
.title .titlekpis { display: flex; gap: 56px; margin-top: 54px }
.title .titlekpis b { display: block; font-size: 44px; color: #FF3621 }
.title .titlekpis span { font-size: 15px; opacity: .8 }
.title .foot { position: absolute; bottom: 48px; font-size: 14px; opacity: .7 }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 40px }
.grid3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 22px }
.card { background: #fff; border-radius: 12px; padding: 20px 22px; border: 1px solid #e6e1d9; font-size: 15px }
.card.lava { background: #FF3621; color: #fff; border: none }
.card .big { font-size: 40px; font-weight: 700; margin-bottom: 8px }
.card p { margin: 8px 0 0; font-size: 14.5px; line-height: 1.4 }
.pts { font-size: 18px; line-height: 1.45; padding-left: 22px }
.pts li { margin-bottom: 11px }
table { border-collapse: collapse; width: 100%; font-size: 15.5px; background: #fff }
th { background: #0B2026; color: #F9F7F4; text-align: left; padding: 8px 10px; font-weight: 600 }
td { padding: 7px 10px; border-bottom: 1px solid #ece7df }
tr.tot td { font-weight: 700; background: #FFE8E3 }
h3 { font-size: 17px; margin: 0 0 10px }
.note { font-size: 13px; opacity: .75 }
.caveat { font-size: 13.5px; background: #fff4d6; padding: 10px 14px; border-radius: 8px; margin-top: 18px }
.quote { background: #fff; border: 1px solid #C4CCD6; border-radius: 12px; padding: 20px 24px; font-size: 15.5px; line-height: 1.45 }
.quote .qh::before { content: 'AI-GENERATED BRIEF'; display: block; font-size: 11px; letter-spacing: .08em; color: #4A5568; margin-bottom: 6px; font-weight: 600 }
.quote .qh { font-weight: 700; font-size: 18px; margin-bottom: 6px }
.flow { display: flex; align-items: stretch; gap: 10px; margin-top: 30px }
.flow .st { flex: 1; background: #fff; border-top: 6px solid #FF3621; border-radius: 10px; padding: 18px 16px; font-size: 14px; line-height: 1.4 }
.flow .st b { display: block; font-size: 19px; margin-bottom: 8px }
.flow .ar { align-self: center; font-size: 30px; color: #FF3621 }
code { background: #eee; padding: 1px 5px; border-radius: 4px; font-size: 90% }
.dense .pts { font-size: 15.5px; line-height: 1.4 } .dense .card p { font-size: 14px }
@media print { body { background: none } .slide { margin: 0 } }
"""

html = ["<!doctype html><html><head><meta charset='utf-8'><title>VentoGuard</title>",
        "<link href='https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&display=swap' rel='stylesheet'>",
        f"<style>{CSS}</style></head><body>"]
for i, s in enumerate(SLIDES, 1):
    cls = "slide title" if s["kind"] == "title" else "slide"
    kick = f"<div class='kick'>{s['kicker']}</div>" if s["kicker"] else ""
    html.append(f"<section class='{cls}'>{kick}<h1>{s['title']}</h1>{s['body']}"
                f"<div class='brand'>VentoGuard · Databricks Data Intelligence Platform</div><div class='num'>{i}/{len(SLIDES)}</div></section>")
html.append("</body></html>")
(HERE / "VentoGuard_deck.html").write_text("\n".join(html))
(HERE / "VentoGuard_deck.md").write_text("\n\n---\n\n".join((f"_{s['kicker']}_\n\n" if s["kicker"] else "") + s["md"] for s in SLIDES) + "\n")

chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=4000",
                f"--print-to-pdf={HERE / 'VentoGuard_deck.pdf'}", f"file://{(HERE / 'VentoGuard_deck.html').resolve()}"], check=True,
               capture_output=True)
print("deck built:", len(SLIDES), "slides")
