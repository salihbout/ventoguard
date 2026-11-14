"""Build the VentoGuard business deck for Aerion Windkraft AG (a fictional customer).

Outputs:
  deck/VentoGuard_deck.html  presentation: one slide per screen, ← → / Space to navigate, F for full screen, animated
  deck/VentoGuard_deck.pdf   the same slides printed with headless Chrome (one page each, final state)
  deck/VentoGuard_deck.md    text version with speaker notes (for text-only readers)

Usage: python deck/build_deck.py
All figures come from evidence/ via deck/extract_numbers.py -> deck/numbers.json. Nothing is typed in by hand.
"""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent


def embed(name, mime):
    """Inline an asset as a data URI so the deck works wherever the HTML file is opened."""
    import base64
    return f"data:{mime};base64," + base64.b64encode((HERE / "assets" / name).read_bytes()).decode()


DBX_LOGO = embed("databricks-logo.png", "image/png")
SPARK_MARK = embed("databricks-spark-mark.svg", "image/svg+xml")
N = json.loads((HERE / "numbers.json").read_text())
CUSTOMER = "Aerion Windkraft AG"


def m(x):  # € millions
    return f"€{x/1e6:.1f} M"


def k(x):
    return f"€{x/1e3:,.0f} k"


def cnt(value, dec=1, pre="", suf=""):
    """Number that counts up when its slide appears. The final value is the static text, so PDF and no-JS views are correct."""
    txt = f"{pre}{value:,.{dec}f}{suf}"
    return f"<span class='cnt' data-v='{value}' data-dec='{dec}' data-pre='{pre}' data-suf='{suf}'>{txt}</span>"


AERION_LOGO = """<div class="aerion"><svg viewBox="-36 -36 72 72" width="46" height="46" aria-hidden="true">
  <g fill="currentColor"><path id="bl" d="M0,-5 C6,-12 6,-27 0,-35 C-3.5,-27 -4,-12 0,-5Z"/>
  <use href="#bl" transform="rotate(120)"/><use href="#bl" transform="rotate(240)"/></g>
  <circle r="5" fill="#FF3621"/></svg><span><b>AERION</b><small>Windkraft AG</small></span></div>"""

SLIDES = []


def slide(kicker, title, body, md, notes="", kind=""):
    SLIDES.append(dict(kicker=kicker, title=title, body=body, md=md, notes=notes, kind=kind))


net, unpl = N["net_annual_benefit_eur"], N["unplanned_cost_annualised_eur"]
half = N["avoidable_100"] * 0.5 - N["false_alarm_cost"]
comp = N["by_component"]
cmax = max(c["total_eur"] for c in comp)

# 1 ─ Title
slide("", "Turn surprise failures into planned repairs worth €4.2&nbsp;M&nbsp;a&nbsp;year",
      f"""<div class="cobrand">{AERION_LOGO}<img class="dbx" src="{DBX_LOGO}" alt="Databricks" width="190" height="30"></div><div class="a sub" style="--d:1">VentoGuard for <b>{CUSTOMER}</b>: predictive drivetrain reliability for 120 turbines</div>
      <div class="kpis">
        <div class="a" style="--d:2"><b>{cnt(net/1e6, 1, '€', ' M')}</b><span>net benefit per year</span></div>
        <div class="a" style="--d:3"><b>{cnt(N['availability_uplift_pp'], 1, '+', ' pp')}</b><span>technical availability</span></div>
        <div class="a" style="--d:4"><b>{cnt(N['median_lead_days'], 0, '', ' days')}</b><span>early warning</span></div>
      </div>
      <div class="a foot" style="--d:5">Prepared for {CUSTOMER}: COO · Head of Data &amp; Architecture · Head of Asset Management</div>""",
      f"""# Turn surprise failures into planned repairs worth €4.2 M a year
VentoGuard for **{CUSTOMER}** (fictional German onshore wind operator, 4 farms, 120 turbines)

- **{m(net)}** net benefit per year · **+{N['availability_uplift_pp']:.1f} pp** technical availability · **{N['median_lead_days']:.0f} days** early warning
- Audience: COO (executive sponsor, funds the decision), Head of Data & Architecture (technical owner, lives with the build), Head of Asset Management (domain owner)""",
      "Thank them. One line: I'll keep slides short and spend most of the time in the product. Then go straight to the outcome.",
      kind="title")

# 2 ─ Outcome
slide("The outcome", "Where the €4.2 M comes from",
      f"""<div class="trio">
        <div class="a card dark" style="--d:1"><b>{cnt(unpl/1e6, 1, '€', ' M')}</b><span>lost each year to unplanned drivetrain failures today</span></div>
        <div class="a arrow" style="--d:2">→</div>
        <div class="a card lava" style="--d:3"><b>{cnt(net/1e6, 1, '€', ' M')}</b><span>saved each year, net, at a conservative 75 % catch rate</span></div>
        <div class="a card" style="--d:4"><b>{cnt(N['downtime_days_avoided'], 0)}</b><span>turbine-days of production back each year</span></div>
      </div>
      <p class="a line" style="--d:5">Failures are flagged <b>{N['median_lead_days']:.0f} days</b> ahead, so a <b>five-week outage</b> becomes a <b>one-week planned swap</b>.</p>""",
      f"""## The outcome: where the €4.2 M comes from
- Today: **{m(unpl)}/yr** lost to unplanned drivetrain failures ({N['failures_observed']} failures in {N['observed_days']} days, repair + lost revenue)
- With VentoGuard: **{m(net)}/yr net** (75 % catch rate, false-alarm inspections deducted) and **{N['downtime_days_avoided']:,} turbine-days** of production back
- How: failures flagged {N['median_lead_days']:.0f} days ahead, so a five-week outage becomes a one-week planned swap""",
      "Say the € number in the first two minutes. €11.3 M today, €4.2 M back per year. Everything after this proves that number.")

# 3 ─ Problem
bars = "".join(
    f"""<div class="bar a" style="--d:{i+1}"><span class="lbl">{c['component'].replace('_', ' ')}</span>
        <span class="track"><span class="fill{' hot' if i < 2 else ''}" style="--w:{c['total_eur']/cmax*100:.1f}%"></span></span>
        <span class="val">{k(c['total_eur'])}</span></div>""" for i, c in enumerate(comp))
slide("The problem", "Gearboxes and main bearings drive 90 % of the cost",
      f"""<div class="split">
        <div class="bars">{bars}<p class="a note" style="--d:5">Cost of unplanned failures by component, last {N['observed_days']} days</p></div>
        <div class="facts">
          <div class="a fact" style="--d:3"><b>€430 k</b><span>and 5+ weeks down for every surprise gearbox</span></div>
          <div class="a fact" style="--d:4"><b>{N['avail_hunsrueck']:.1f} %</b><span>availability at Hunsrück Höhe, against a 97 % target</span></div>
          <div class="a fact" style="--d:5"><b>2–5 weeks</b><span>of warning signs in SCADA and technicians' notes that nobody combined</span></div>
        </div></div>""",
      "## The problem: gearboxes and main bearings drive 90 % of the cost\n" +
      "\n".join(f"- {c['component']}: {c['failures']} failures, {k(c['total_eur'])}" for c in comp) +
      f"\n- €430 k and 5+ weeks per surprise gearbox · Hunsrück Höhe at {N['avail_hunsrueck']:.1f} % vs 97 % target\n- Warning signs were visible 2–5 weeks ahead in SCADA and technician notes, but never combined",
      "This is their pain in their numbers. Pause on €430 k per gearbox. Say the signals were already there; the problem is that nothing connected them.")

# 4 ─ Demo intro (tell)
steps = ["Risk board", "AI brief", "Work order", "Ask Genie"]
subs = [f"{N['n_critical']} critical turbines, ranked by €", "diagnosis + business case", "booked in one click", "plain-language fleet questions"]
chips = "".join(f"<div class='a step' style='--d:{i+1}'><i>{i+1}</i><b>{s}</b><span>{t}</span></div>" + ("<div class='a chev' style='--d:%d'>›</div>" % (i + 1) if i < 3 else "")
                for i, (s, t) in enumerate(zip(steps, subs)))
slide("Live demo · what you'll see", "Monday 07:00 at the reliability desk",
      f"""<div class="steps">{chips}</div>
      <p class="a line" style="--d:5">Watch for the moment a <b>€400 k surprise</b> becomes a <b>planned job</b>.</p>""",
      """## Live demo · what you'll see: Monday 07:00 at the reliability desk
1. Risk board: critical turbines ranked by € at stake
2. AI maintenance brief: diagnosis, technician notes, business case
3. One-click work order (Lakebase)
4. Ask Genie a fleet question, with the SQL shown""",
      "TELL before you SHOW. Say the four steps, then switch to the app.")

# 5 ─ Demo landing (tell)
rows = [("Risk board", "Only the turbines that matter, ranked by money", f"{k(N['app_avoidable_now_eur'])} avoidable now"),
        ("AI brief", f"A decision on {N['brief_turbine']} in minutes", "≈ €207 k saved"),
        ("Work order", "Crane, spare and crew in a low-wind window", "Corrective → planned"),
        ("Genie", "Answers without a BI ticket", "Time to insight")]
tr = "".join(f"<div class='a row' style='--d:{i+1}'><b>{a}</b><span>{b}</span><em>{c}</em></div>" for i, (a, b, c) in enumerate(rows))
slide("Live demo · what it means", "Four clicks: a five-week surprise became a one-week plan",
      f"""<div class="rows">{tr}</div>
      <p class="a line" style="--d:5">Run every morning across the fleet: <b>{m(net)} a year</b>.</p>""",
      "## Live demo · what it means: four clicks, a five-week surprise became a one-week plan\n" +
      "\n".join(f"- {a}: {b} ({c})" for a, b, c in rows) + f"\n- Run every morning across the fleet: {m(net)}/yr",
      "TELL after you SHOW. Land it in business terms, not features.")

# 6 ─ Proof
leads = "".join(f"<div class='lead a' style='--d:{1 + i*0.35:.2f}'><span class='lf' style='--h:{b['lead']/14*100:.0f}%'></span><small>{b['lead']} d</small></div>" for i, b in enumerate(N["backtest"]))
slide("Proof", f"{N['bt_caught']} of {N['bt_total']} hold-out failures were flagged in advance",
      f"""<div class="split">
        <div><div class="leads">{leads}</div><p class="a note" style="--d:4">Days of warning before each failure in the back-test (Aug–Sep, never seen in training)</p></div>
        <div class="facts">
          <div class="a fact" style="--d:3"><b>4 / 4</b><span>turbines degrading right now are the 4 on today's risk board</span></div>
          <div class="a fact" style="--d:4"><b>{N['precision']*100:.0f} %</b><span>of alerts were real failures</span></div>
          <div class="a fact muted" style="--d:5"><b>75 %</b><span>catch rate assumed in the value case. Synthetic data, so the pilot measures the real number</span></div>
        </div></div>""",
      "## Proof\n" + f"- Back-test: {N['bt_caught']}/{N['bt_total']} hold-out failures flagged ahead; lead times " +
      ", ".join(f"{b['lead']} d" for b in N["backtest"]) +
      f"\n- Live check: today's 4 high/critical turbines are the 4 that are degrading (hidden ground truth)\n- Precision {N['precision']*100:.0f} %, ROC-AUC {N['auc']:.3f}, PR-AUC {N['pr_auc']:.2f}\n- Caveat: synthetic data, so the value case assumes a 75 % catch rate and the pilot measures the real one",
      "Concede the synthetic-data caveat yourself, before they raise it. That's why the case assumes 75 %.")

# 7 ─ COO value
wf = [("Avoidable if every failure is planned", N["avoidable_100"], ""), ("At a 75 % catch rate", N["avoidable_75"], ""),
      ("False-alarm inspections", -N["false_alarm_cost"], "neg"), ("Net benefit per year", net, "tot")]
wmax = N["avoidable_100"]
wfh = "".join(f"""<div class="bar a" style="--d:{i+1}"><span class="lbl">{l}</span><span class="track"><span class="fill {c}" style="--w:{abs(v)/wmax*100:.1f}%"></span></span>
              <span class="val">{'−' if v < 0 else ''}{m(abs(v)) if abs(v) >= 1e6 else k(abs(v))}</span></div>""" for i, (l, v, c) in enumerate(wf))
slide("Value · COO", f"{m(net)} a year net, and {m(half)} even if we catch only half",
      f"""<div class="split">
        <div class="bars wide">{wfh}</div>
        <div class="facts">
          <div class="a fact" style="--d:3"><b>EBITDA</b><span>less corrective O&M, with crane mobilisation alone ≈ €120 k per gearbox</span></div>
          <div class="a fact" style="--d:4"><b>Revenue</b><span>+{N['availability_uplift_pp']:.1f} pp availability protects PPA volumes</span></div>
          <div class="a fact" style="--d:5"><b>Run cost</b><span>serverless and scale-to-zero, measured in the pilot; one avoided gearbox covers it many times</span></div>
        </div></div>""",
      f"""## Value for the COO: {m(net)} a year net, {m(half)} even at half the catch rate
- Avoidable at 100 %: {m(N['avoidable_100'])} · at 75 %: {m(N['avoidable_75'])} · minus false-alarm inspections −{k(N['false_alarm_cost'])} · **net {m(net)}/yr**
- EBITDA: less corrective O&M (crane ≈ €120 k per gearbox) · Revenue: +{N['availability_uplift_pp']:.1f} pp availability · Run cost: serverless, measured in the pilot""",
      "Look at the COO. Lead with the downside case: even at 50 % it's €2.7 M.")

# 8 ─ Asset management value
tiles = [("13 days", "matches crane booking and spare-pool lead times"), ("Explained", "each alert names the component and the 3 sensor signals behind it"),
         ("519 notes", "German and English technician notes now raise risk"), ("Self-service", "fleet questions answered by Genie, with the SQL shown")]
th = "".join(f"<div class='a tile' style='--d:{i+1}'><b>{a}</b><span>{b}</span></div>" for i, (a, b) in enumerate(tiles))
slide("Value · Head of Asset Management", "From firefighting to a planned maintenance calendar",
      f"""<div class="tiles">{th}</div>
      <p class="a line" style="--d:5">KPIs you're measured on, from governed tables: <b>availability · MTTR · corrective/planned ratio · O&M €/MWh</b></p>""",
      "## Value for the Head of Asset Management: from firefighting to a planned maintenance calendar\n" +
      "\n".join(f"- **{a}**: {b}" for a, b in tiles) + "\n- KPIs from governed gold tables: availability, MTTR, corrective/planned ratio, O&M €/MWh",
      "Look at the domain owner. Talk about their week: fewer surprises, explainable alerts, their team's notes finally count.")

# 9 ─ Architecture
flow = [("Lakeflow", "ingest SCADA, notes, assets, prices"), ("Unity Catalog", "govern, mask, lineage"), ("ML + GenAI", "14-day risk and AI briefs"),
        ("Lakebase", "millisecond serving and work orders"), ("App + Genie", "where the business works")]
fh = "".join(f"<div class='a node' style='--d:{i+1}'><b>{a}</b><span>{b}</span></div>" + (f"<div class='a link' style='--d:{i+1.5}'></div>" if i < 4 else "") for i, (a, b) in enumerate(flow))
slide("How it works", "One governed platform, from raw SCADA to the dispatcher's screen",
      f"""<div class="flow">{fh}</div>
      <p class="a line small" style="--d:6">One Lakeflow Job, daily at 05:00 · deployed as one bundle · open formats (Delta, Postgres, MLflow)</p>""",
      "## How it works: one governed platform\n" + " → ".join(f"**{a}** ({b})" for a, b in flow) +
      "\n- One Lakeflow Job daily at 05:00, deployed as a Declarative Automation Bundle, open formats",
      "Look at the architect. Keep it to one breath, and offer to go deeper in Q&A (backup slides).")

# 10 ─ Trust
trust = [("Data quality", f"{N['dq_dropped']:,} bad readings dropped before the model"), ("GDPR", "technician names masked in every tool"),
         ("Model gate", "no promotion without passing quality checks"), ("Grounded AI", "briefs use only measured facts"),
         ("Lineage", "every number traces back to its raw file"), ("Least privilege", "the app sees only what it needs")]
tt = "".join(f"<div class='a tile sm' style='--d:{1 + i*0.6:.1f}'><b>{a}</b><span>{b}</span></div>" for i, (a, b) in enumerate(trust))
slide("Trust", "Governed data, explainable models, grounded AI",
      f"""<div class="tiles six">{tt}</div>""",
      "## Trust: governed data, explainable models, grounded AI\n" + "\n".join(f"- **{a}**: {b}" for a, b in trust),
      "Short. These are the answers to the architect's security questions before they ask.")

# 11 ─ Ask
plan = [("Weeks 1–2", "connect real SCADA and SAP PM"), ("Weeks 3–4", "retrain and calibrate with your reliability lead"),
        ("Weeks 5–8", "live shadow mode on Hunsrück Höhe"), ("Week 8", "go/no-go on € avoided")]
ph = "".join(f"<div class='a ms' style='--d:{i+1}'><i></i><b>{a}</b><span>{b}</span></div>" for i, (a, b) in enumerate(plan))
slide("The ask", "An 8-week pilot on Hunsrück Höhe",
      f"""<img class="logo" src="{SPARK_MARK}" alt="Databricks" width="44" height="49"><div class="timeline">{ph}</div>
      <div class="a decide" style="--d:5"><b>Two decisions today</b><span>① your sponsorship &nbsp; ② access to 24 months of SCADA and CMMS data</span></div>""",
      "## The ask: an 8-week pilot on Hunsrück Höhe\n" + "\n".join(f"- {a}: {b}" for a, b in plan) +
      "\n- Success: ≥ 60 % of major failures flagged ≥ 7 days ahead; ≤ 1 false alarm per 10 turbines per month; ≥ 1 documented planned-instead-of-unplanned repair\n- Two decisions today: sponsorship, and access to 24 months of SCADA and CMMS data",
      "Ask, then stop talking. Let them answer.", kind="ask")

# ─ Backup (Q&A)
def backup(title, cards, md, notes):
    ch = "".join(f"<div class='a card q' style='--d:{i+1}'><b>{a}</b><span>{b}</span></div>" for i, (a, b) in enumerate(cards))
    slide("Backup · Q&A", title, f"<div class='qgrid'>{ch}</div>", md, notes)


backup("Cost, risk and time to value",
       [("Cost", f"Serverless and scale-to-zero, so no idle cluster. The pilot measures it exactly. One gearbox ≈ €430 k."),
        ("Downside case", f"Only 50 % caught still gives {m(half)}/yr."),
        ("Precision risk", "The case assumes 75 %, and shadow mode puts a field verdict on every alert."),
        ("Alert fatigue", "Ranked by € at stake. Target ≤ 1 false alarm per 10 turbines per month."),
        ("Adoption", "The work order sits on the same screen as the alert. Daily use is a go/no-go criterion."),
        ("Time to value", "First live alerts in week 5, go/no-go in week 8, then the same bundle on all 4 farms.")],
       f"""## Backup: cost, risk and time to value
- Cost: serverless + scale-to-zero, measured in the pilot; one gearbox ≈ €430 k · Downside: {m(half)}/yr at 50 % caught
- Risk: 75 % assumed, shadow mode with field verdicts; ≤ 1 false alarm/10 turbines/month; work order in the same screen
- Time to value: live alerts week 5, go/no-go week 8, then all 4 farms with the same bundle""",
       "Business pushback. Answer with the headline first, then point at the card.")

backup("Architecture and integration",
       [("Ingest", "Auto Loader today. In the pilot: historian exports or Zerobus for SCADA, and Lakeflow Connect for SAP PM."),
        ("Transform", "Declarative pipeline bronze → silver → gold, with expectations at silver."),
        ("Serve", "Gold tables sync to Lakebase Postgres. Work orders are transactional, in the app's own schema."),
        ("Write-back", "Work orders go to SAP PM through its API. SAP stays the system of record."),
        ("Scale", "≈ 3.3 M rows of 10-minute SCADA on serverless. More farms is configuration, not a rebuild."),
        ("Freshness", "Daily fits the 14-day horizon. The sync can switch to continuous.")],
       """## Backup: architecture and integration
- Ingest: Auto Loader; pilot = historian exports or Zerobus (SCADA), Lakeflow Connect (SAP PM)
- Transform: declarative pipeline with expectations · Serve: Lakebase synced tables + transactional work orders
- Write-back to SAP PM (system of record) · Scale: ~3.3 M rows of 10-min SCADA on serverless · Freshness: daily, can go continuous""",
       "Technical pushback. Give real detail, then one sentence back to the COO.")

backup("Data quality, model validation, AI guard-rails",
       [("Data quality", f"Expectations dropped {N['dq_dropped']:,} impossible readings. Features are fleet-relative, so weather isn't mistaken for failure."),
        ("Validation", "Time split: trained before August, tested Aug–Sep, so no leakage."),
        ("Model gate", "PR-AUC ≥ 0.30 and ≥ 60 % caught ≥ 3 days ahead, or no @champion."),
        ("Lifecycle", "MLflow tracks every run. The pilot adds drift monitoring and a monthly retrain."),
        ("Grounded AI", "Claude via ai_query, using only the score, residuals and notes. Tagged ai_generated."),
        ("Security", "UC grants, column mask on names, and a least-privilege app service principal.")],
       f"""## Backup: data quality, model validation, AI guard-rails
- Data quality: expectations dropped {N['dq_dropped']:,} readings; fleet-relative features
- Validation: time split (train < Aug, test Aug–Sep); gate PR-AUC ≥ 0.30 and ≥ 60 % caught ≥ 3 d ahead before @champion; MLflow tracking; pilot adds drift monitoring + monthly retrain
- GenAI: Claude via ai_query, grounded on score, residuals and notes, tagged ai_generated; a human approves every work order
- Security: UC grants, column mask on technician names, least-privilege app service principal""",
       "Technical pushback on models and AI. Stay concrete.")

# ─ Industry context: how the industry fixes this, and what leaders already show (all figures from public sources)
ladder = [("1", "Fix it when it breaks", "time-based service and fixed SCADA alarms", "today"),
          ("2", "Watch each component", "vibration and oil sensors per turbine (CMS)", ""),
          ("3", "Predict across the fleet", "SCADA, CMS and work orders combined with AI, weeks ahead", "vg"),
          ("4", "Act automatically", "AI writes the brief, plans crew, crane and low-wind window", "vg")]
lh = "".join(f"<div class='a rung {c}' style='--d:{i+1}'><i>{n}</i><b>{t}</b><span>{d}</span>"
             + ("<em>Aerion today</em>" if c == "today" else "<em>VentoGuard</em>" if c == "vg" else "") + "</div>"
             for i, (n, t, d, c) in enumerate(ladder))
slide("How the industry fixes it", "From fixing failures to predicting them",
      f"""<div class="ladder">{lh}</div>
      <p class="a line" style="--d:5">Leading operators moved from step 1 to steps 3–4. <b>The data already exists at Aerion</b>; what's missing is one place that connects it.</p>""",
      """## How the industry fixes it: from fixing failures to predicting them
1. Fix it when it breaks: time-based service, fixed SCADA alarms (**Aerion today**)
2. Watch each component: vibration and oil sensors per turbine (condition monitoring)
3. Predict across the fleet: SCADA, CMS and work orders combined with AI, weeks ahead (**VentoGuard**)
4. Act automatically: AI writes the brief and plans crew, crane and a low-wind window (**VentoGuard**)
- Leading operators moved from step 1 to steps 3–4. The data already exists at Aerion; what's missing is one place that connects it.""",
      "Frame this as a journey the industry is already on. Aerion is not behind on data, only on connecting it.")

# Peer names are fictional; each figure is a real public disclosure by the company it stands for (see deck/SOURCES.md).
peers = [("Borealis Turbines", "Turbine maker", "99 %", "of drivetrain failures detected, predicted up to 3 years ahead, from 600 TB of AI training data"),
         ("Polaris Wind Systems", "Turbine maker", "51,000+", "turbines monitored centrally, with wear predicted and repairs planned into low-wind periods"),
         ("Meridian Energía", "Utility", "15–95 %", "of major-component repair cost saved by ML vibration analysis on 1,400+ turbines"),
         ("Northgate Power", "Utility", "−5 %", "corrective maintenance frequency projected from an AI trial on an offshore wind farm")]
ph2 = "".join(f"<div class='a peer' style='--d:{i+1}'><small>{n}</small><em>{r}</em><b>{v}</b><span>{d}</span></div>"
              for i, (n, r, v, d) in enumerate(peers))
slide("The competition", "Leaders already turn data and AI into availability",
      f"""<div class="peers">{ph2}</div>
      <div class="a edge" style="--d:5"><b>Aerion's edge</b><span>OEM tools see their own turbines. Aerion runs a mixed fleet (Hansa Drives and NordGear gearboxes), so <b>owning one governed view of every turbine</b> is what keeps the margin in-house.</span></div>
      <p class="a src" style="--d:6">Company names are anonymised. Each figure is that company's own public disclosure (OEM brochures, utility press release 2018, independent test-centre release 2021).</p>""",
      """## The competition: leaders already turn data and AI into availability
_Company names are anonymised; each figure is that company's own public disclosure. Sources are listed in deck/SOURCES.md._
- **Borealis Turbines (turbine maker):** 99 % drivetrain detection hit rate; component failures predicted up to 3 years in advance; 600 TB of data for its AI
- **Polaris Wind Systems (turbine maker):** central diagnostics centre monitors 51,000+ turbines; wear is predicted and repairs planned during low-wind periods
- **Meridian Energía (utility):** machine-learning vibration analysis on 1,400+ turbines saves 15–95 % of main-component repair cost (2018)
- **Northgate Power (utility):** independent analysis of an AI trial on an offshore wind farm: corrective maintenance frequency could fall by 5 % (2021)
- Also: peer-reviewed research shows SCADA data alone flags gearbox and generator failures months ahead (*Wind Energy Science* 10, 2025)
- **Aerion's edge:** OEM tools see their own turbines. Aerion runs a mixed fleet (Hansa Drives and NordGear), so owning one governed view of every turbine keeps the margin in-house.""",
      "This answers 'why now' for the COO: competitors and OEMs are already doing this. Then pivot to the edge: OEMs only see their own turbines. If asked, the names are anonymised but the figures are real public disclosures.")

# Story order: promise (title) → problem → how the industry fixes it → competitors → where the € comes from → demo
competition = SLIDES.pop()      # defined last
industry = SLIDES.pop()         # defined just before it
SLIDES[1], SLIDES[2] = SLIDES[2], SLIDES[1]
SLIDES[2:2] = [industry, competition]

# ─ Render ───────────────────────────────────────────────────────────────────────────────────────
CSS = """
:root { --lava:#FF3621; --navy:#0B2026; --light:#F9F7F4; --line:#E6E1D9; --muted:#5A6B73 }
* { box-sizing: border-box; margin: 0 }
html, body { height: 100%; background: var(--navy); font-family: 'DM Sans', 'Helvetica Neue', Arial, sans-serif; color: var(--navy); overflow: hidden }
#stage { position: absolute; width: 1280px; height: 720px; left: 50%; top: 50%; transform-origin: center; }
.slide { position: absolute; inset: 0; padding: 64px 80px; background: var(--light); opacity: 0; visibility: hidden; transition: opacity .45s ease, visibility .45s }
.slide.active { opacity: 1; visibility: visible }
.kick { color: var(--lava); font-weight: 700; letter-spacing: .1em; font-size: 14px; text-transform: uppercase; margin-bottom: 12px }
h1 { font-size: 46px; line-height: 1.1; letter-spacing: -.01em; max-width: 1080px; margin-bottom: 48px }
.a { opacity: 0; transform: translateY(18px) }
.active .a { animation: up .6s cubic-bezier(.2,.7,.2,1) forwards; animation-delay: calc(var(--d, 0) * .18s + .1s) }
.active .kick, .active h1 { animation: up .55s cubic-bezier(.2,.7,.2,1) both }
@keyframes up { to { opacity: 1; transform: none } }
.logo { position: absolute; top: 56px; right: 80px; width: 44px; height: auto }
.active .logo { animation: up .6s cubic-bezier(.2,.7,.2,1) both }
.brand { position: absolute; bottom: 26px; left: 80px; font-size: 13px; opacity: .45 }
.ask { background: var(--navy); color: var(--light) }
.title { background: var(--light) }
.title h1 { font-size: 62px; margin: 140px 0 22px; max-width: 1120px }
.title .sub { font-size: 24px; opacity: .85 }
.kpis { display: flex; gap: 72px; margin-top: 64px }
.kpis b { display: block; font-size: 60px; color: var(--navy); line-height: 1 }
.kpis div:first-child b { color: var(--lava) }
.kpis span { font-size: 17px; opacity: .75 }
.foot { position: absolute; bottom: 56px; font-size: 15px; opacity: .6 }
.trio { display: flex; align-items: stretch; gap: 22px }
.card { flex: 1; background: #fff; border: 1px solid var(--line); border-radius: 16px; padding: 30px 28px }
.card b { display: block; font-size: 56px; line-height: 1; margin-bottom: 14px }
.card span { font-size: 18px; line-height: 1.35; color: var(--muted) }
.card.dark { background: var(--navy); border: none } .card.dark b, .card.dark span { color: var(--light) }
.card.lava { background: var(--lava); border: none } .card.lava b, .card.lava span { color: #fff }
.arrow { align-self: center; font-size: 44px; color: var(--lava) }
.line { font-size: 24px; margin-top: 44px; line-height: 1.4 } .line.small { font-size: 18px; color: var(--muted) }
.split { display: grid; grid-template-columns: 1.25fr 1fr; gap: 64px; align-items: start }
.bars .bar { display: grid; grid-template-columns: 170px 1fr 92px; align-items: center; gap: 14px; margin-bottom: 22px; font-size: 18px }
.bars.wide .bar { grid-template-columns: 250px 1fr 84px; font-size: 17px }
.lbl { text-transform: capitalize } .bars.wide .lbl { text-transform: none }
.track { height: 30px; background: #ECE7DF; border-radius: 6px; overflow: hidden }
.fill { display: block; height: 100%; width: var(--w); background: #9AA8B0; border-radius: 6px; transform: scaleX(0); transform-origin: left }
.fill.hot, .fill.tot { background: var(--lava) } .fill.neg { background: var(--navy) }
.active .fill { transition: transform 1s cubic-bezier(.2,.7,.2,1) .5s; transform: scaleX(1) }
.val { font-weight: 700; text-align: right }
.cnt { font-size: inherit !important; color: inherit !important; opacity: 1 !important; line-height: inherit }
.note { font-size: 14px; color: var(--muted); margin-top: 10px }
.facts .fact { background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 14px 20px; margin-bottom: 16px }
.fact b { display: block; font-size: 34px; line-height: 1.05; color: var(--navy) } .fact span { font-size: 17px; color: var(--muted) }
.fact.muted { background: transparent; border-style: dashed; border-color: #C4CCD6 }
.steps { display: flex; align-items: center; gap: 14px; margin-top: 20px }
.step { flex: 1; background: #fff; border: 1px solid var(--line); border-radius: 16px; padding: 28px 22px; min-height: 190px }
.step i { font-style: normal; display: inline-grid; place-items: center; width: 38px; height: 38px; border-radius: 50%; background: var(--lava); color: #fff; font-weight: 700; margin-bottom: 18px }
.step b { display: block; font-size: 26px; margin-bottom: 8px } .step span { font-size: 16px; color: var(--muted) }
.chev { font-size: 40px; color: var(--lava) }
.rows .row { display: grid; grid-template-columns: 200px 1fr 330px; gap: 24px; align-items: center; background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 20px 26px; margin-bottom: 12px; font-size: 19px }
.row b { font-size: 21px } .row em { font-style: normal; font-weight: 700; color: var(--lava); text-align: right }
.leads { display: flex; align-items: flex-end; gap: 18px; height: 300px; padding-top: 10px; border-bottom: 2px solid var(--navy) }
.lead { flex: 1; height: 100%; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; gap: 6px }
.lead .lf { width: 100%; height: var(--h); background: var(--lava); border-radius: 6px 6px 0 0; transform: scaleY(0); transform-origin: bottom; order: 2 }
.lead small { font-weight: 700; font-size: 15px; order: 1 }
.active .lead .lf { transition: transform .9s cubic-bezier(.2,.7,.2,1) .4s; transform: scaleY(1) }
.tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px }
.tiles.six { grid-template-columns: repeat(3, 1fr) }
.tile { background: #fff; border: 1px solid var(--line); border-top: 6px solid var(--lava); border-radius: 14px; padding: 26px 24px; min-height: 180px }
.tile b { display: block; font-size: 30px; margin-bottom: 10px } .tile span { font-size: 17px; color: var(--muted); line-height: 1.4 }
.tile.sm { min-height: 150px } .tile.sm b { font-size: 25px }
.flow { display: flex; align-items: center; margin-top: 30px }
.node { flex: 1; background: #fff; border: 1px solid var(--line); border-radius: 14px; padding: 26px 18px; text-align: center; min-height: 170px }
.node b { display: block; font-size: 23px; margin-bottom: 10px } .node span { font-size: 15.5px; color: var(--muted) }
.link { width: 36px; height: 4px; background: var(--lava); flex: none; transform-origin: left }
.timeline { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; margin-top: 30px; border-top: 4px solid rgba(249,247,244,.25) }
.ms { padding: 26px 22px 0 0; position: relative }
.ms i { position: absolute; top: -14px; left: 0; width: 24px; height: 24px; border-radius: 50%; background: var(--lava) }
.ms b { display: block; font-size: 24px; margin: 8px 0 8px; color: var(--lava) } .ms span { font-size: 18px; opacity: .85 }
.decide { margin-top: 64px; background: rgba(255,54,33,.12); border: 1px solid var(--lava); border-radius: 14px; padding: 24px 30px }
.decide b { display: block; font-size: 26px; margin-bottom: 6px } .decide span { font-size: 21px }
.qgrid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px }
.card.q { padding: 22px 24px } .card.q b { font-size: 22px; margin-bottom: 8px } .card.q span { font-size: 16px }
.ask .brand { color: var(--light) }
.ladder { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; align-items: end }
.rung { background: #fff; border: 1px solid var(--line); border-radius: 14px; padding: 22px 20px; position: relative }
.rung:nth-child(1) { min-height: 170px } .rung:nth-child(2) { min-height: 210px } .rung:nth-child(3) { min-height: 250px } .rung:nth-child(4) { min-height: 290px }
.rung i { font-style: normal; display: inline-grid; place-items: center; width: 34px; height: 34px; border-radius: 50%; background: var(--navy); color: #fff; font-weight: 700; margin-bottom: 14px }
.rung b { display: block; font-size: 22px; margin-bottom: 8px } .rung span { font-size: 16px; color: var(--muted); line-height: 1.35 }
.rung em { position: absolute; top: 18px; right: 16px; font-style: normal; font-size: 12px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; padding: 4px 10px; border-radius: 999px; background: #ECE7DF; color: var(--navy) }
.rung.vg { border-color: var(--navy) } .rung.vg i { background: var(--lava) } .rung.vg em { background: var(--navy); color: #fff }
.peers { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px }
.peer { background: #fff; border: 1px solid var(--line); border-radius: 14px; padding: 22px 20px }
.peer small { display: block; font-size: 13px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--navy) }
.peer em { display: block; font-style: normal; font-size: 12.5px; color: var(--muted); margin: 2px 0 12px }
.peer b { display: block; font-size: 44px; line-height: 1; margin-bottom: 12px } .peer span { font-size: 15.5px; color: var(--muted); line-height: 1.4 }
.edge { margin-top: 28px; background: var(--navy); color: var(--light); border-radius: 14px; padding: 20px 26px; display: grid; grid-template-columns: 160px 1fr; gap: 20px; align-items: center }
.edge b { font-size: 20px; color: var(--lava) } .edge span { font-size: 18px; line-height: 1.4 } .edge span b { color: var(--light); font-size: inherit }
.src { margin-top: 16px; font-size: 12px; color: var(--muted) }
.cobrand { position: absolute; top: 56px; left: 80px; right: 80px; display: flex; justify-content: space-between; align-items: center }
.active .cobrand { animation: up .6s cubic-bezier(.2,.7,.2,1) both }
.cobrand .dbx { width: 190px; height: auto }
.aerion { display: flex; align-items: center; gap: 12px; color: var(--navy) }
.aerion b { display: block; font-size: 26px; letter-spacing: .18em; line-height: 1 }
.aerion small { display: block; font-size: 12px; letter-spacing: .32em; text-transform: uppercase; color: var(--muted); margin-top: 4px }
#bar { position: fixed; left: 0; bottom: 0; height: 4px; background: var(--lava); transition: width .4s ease; z-index: 5 }
#num { position: fixed; right: 18px; bottom: 12px; color: rgba(249,247,244,.55); font-size: 13px; z-index: 5 }
#hint { position: fixed; left: 50%; bottom: 14px; transform: translateX(-50%); color: rgba(249,247,244,.5); font-size: 13px; transition: opacity 1s; z-index: 5 }
@media (prefers-reduced-motion: reduce) {
  .a, .kick, h1, .logo, .cobrand { animation: none !important; opacity: 1 !important; transform: none !important }
  .fill, .lead .lf { transition: none !important; transform: none !important }
  .slide { transition: none }
}
@media print {
  html, body { overflow: visible; height: auto; background: none }
  #stage { position: static; transform: none !important; width: auto; height: auto }
  .slide { position: relative; width: 1280px; height: 720px; opacity: 1; visibility: visible; page-break-after: always; break-after: page }
  .a, .kick, h1, .logo, .cobrand { opacity: 1 !important; transform: none !important; animation: none !important }
  .fill, .lead .lf { transform: none !important; transition: none !important }
  #bar, #num, #hint { display: none }
}
@page { size: 1280px 720px; margin: 0 }
"""

JS = """
const PRINT = location.search.includes('print') || matchMedia('(prefers-reduced-motion: reduce)').matches;
const slides = [...document.querySelectorAll('.slide')], stage = document.getElementById('stage');
let i = Math.min(Math.max(parseInt(location.hash.slice(1)) - 1 || 0, 0), slides.length - 1);
function fit() { const s = Math.min(innerWidth / 1280, innerHeight / 720); stage.style.transform = `translate(-50%,-50%) scale(${s})`; }
function count(el) {
  const v = parseFloat(el.dataset.v), dec = +el.dataset.dec, pre = el.dataset.pre, suf = el.dataset.suf, t0 = performance.now(), dur = 1200;
  const f = (t) => { const p = Math.min((t - t0) / dur, 1), e = 1 - Math.pow(1 - p, 3);
    el.textContent = pre + (v * e).toLocaleString('en-US', {minimumFractionDigits: dec, maximumFractionDigits: dec}) + suf;
    if (p < 1) requestAnimationFrame(f); };
  requestAnimationFrame(f);
}
function show(n) {
  i = Math.min(Math.max(n, 0), slides.length - 1);
  slides.forEach((s, j) => s.classList.toggle('active', j === i));
  if (!PRINT) slides[i].querySelectorAll('.cnt').forEach(count);
  document.getElementById('bar').style.width = ((i + 1) / slides.length * 100) + '%';
  document.getElementById('num').textContent = (i + 1) + ' / ' + slides.length;
  history.replaceState(null, '', '#' + (i + 1));
}
addEventListener('keydown', (e) => {
  if (['ArrowRight', 'ArrowDown', 'PageDown', ' ', 'Enter'].includes(e.key)) { e.preventDefault(); show(i + 1); }
  else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace'].includes(e.key)) { e.preventDefault(); show(i - 1); }
  else if (e.key === 'Home') show(0); else if (e.key === 'End') show(slides.length - 1);
  else if (e.key === 'f' || e.key === 'F') { document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen(); }
});
addEventListener('click', (e) => show(e.clientX > innerWidth / 3 ? i + 1 : i - 1));
addEventListener('resize', fit);
setTimeout(() => document.getElementById('hint').style.opacity = 0, 3500);
fit(); show(i);
"""

html = ["<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>VentoGuard · {CUSTOMER}</title>",
        "<link href='https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap' rel='stylesheet'>",
        f"<style>{CSS}</style></head><body><div id='stage'>"]
for n, s in enumerate(SLIDES, 1):
    cls = f"slide {s['kind']}".strip()
    kick = f"<div class='kick'>{s['kicker']}</div>" if s["kicker"] else ""
    html.append(f"<section class='{cls}' data-n='{n}'>{kick}<h1>{s['title']}</h1>{s['body']}"
                f"<div class='brand'>VentoGuard · {CUSTOMER} · Databricks Data Intelligence Platform</div></section>")
html.append("</div><div id='bar'></div><div id='num'></div><div id='hint'>← → to navigate · F for full screen</div>")
html.append(f"<script>{JS}</script></body></html>")
(HERE / "VentoGuard_deck.html").write_text("\n".join(html))

md = [f"<!-- Generated by deck/build_deck.py from deck/numbers.json. {CUSTOMER} is a fictional customer; all data is synthetic. -->"]
for n, s in enumerate(SLIDES, 1):
    block = (f"_Slide {n} · {s['kicker']}_\n\n" if s["kicker"] else f"_Slide {n}_\n\n") + s["md"]
    if s["notes"]:
        block += f"\n\n> Speaker notes: {s['notes']}"
    md.append(block)
(HERE / "VentoGuard_deck.md").write_text("\n\n---\n\n".join(md) + "\n")

chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=6000",
                f"--print-to-pdf={HERE / 'VentoGuard_deck.pdf'}", f"file://{(HERE / 'VentoGuard_deck.html').resolve()}?print=1"], check=True,
               capture_output=True)
print("deck built:", len(SLIDES), "slides")
