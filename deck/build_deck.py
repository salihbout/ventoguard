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
slide("Monday 07:00: what the reliability lead sees",
      f"""<div class="grid2">
        <div><ol class="pts">
          <li><b>Risk board</b> (served from Lakebase in milliseconds): <b>{N['n_critical']} CRITICAL, {N['n_high']} HIGH</b> turbines, each with the likely component and € at stake.</li>
          <li><b>AI maintenance brief</b> for {N['brief_turbine']}: the diagnosis cites the sensor evidence and the technician's German note, with steps, crew, parts and the business case.</li>
          <li><b>One click → work order</b>, written transactionally to Lakebase with priority, crew and planned date.</li>
          <li><b>Asset manager asks Genie</b>: <i>"Which farm lost the most revenue to failures, and which component caused it?"</i> Genie answers with the SQL shown.</li>
        </ol></div>
        <div class="quote"><div class="qh">{N['brief_headline']}</div><p>{N['brief_diagnosis']}</p><p><b>Business case.</b> {N['brief_business_case']}</p><small>Generated by Claude on Databricks from the model score, sensor residuals and technician notes</small></div>
      </div>""",
      f"""## Monday 07:00: what the reliability lead sees
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
@media print { body { background: none } .slide { margin: 0 } }
"""

html = ["<!doctype html><html><head><meta charset='utf-8'><title>VentoGuard</title>",
        "<link href='https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&display=swap' rel='stylesheet'>",
        f"<style>{CSS}</style></head><body>"]
for i, s in enumerate(SLIDES, 1):
    cls = "slide title" if s["kind"] == "title" else "slide"
    html.append(f"<section class='{cls}'><h1>{s['title']}</h1>{s['body']}"
                f"<div class='brand'>VentoGuard · Databricks Data Intelligence Platform</div><div class='num'>{i}/{len(SLIDES)}</div></section>")
html.append("</body></html>")
(HERE / "VentoGuard_deck.html").write_text("\n".join(html))
(HERE / "VentoGuard_deck.md").write_text("\n\n---\n\n".join(s["md"] for s in SLIDES) + "\n")

chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=4000",
                f"--print-to-pdf={HERE / 'VentoGuard_deck.pdf'}", f"file://{(HERE / 'VentoGuard_deck.html').resolve()}"], check=True,
               capture_output=True)
print("deck built:", len(SLIDES), "slides")
