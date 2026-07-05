# Demo Script (Restaurant-Agency Wedge)

> Roadmap Phase 6 deliverable. Target: 15 minutes, same script every time (consistency is a Phase 1 success criterion).
> Demo tenant: seeded data (`app/seed/seed_data.py`) — **Stellar Digital Agency** → **Tasty Burger Co.** (2 locations). Login: `agency@stellar.digital` / `demo1234` (rotate this password on any internet-facing demo instance).

## Positioning (say this first, 1 min)

"You manage reviews for a dozen restaurant clients. Every morning someone on your team reads Google reviews, decides which need answers, writes replies in each client's voice, and at month-end builds a report. ReputationOS is that person, minus the manual work — and it runs under **your brand**, so to your clients it looks like your own product."

Sell the narrow core: **ingest → reply → report**. Phase 5 features (forecasting, copilot, journeys) are garnish — show only if asked.

## Beat 1 — Agency view (2 min)

- Log in as Stellar Digital admin. Point out the tenant switcher: four clients, one login.
- "Each of your clients gets their own workspace, users, and permissions. Your junior staff can see one client; you see everything."

## Beat 2 — Review inbox (3 min)

- Switch to Tasty Burger Co. Open the review inbox.
- Filter: 1–3 stars, unreplied, last 30 days. "This is the morning queue — the only reviews a human needs to look at."
- Open a negative review. Show sentiment + extracted topics ("slow service", "cold food"). "This is how you spot an operational problem, not just a bad day."

## Beat 3 — AI reply, the aha moment (4 min)

- Generate AI reply → two drafts appear, in Tasty Burger's brand voice.
- Edit one line live ("you always stay in control"), approve, show it queued to publish to Google.
- Show the brand voice profile: tone, greeting, closing, banned phrases. "Set once per client; every draft sounds like them, not like ChatGPT."
- Show smart rules: 5★ can auto-thank; 1★ always escalates to a human. "You choose the automation level per client."

## Beat 4 — White-label report (3 min)

- Dashboard: reputation score, response rate, rating trend.
- Generate a PDF report — **their logo and colors**, not ours (branding settings).
- Scheduled reports: "every Monday 8am this lands in your client's inbox with your branding. That's your monthly retainer justifying itself."

## Beat 5 — Close (2 min)

- Pricing (finalize after the 10 discovery calls; anchor per-location per-month).
- Trial: "14 days, we onboard your first client together on a 30-minute call — you'll see your own reviews and your first AI reply inside that call."
- Ask: "Which client would you connect first?"

## Q&A crib sheet

| Question | Answer |
|---|---|
| Only Google reviews? | Google is the pilot focus (70%+ of restaurant review volume); manual import covers the rest today; more sources on the roadmap when a paying customer pulls for them. |
| Will AI post without approval? | Only if you turn that rule on. Default is human approval; 1–3★ can never auto-reply. |
| Where's our data? | Isolated per tenant, OAuth tokens encrypted at rest, GDPR export/delete built in. Security doc available. |
| Can our clients log in? | Yes — client-scoped roles see only their own workspace, under your branding. |

## Demo hygiene

- Before every demo: fresh browser profile, seeded database (`seed_data.py`), dark mode per prospect vibe.
- Never demo against a real customer's tenant.
- After each demo, log: date, agency, objections, next step (feeds the demo-to-trial KPI).
