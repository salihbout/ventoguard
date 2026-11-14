# VentoGuard: role-play playbook (20–30 min)

**Audience:** the **COO** (business stakeholder, funds the decision) and the **Head of Data / Architect** (technical stakeholder, has to live with the build).
They are both in the room for one session.
**Deck:** `deck/VentoGuard_deck.pdf`, 15 slides. Slides 1–12 are the main story and slides 13–15 are backup for Q&A.
**App:** https://ventoguard-7474660468503815.aws.databricksapps.com
**Rule of thumb:** tell → show → tell. Every screen ends with *"what this means for you is …"*.

## Scoring rubric → where you earn it

| Rubric item | Where in this flow |
|---|---|
| Demo setup (customer, problem, what you'll show) | Slide 2, *before* any numbers or screens |
| Tell-show-tell | Slide 5 (tell) → live app (show) → slide 6 (tell) |
| Value at executive altitude | Slides 3, 8 and 12. Talk in € and availability, never in features |
| Reading the room | Q&A bank below: lead with the headline, then the detail, then bridge back to €. Name who you are answering |
| Professionalism and objections | Acknowledge → answer → evidence → bridge. Never defensive. Concede the synthetic-data caveat up front |

## Timed run of show (≈ 22 min + Q&A)

| Min | Slide / screen | Say (key lines) |
|---|---|---|
| 0–1 | **1 Title** | "Thank you both. I'll be brief on slides and spend most of the time in the product." |
| 1–3 | **2 Why we're here** *(setup)* | "You run 120 turbines on 4 farms. Last year surprise drivetrain failures cost you **€11.3 M**, and Hunsrück Höhe sits at **95 %** availability against a 97 % target. In the next 30 minutes: the outcome, then a **live Monday morning** from alert to booked repair, then proof and how it's built, then **one decision**: an 8-week pilot." Check: *"Is that the right use of your time?"* |
| 3–5 | **3 Outcome** | "The outcome is **€4.2 M a year net** and **+1.5 points of availability**. We get there by seeing failures **13 days ahead**, so a five-week outage becomes a one-week planned swap." |
| 5–6 | **4 Problem in your KPIs** | "Gearboxes and main bearings are 90 % of the cost, about **€430 k** per surprise gearbox. The signals were in SCADA and in your technicians' German notes weeks ahead. Nobody connected them." |
| 6–7 | **5 What I'll show you** *(tell)* | "I'll walk one Monday morning as your reliability lead: **risk board → AI brief → work order → a question to Genie**. Watch for the moment a €400 k surprise becomes a planned job." |
| 7–15 | **LIVE APP** *(show)* | See the demo click path below |
| 15–16 | **6 What you just saw** *(tell)* | "Four clicks. The week starts with the 4 turbines that matter, a decision in minutes, the crane booked in a low-wind window. Run every morning, that's the €4.2 M." |
| 16–17 | **7 Proof** | "Every hold-out failure was flagged in advance, 8 of 8. And the 4 turbines on today's board are exactly the 4 degrading now. The data is synthetic, so we assume only 75 % on your real fleet, and the pilot will measure it." |
| 17–18 | **8 For the COO** | Look at the COO: "€4.2 M net. If we only catch half, still **€2.7 M**. The pilot measures the run cost exactly, and one avoided gearbox covers it many times over." |
| 18–19 | **9 For Asset Management** | Look at the domain owner: "13 days matches your crane and spare-pool lead times. Every alert is explained, and your team's notes finally count." |
| 19–20 | **10 How it works** | Look at the architect: "One governed platform, from raw SCADA to the dispatcher's screen. One job, one bundle, open formats. Happy to go deep." |
| 20–21 | **11 Trust** | "Data quality, GDPR masking, model gate, grounded AI, and lineage from the raw file to the risk board." |
| 21–22 | **12 The ask** | "8 weeks on Hunsrück Höhe, shadow mode from week 5, go/no-go on measured € avoided. **Two decisions today:** your sponsorship and access to 24 months of SCADA and CMMS exports. Can we agree on that?" |
| 22–30 | **Q&A** | Use the bank below. Jump to slides 13–15 when it helps |

## Live demo click path (≈ 8 min)

Before each screen, say one line about what they'll see. After it, say one line about what it means.

1. **Fleet page ("Fleet risk")**
   - *Tell:* "This is what your reliability lead opens at 07:00."
   - *Show:* the KPI strip: turbines at high or critical risk (**4**), **avoidable cost if acted on now (≈ €806 k)**, availability over 30 days, lost revenue over 30 days. Point to the farm map coloured by risk, then the **Risk board**: **3 CRITICAL, 1 HIGH**, ranked by € at stake.
   - *Land:* "Not 120 alarms, just 4 turbines, sorted by money."
2. **Click F03-T07, which opens the turbine page**
   - *Show:* failure probability over 14 days (~99 %) and the most likely component (gearbox). Under **"Strongest signals against the fleet"**, the vibration is +1.58 mm/s and the bearing temperature +6 °C *versus the rest of the fleet on the same day*. Then the trend charts, where the drift is visible for weeks.
   - *Show the AI brief:* the diagnosis cites the sensors **and** the technician's note ("metallic whine, iron in the oil"), with steps, crew and parts. The business case says a **planned repair saves ≈ €207 k**.
   - *Land:* "Your lead makes this decision in two minutes, not a morning in SCADA and SAP."
   - *Architect aside:* "The score comes from the MLflow model in Unity Catalog, the brief from Claude via `ai_query`, grounded only on these numbers and notes. Every value here is in a governed gold table."
3. **"Plan the repair", then Create work order** (P1 · within 72 hours)
   - *Show:* the order appears on the **Work orders** page and "Value protected by open orders" goes up.
   - *Land:* "The crane, the spare and the crew are booked into a low-wind window. That's the five-week outage avoided."
   - *Architect aside:* "This is a transactional write to Lakebase Postgres, in the app's own schema. In the pilot it goes to SAP PM."
4. **"Ask the fleet" (Genie)**
   - *Show:* click *"Which wind farm lost the most revenue to unplanned failures, and which component caused it?"* and open **Generated SQL**.
   - *Land:* "Your asset manager gets that answer without a BI ticket, and the architect can see exactly which governed table it came from."

**Fallback if the app or the network fails:** stay calm and say *"Let me show you the same moment from this morning's run."* Then use slide 5, which has the brief verbatim, and slide 6. All outputs are also in `evidence/app.md` and `evidence/genie_conversations.md`.

## Q&A bank: two altitudes per answer

Pattern: **answer the asker first** at their altitude, then add one sentence for the other person.
For example: *"[to the architect] … detail … [to the COO] what that means for you is …"*

### Business stakeholder (COO): cost, risk, time to value

| Question | Headline answer (exec altitude) | If they push |
|---|---|---|
| "What does this cost?" | "The run cost is small next to one gearbox. It's serverless and scales to zero, with no cluster running overnight. The pilot measures it to the euro from the billing tables, and it's a go/no-go input." | Slide 13. One avoided gearbox ≈ €430 k. Don't quote a platform price you haven't measured |
| "Your data is synthetic. Why believe €4.2 M?" | "Fair challenge. That's why the case assumes only 75 %, and why at 50 % it's still €2.7 M. The pilot replaces my assumptions with your measured numbers in 8 weeks." | Slide 7 caveat. The cost inputs (crane, downtime, prices) are your operating reality, not model output |
| "What if it raises false alarms?" | "A false alarm costs an inspection, about €2.5 k. A miss costs €430 k. We already deduct €194 k a year for false alarms, and the pilot target is ≤ 1 per 10 turbines per month." | Tiers and € ranking keep the list short |
| "How fast do I see value?" | "First live alerts in week 5, a go/no-go on measured € in week 8. One avoided gearbox in the pilot pays for the year." | Slide 12 / 13 |
| "What's the risk to operations?" | "Zero during the pilot. It runs in shadow mode, your crews decide, and SAP stays the system of record." | Human approves every work order |
| "Why not our OEM's condition-monitoring system?" | "Keep it. CMS spectra become another input. The OEM sees one component. This combines SCADA, CMS, your technicians' notes and the cost of downtime across the whole fleet, and you own it." | Multi-vendor fleet (Hansa Drives vs NordGear insight) |
| "Do I need to hire data scientists?" | "No. It runs as one daily job. Your team works in the app and asks Genie. We'd enable one engineer on your side during the pilot." | Everything is code in one bundle |
| "What do you need from me today?" | "Two things: your sponsorship for Hunsrück Höhe, and access to 24 months of SCADA and CMMS exports." | Close |

### Technical stakeholder (architect / data lead): architecture, data quality, security, integration

| Question | Detail answer | Bridge to the COO |
|---|---|---|
| "How does it integrate with our SCADA historian and SAP PM?" | "Today: Auto Loader from a UC Volume. Pilot: historian exports or Zerobus streaming for SCADA, Lakeflow Connect for SAP PM / CMMS. Work orders are written back to SAP PM via its API, so SAP stays the system of record." | "So no new system for your crews to learn." |
| "How do you handle bad sensor data?" | "Lakeflow expectations at silver drop physically impossible readings, 7,717 in this run (999 °C oil, negative wind). They're visible in the pipeline event log and can be alerted on. Features are relative to the fleet on the same day, so weather doesn't look like failure." | "So the alerts aren't driven by broken sensors." |
| "How did you validate the model? Leakage?" | "Time split: trained before August, tested Aug–Sep. The model never saw the test period. HistGradientBoosting, 14-day horizon. There's a quality gate (PR-AUC ≥ 0.30, ≥ 60 % caught ≥ 3 days ahead) before `@champion` moves, and metrics plus back-test tables are logged in MLflow." | "A bad model can't reach your dispatchers." |
| "Drift and retraining?" | "In the pilot: monitoring on features and predictions, a monthly retrain through the same job, and challenger vs champion on the gate." | |
| "Can the LLM hallucinate a repair?" | "The brief is grounded only on the score, measured residuals and the technician's own notes, and the prompt forbids invented numbers. Output is tagged `ai_generated` and shown next to the evidence, and a human approves every work order." | "The AI writes the brief, your engineer makes the call." |
| "Where does our data go? Which LLM?" | "Claude via Databricks Foundation Model APIs, called from SQL with `ai_query` inside the governed workspace. It's covered by UC permissions and is auditable." | |
| "GDPR? Technician names?" | "Names carry the `class.name` tag and a UC column mask. Only reliability leads see them, in every tool including Genie. The app runs as a least-privilege service principal." | "Compliant by default, works council friendly." |
| "Why Lakebase and not just query the warehouse?" | "The app needs millisecond reads and transactional writes (work orders). Gold tables sync to Postgres after scoring. Analytics stay in Delta, operations in Postgres, and both are governed." | |
| "Latency and freshness?" | "A daily run at 05:00 suits a 14-day horizon. The sync can be switched to triggered or continuous if intraday matters." | |
| "Scale and lock-in?" | "About 3.3 M rows of 10-minute SCADA, on serverless. Open formats throughout: Delta, Postgres, MLflow. One bundle with dev and prod targets." | "Rolling out to all 4 farms is configuration, not a project." |
| "Who operates it?" | "One Lakeflow Job with six tasks, CI/CD through the bundle, and run history and alerts in Jobs." | |

## Delivery reminders

- **Lead with the outcome.** Say the first € number within 2 minutes.
- **Use their names and roles** when you switch altitude: *"For you, [COO] … and for [architect], the detail is …"*
- **Handle objections in four steps:** acknowledge ("That's the right question") → answer → evidence (slide or number) → check ("Does that address it?").
- **Never claim more than the evidence.** Concede the synthetic-data caveat yourself, before they raise it.
- **Close with the ask** and silence. Let them answer.

## Rehearsal plan (do this out loud, with a timer)

1. **60-second opener, 3 times.** Say this from memory, without slides, until it lands at about 60 s: *"You run 120 turbines on four farms. Surprise drivetrain failures cost you €11.3 M last year, and Hunsrück is at 95 % availability against 97 %. The warning signs were in your SCADA and your technicians' notes weeks before. VentoGuard connects them and flags failures 13 days ahead, which is worth €4.2 M a year net. I'll show you one Monday morning, from alert to booked repair, then ask for an 8-week pilot."*
2. **Demo only, 3 runs, under 8 minutes each.** Say the tell line before every click and the "what it means" line after it. If a run goes over 8 minutes, cut words, not steps.
3. **Objection drill, one round per stakeholder.** Pick 5 questions from each table at random and answer each in under 45 s: headline first, then evidence, then the bridge. Record yourself once and check that you name the asker and switch altitude.
4. **Hostile round.** Practise the three hardest questions back to back: *"Synthetic data, why believe it?"*, *"What does it cost?"* and *"Can the LLM hallucinate a repair?"*. Stay calm, concede the caveat, and pivot to the pilot.
5. **Full dress rehearsal, timed to 22 minutes + Q&A**, with the deck and the live app. Then do the real attempt. You can retake it with any resubmission.

Tip: a mock role-play with Claude playing the COO and the architect is a cheap extra round. Ask it to interrupt, push back on cost and data quality, and score you against the five rubric items.

## Pre-demo checklist

- [ ] App loads and the Okta push is approved, *before* the session
- [ ] The risk board shows 3 CRITICAL / 1 HIGH. Data is frozen at the last scoring run (score date 2026-10-09) because the job schedule is paused on purpose
- [ ] Remove old test work orders, or explain them as "from last week"
- [ ] Genie answers the first suggested question (warm the SQL warehouse 5 min before)
- [ ] Deck PDF open on slide 1, with this playbook on a second screen
