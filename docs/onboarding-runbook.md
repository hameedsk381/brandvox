# Pilot Onboarding Runbook

> Roadmap Phase 6 deliverable: "onboarding runbook for the first 10 trials (manual-touch is fine; script what works)".
> Audience: whoever runs the pilot. One page per step; update after every onboarding — this document should get shorter as steps get automated.

## 0. Before any customer: Google API production access ⚠️ LONGEST LEAD TIME

Google Business Profile APIs ship with **quota 0**. Nothing syncs until Google approves access for the Google Cloud project used. Start this **weeks before** the first trial.

1. Create (or reuse) the production Google Cloud project.
2. Enable: My Business Account Management API, My Business Business Information API, Google My Business API (v4).
3. Request GBP API access at https://developers.google.com/my-business/content/prereqs — requires a business justification, the project number, and a Google account that manages at least one Business Profile. Approval typically takes 2+ weeks and may involve follow-up questions.
4. After approval, confirm quota > 0 under IAM & Admin → Quotas for the three APIs.
5. Configure the OAuth consent screen (external, production status — not "testing", which expires refresh tokens after 7 days) with scope `https://www.googleapis.com/auth/business.manage`.

**Decision to make once:** one central Google project (our credentials, agencies OAuth into it — one approval, we own quota) vs. per-agency projects (each agency waits on Google). For the pilot, use the **central project**; per-agency BYO-credentials remains supported by the schema (`Agency.google_oauth_client_id/secret`) for white-label customers later.

## 1. Provision the trial (day 0, ~15 min, manual)

1. Create the agency + first admin user (register flow, or seeded by us).
2. Set `subscription_plan=trial`, `trial_ends_at` = now + 14 days.
3. Create the agency's first client + location(s) with them on a call.
4. Record in the pilot tracker: agency name, contact, start date, # locations.

## 2. Connect Google (with the customer on the call)

1. Dashboard → Integrations → Connect Google Business Profile.
2. The person consenting must be an **owner/manager of the GBP listing**.
3. Map each location to its GBP location (Integrations page → map location).
4. Trigger the first sync; confirm reviews appear in the inbox.
5. If sync fails: check `last_sync_error` on the Integrations page. Most common causes: quota 0 (step 0 not done), consent screen in testing mode (expired refresh token), wrong Google account (no GBP access).

## 3. First AI reply (same call — this is the aha moment)

1. Open a recent negative-or-mixed review → Generate AI reply.
2. Show the 2 drafts, edit one together, approve, publish.
3. Confirm the reply appears on Google (may take a few minutes).
4. Set up their brand voice profile (tone, greeting/closing, phrases to avoid).
5. Configure smart rules. The built-in default is already safe: with no rules configured, every review gets AI drafts for approval and nothing auto-publishes; historical reviews imported on first sync never trigger automation. Only enable 4–5★ auto-reply once the customer trusts the drafts.

## 4. Instrumentation check (us, after the call)

`GET /api/analytics/activation` for the agency — verify `first_synced_at` and `first_ai_reply_at` are stamped. Log **time-to-first-sync** and **time-to-first-AI-reply** in the pilot tracker. Target: both under 30 minutes from account creation.

## 5. Week 1–2 cadence

- Day 2: check sync status for all their locations (ops runbook §5); fix silently before they notice.
- Day 3: 15-min check-in — are they in the review inbox? blockers?
- Day 7: set up one scheduled report (their logo, weekly, to their client) — this is the retention hook for agencies.
- Day 14: trial-end call — convert, extend, or exit-interview. **Every** churned trial gets an exit interview (roadmap success criterion).

## Pilot tracker template

| Agency | Contact | Start | Locations | TTF-sync | TTF-AI-reply | Weekly active? | Status |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
