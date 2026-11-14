# VentoGuard: presentation script

**Customer:** Aerion Windkraft AG (fictional German onshore wind operator, 4 farms, 120 turbines)
**In the room:** the COO (business stakeholder, funds the decision) and the Head of Data & Architecture (technical stakeholder, lives with the build)
**Length:** about 24 minutes, then Q&A up to 30 minutes
**Deck:** open deck/VentoGuard_deck.html in Chrome, press F for full screen, → to advance
**App:** https://ventoguard-7474660468503815.aws.databricksapps.com

## How to use this script

- **Bold lines are the ones to say word for word.** The rest can be in your own words.
- *Italic lines are stage directions:* where to look, what to click, when to pause.
- The structure is **tell → show → tell**: say what you will show, show it, then say what it means in € and KPIs.
- When you answer a question, **name the person**, answer at their level, then add one sentence for the other person.

## Before you start (5 minutes)

- Open the app and approve the Okta push. Check that the risk board shows 3 critical and 1 high turbine.
- Ask Genie the first suggested question once, so the SQL warehouse is warm.
- Open the deck on slide 1, full screen. Keep this script on a second screen.
- In the app, set "View as" to Operations, so the demo starts on the risk board.
- Open Work orders: only one order should be there, F01-T20 (P1, scheduled). If you created test orders while rehearsing, delete them, so the F03-T07 order you create live is the only one for that turbine.

## Slide 1 · Title (0:00–1:00)

*Look at both of them. Smile. Slow down.*

**"Thank you both for the time. When we last spoke, you told us that surprise gearbox failures were the biggest hit to your year."**

**"Today I want to show you what that is worth to you, the problem behind it, and then spend most of our time in the product, on one real Monday morning, from the first alert to a booked repair. At the end I'll ask you for one decision: an eight-week pilot on Hunsrück Höhe."**

**"Does that work for both of you?"**

*Wait for a nod. That is your demo setup.*

## Slide 2 · The problem (1:00–2:00)

**"Here's the pain behind that number."**

**"Gearboxes and main bearings drive 90 % of your unplanned cost. Every surprise gearbox costs about €430 k and keeps a turbine down for more than five weeks, mostly waiting for a crane and a spare."**

**"Hunsrück Höhe runs at 95.0 % availability, against a 97 % target."**

**"And the frustrating part: the warning signs were there two to five weeks before each failure, in your SCADA data and in your technicians' own notes. Nothing connected them."**

## Slide 3 · How the industry fixes it (2:00–3:00)

**"The industry has been on a journey from fixing failures to predicting them."**

*Point left to right along the steps.*

**"Step one is where most fleets start: fix it when it breaks, with fixed alarms. Step two adds sensors on each component. Steps three and four are where the leaders are now: AI across the whole fleet that predicts failures weeks ahead, and then plans the crew, the crane and the weather window."**

**"Aerion is not behind on data. You already have it. What's missing is one place that connects it."**

## Slide 4 · The competition (3:00–5:00)

*Look at the COO. This is the "why now".*

**"Your competitors and the turbine makers are already there. One leading turbine maker detects 99 % of drivetrain failures, up to three years ahead. Another monitors more than 51,000 turbines centrally. One utility saves between 15 and 95 % of the repair cost on major components."**

*Pause. Then pivot.*

**"But there's a catch, and it's your opportunity. Turbine makers see their own turbines. You run a mixed fleet, with Hansa Drives and NordGear gearboxes. Owning one governed view of every turbine is what keeps that margin inside Aerion."**

*If asked: "The names are anonymised, but every figure is that company's own public disclosure."*

## Slide 5 · Where the €4.2 M comes from (5:00–7:00)

**"So what is it worth to you?"**

**"Today you lose €11.3 M a year to unplanned drivetrain failures. With VentoGuard, €4.2 M of that comes back every year, net. That's after we deduct the cost of false alarms, and it assumes we only catch 75 % of failures."**

**"You also get 664 turbine-days of production back each year."**

**"How? We see failures 13 days ahead. That turns a five-week outage into a one-week planned swap in a low-wind window."**

**"Let me show you how."**

## Slide 6 · What you'll see (7:00–8:00)

*TELL before you SHOW.*

**"I'll walk you through one Monday morning as your reliability lead, in four steps: the risk board, the AI brief, the work order, and then a question to Genie."**

**"Watch for the moment a €400 k surprise becomes a planned job."**

*Switch to the app.*

## Live demo (8:00–16:00)

### Step 1 · Fleet risk: the 07:00 view

*Tell:* **"This is what your reliability lead opens at seven in the morning."**

*Show:* the KPI strip: 4 turbines at high or critical risk, €806 k avoidable if acted on now, 30-day availability, lost revenue.

*Click "Hunsrück Höhe" (badge 2) on the map. The map flies to the farm. Hover F03-T07.*

**"Every turbine is on the map at its real location. This one, F03-T07, has a 99.5 % chance of a gearbox failure in the next 14 days. Planning the repair now avoids €207 k. Recommended action: within 72 hours."**

*Optional: press Expand for the full-screen map, then Esc.*

*Land:* **"Not 120 alarms. Four turbines, sorted by money."**

### Step 2 · The AI brief (click F03-T07)

*Show:* failure probability, likely component, and "Strongest signals against the fleet": vibration +1.58 mm/s and bearing temperature +6 °C compared with the rest of the fleet on the same day. Scroll to the trend charts.

**"You can see the drift building for weeks."**

*Show the AI brief.*

**"The AI writes the brief for the dispatcher. It cites the sensor evidence and the technician's own note, in German: iron particles in the oil, a metallic whine. It gives the steps, the crew and the parts. And the business case: a planned repair saves about €207 k compared with waiting for the failure."**

*Land:* **"Your reliability lead makes this decision in two minutes, not a morning digging through SCADA and SAP."**

*Architect aside, look at them:* **"The score comes from an MLflow model in Unity Catalog. The brief comes from Claude through ai_query, grounded only on these numbers and notes. Every value on this screen sits in a governed gold table."**

### Step 3 · Plan the repair

*Click "Plan the repair", choose P1 (within 72 hours), then "Create work order". Open the Work orders page.*

**"One click, and the work order exists. It sits next to the F01-T20 gearbox swap your team already scheduled last week, and the value protected by open orders goes up."**

*Land:* **"The crane, the spare and the crew are now booked into a low-wind window. That's the five-week outage avoided."**

*Architect aside:* **"That's a transactional write to Lakebase Postgres, in the app's own schema. In the pilot we push it to SAP PM, so SAP stays the system of record."**

### Step 4 · Ask the fleet (Genie)

*Click "Ask the fleet", then the first suggested question: "Which wind farm lost the most revenue to unplanned failures, and which component caused it?" Open "Generated SQL".*

*Land:* **"Your asset manager gets that answer without a BI ticket. And you" — to the architect — "can see exactly which governed table it came from."**

### Step 5 · The COO's own screen

*Switch "View as" to Executive.*

*Tell:* **"And this is what you see, as COO, on the same Monday."**

*Show:* €4.19 M value per year (€2.73 M even at a 50 % catch rate), €11.33 M unplanned-cost run rate, 97.7 % availability against the 97 % target, and €806 k at stake now.

*Then the key insights. Read the first two out loud:* "Hunsrück Höhe runs 2.0 pp below the 97 % availability target" (the pilot farm) and "2 at-risk turbines have no work order yet".

**"Before I created that order, this said three. The order I just booked already shows up here, and the value protected went from €215 k to €421 k."**

*Point to "Decisions this week": about €374 k is still avoidable on the two turbines without an order.*

**"And this is the one decision that's still open for you this week."**

*Land:* **"You don't need to open a single turbine. You see the money, the risk, and the one decision that needs you."**

*Architect aside:* **"These are the same Lakebase tables as the operations screen, so the numbers agree everywhere. The value case is calculated live with the same model as this deck."**

*Optional: "View as → Asset management" for the Head of Asset Management (mean time to repair, crane share, supplier and age cohorts, maintenance calendar).*

*Switch back to the deck, slide 7.*

### If the app or the network fails

**"Let me show you the same moment from this morning's run."** Use slides 6 and 7, and quote the F03-T07 brief. Stay calm; it's a prototype, and the evidence is in the repo.

## Slide 7 · What it means (16:00–17:00)

*TELL after you SHOW.*

**"So, four clicks. The week starts with the turbines that matter. A decision in minutes instead of a morning. The crane booked into a low-wind window. And answers without a BI ticket."**

**"Run that every morning across the fleet, and that's the €4.2 M a year."**

## Slide 8 · Proof (17:00–18:00)

**"Does it work? We tested it on failures the model had never seen. Eight out of eight were flagged in advance, with a median of 13 days' warning."**

**"And the four turbines on today's board are exactly the four that are degrading right now."**

*Concede the caveat yourself, before they raise it:*

**"To be clear, this prototype runs on synthetic data, so your real numbers will be lower. That's why the value case assumes only 75 %, and why the pilot measures the real number."**

## Slide 9 · Value for the COO (18:00–19:00)

*Look at the COO.*

**"€4.2 M a year, net. And if we only catch half the failures, it's still €2.7 M."**

**"It shows up in three places: lower corrective O&M, since the crane alone is about €120 k per gearbox; more revenue, with +1.5 points of availability protecting your PPA volumes; and lower risk."**

**"The run cost is serverless and scales to zero. We'll measure it exactly in the pilot. One avoided gearbox covers it many times over."**

## Slide 10 · Value for Asset Management (19:00–20:00)

**"For your Head of Asset Management, this is the move from firefighting to a planned maintenance calendar."**

**"Thirteen days matches your crane booking and spare-pool lead times. Every alert explains itself: the component and the three signals behind it. Your technicians' 519 notes, in German and English, now actually raise the risk score. And the KPIs they're measured on come from governed tables: availability, mean time to repair, corrective versus planned, and O&M cost per MWh."**

## Slide 11 · How it works (20:00–21:00)

*Look at the architect. One breath.*

**"One governed platform from raw SCADA to the dispatcher's screen. Lakeflow ingests the data. Unity Catalog governs it. The ML model and the AI briefs make it intelligent. Lakebase serves it in milliseconds and stores the work orders. And the app and Genie are where the business works."**

**"It's one daily job, deployed as one bundle, on open formats: Delta, Postgres and MLflow. Happy to go as deep as you like."**

## Slide 12 · Trust (21:00–22:00)

**"Six things you'd ask me about anyway: data quality checks dropped 7,717 bad readings before they reached the model; technician names are masked in every tool, Genie included; no model goes live without passing a quality gate; the AI briefs only use measured facts; every number traces back to its raw file; and the app sees only what it needs."**

## Slide 13 · The ask (22:00–24:00)

**"Here's what I'm proposing: eight weeks on Hunsrück Höhe."**

**"In weeks one and two we connect your real SCADA and SAP PM data. In weeks three and four we retrain the model with your reliability lead. From week five it runs live, in shadow mode, so your crews still decide. In week eight we make a go or no-go decision on the euros actually avoided."**

**"So I need two decisions from you today: your sponsorship, and access to 24 months of SCADA and maintenance data."**

**"Can we agree on that?"**

*Then stop talking. Let them answer.*

## Q&A: business stakeholder (COO)

Pattern: **headline answer → evidence → bridge to the business → "Does that answer it?"**

| Question | What to say |
|---|---|
| "What does this cost?" | "The run cost is small next to one gearbox. It's serverless and scales to zero, so nothing runs overnight. We measure it exactly in the pilot, and it's part of the go/no-go." (Backup slide 14) |
| "Your data is synthetic. Why should I believe €4.2 M?" | "Fair challenge. That's why the case assumes only 75 %, and why even at 50 % it's €2.7 M. The cost inputs, the crane, the downtime and the prices, are your operating reality. The pilot replaces my assumptions with your measured numbers in eight weeks." |
| "What about false alarms?" | "A false alarm costs one inspection, about €2.5 k. A miss costs €430 k. We already deduct €194 k a year for false alarms, and the pilot target is at most one per ten turbines per month." |
| "How fast do I see value?" | "First live alerts in week five, a go/no-go on measured euros in week eight. One avoided gearbox during the pilot pays for the year." |
| "What's the risk to operations?" | "During the pilot, none. It runs in shadow mode, your crews decide, and SAP stays the system of record." |
| "Why not just use our OEM's monitoring?" | "Keep it. Their sensor data becomes another input. But the OEM sees one brand of turbine. This combines all your turbines, your technicians' notes and the cost of downtime, and you own it." |
| "Are those competitor numbers comparable to ours?" | "Not one-to-one, and I won't pretend they are. They're each company's own published figures, with different scopes. The point is the direction: everyone serious is predicting failures with data. Our number comes from your cost model, and the pilot measures it." |
| "Do I need to hire data scientists?" | "No. It runs as one daily job. Your team works in the app and asks Genie. We'd enable one engineer on your side during the pilot." |

## Q&A: technical stakeholder (Head of Data & Architecture)

Pattern: **real detail → one sentence back to the COO.**

| Question | What to say | Bridge to the COO |
|---|---|---|
| "How does it integrate with our SCADA historian and SAP PM?" | "Today, Auto Loader from a Unity Catalog volume. In the pilot, historian exports or Zerobus streaming for SCADA, and Lakeflow Connect for SAP PM. Work orders go back to SAP PM through its API, so SAP stays the system of record." | "So your crews don't learn a new system." |
| "How do you handle bad sensor data?" | "Lakeflow expectations drop impossible readings, 7,717 in this run: 999 °C oil, negative wind. It's all visible in the pipeline event log. And the features compare each turbine with the rest of the fleet on the same day, so weather doesn't look like a failure." | "The alerts aren't driven by broken sensors." |
| "How did you validate the model? What about leakage?" | "A time split: trained before August, tested on August and September, which it never saw. A gradient-boosted model with a 14-day horizon. A quality gate has to pass before it goes live, and every run is logged in MLflow." | "A bad model can't reach your dispatchers." |
| "Drift and retraining?" | "In the pilot: monitoring on features and predictions, a monthly retrain through the same job, and challenger versus champion through the same gate." | |
| "Can the AI hallucinate a repair?" | "The brief only uses the score, the measured signals and the technician's notes, and the prompt forbids invented numbers. The output is tagged as AI-generated and shown next to the evidence, and a human approves every work order." | "The AI writes the brief; your engineer makes the call." |
| "Where does our data go? Which LLM?" | "Claude, through Databricks Foundation Model APIs, called from SQL inside your governed workspace. Unity Catalog permissions apply, and every call is auditable." | |
| "GDPR? Technician names?" | "Names carry a classification tag and a column mask. Only reliability leads see them, in every tool including Genie. The app runs as a least-privilege service principal." | "Compliant by default, and friendly to your works council." |
| "Why Lakebase and not just the warehouse?" | "The app needs millisecond reads and real transactions for work orders. Analytics stay in Delta, operations in Postgres, and both are governed." | |
| "Scale and lock-in?" | "About 3.3 million rows of ten-minute SCADA today, on serverless. Open formats throughout: Delta, Postgres, MLflow. One bundle with dev and prod targets." | "Rolling out to all four farms is configuration, not a project." |

## Delivery reminders

- **Say the first € number within two minutes.**
- **Use their roles when you switch level:** "For you, as COO… and for you, the detail is…"
- **Handle objections in four steps:** "That's the right question" → answer → evidence → "Does that answer it?"
- **Never claim more than the evidence.** Raise the synthetic-data caveat yourself.
- **End with the ask, then stay silent.**
