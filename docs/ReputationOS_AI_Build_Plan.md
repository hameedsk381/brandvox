# ReputationOS AI — Build Plan (Compressed 12-Month Execution)

> **Status note (2026-07-03):** strategy document, not a status document. For current product
> state and the active milestone see `product-roadmap.md` v2.0 (built & hardened, pre-revenue,
> Phase 6 = first paying customers; Phase 5 breadth frozen). Any completion claims below predate
> the July 2026 re-baseline.

> Based on v2 strategic roadmap with timing compression for fastest differentiation.

---

## Guiding Principle

Ship the **narrative-changing feature first**, then build the moat.

The existing product is well-engineered but undifferentiated. Every phase below is ordered to maximize how the market perceives ReputationOS — not just what the code does.

---

## Phase 0 — Quick Wins (Week 1, no code)

### Pricing (Day 1)

| Plan | Current | New | Rationale |
|---|---|---|---|
| Starter | $19 | $49 | $19 signals "cheap tool" |
| Pro | $49 | $149 | Covers AI inference costs |
| Agency | — | $399 | New tier for agencies with white-label |
| Enterprise | Custom | Custom | Unchanged |

Change in `schemas/billing.py`.

### Messaging (Day 2)

Replace every feature label with an outcome statement. Zero code — just copy in UI labels, landing copy, and docs:

| Before | After |
|---|---|
| AI Reply Generator | Reply to 95% of reviews in under 30s |
| Sentiment Analysis | Spot operational fires before they cost a star |
| Competitor Tracking | Know where you rank vs every local competitor |
| Crisis Detection | Stop a brand crisis before it goes viral |
| Dashboard | Your brand health at a glance |
| Reports | Executive-ready insights in one click |
| Brand Voice | Sound like your brand, not a bot |
| Review Inbox | Never miss a review again |

### Sidebar rename (Day 2)

`Dashboard` → `Brand Health`  
`Analytics` → `Insights`  
`Settings` → `Studio`

---

## Phase 1 — Review Growth Engine (Weeks 1-4)

**Narrative shift:** "We don't just manage reviews — we generate more 5-star reviews."

### Week 1-2: QR + NFC Campaigns

| Deliverable | Effort | Details |
|---|---|---|
| `ReviewCampaign` model | 0.5d | `id, agency_id, name, type(qr/nfc/sms/email/whatsapp), target_url, redirect_url, created_at` |
| QR code generator endpoint | 1d | `POST /api/review-campaigns` returns PNG + short URL. Use `qrcode` Python lib. |
| NFC card config page | 0.5d | URL generator for NFC tags. Branded landing page that opens Google Review link. |
| Campaign management UI | 1.5d | `/dashboard/review-campaigns` — list, create, download QR, copy NFC URL |

**Total: ~3.5 engineering days**

### Week 2-3: SMS + Email + WhatsApp Campaigns

| Deliverable | Effort | Details |
|---|---|---|
| `CampaignContact` model | 0.5d | `id, campaign_id, phone/email, status(pending/sent/opened/converted), sent_at` |
| SMS integration (Twilio) | 1d | `POST /api/review-campaigns/{id}/send-sms` — send review link via Twilio API |
| Email integration (SendGrid) | 1d | `POST /api/review-campaigns/{id}/send-email` — branded email with review link |
| WhatsApp integration (Twilio) | 1d | WhatsApp Business API via Twilio |
| Campaign analytics | 1d | Send rate, open rate, conversion rate per campaign |

**Total: ~4.5 engineering days**

### Week 3-4: Review Funnel + Employee Leaderboard

| Deliverable | Effort | Details |
|---|---|---|
| Review funnel flow | 2d | Happy customer (4-5★) → Google review link. Unhappy (1-3★) → private feedback form. Saves negative feedback internally instead of public bad review. |
| Employee leaderboard | 1.5d | Track which employees generate the most reviews. Per-location leaderboard with rewards configuration. |
| Review generation dashboard | 1d | Total reviews generated, conversion rate, top campaigns, top performers |

**Total: ~4.5 engineering days**

### Phase 1 Total: ~12.5 engineering days = 3 weeks with 1 dev

### Go-to-Market Impact

> "Get 30% more Google reviews in 30 days."

This is the headline competitors cannot match. Most platforms manage reviews. ReputationOS *generates* them.

---

## Phase 2 — Local SEO Intelligence (Weeks 5-8, parallel with Phase 3 start)

**Narrative addition:** "We grow your visibility and your reviews."

### Week 5-6: GBP Audit + Keyword Rankings

| Deliverable | Effort | Details |
|---|---|---|
| Google Business Profile audit API | 2d | Scrape GBP completeness score, missing fields, photo count, post frequency. AI generates optimization checklist. |
| Local keyword ranking tracker | 2d | Track rankings for "near me" keywords (e.g., "best pizza Brooklyn"). Manual keyword input + daily rank check via Google Maps API / SERP scraping. |
| `SeoProfile` model | 0.5d | `id, location_id, gbp_completeness_score, keyword_rankings JSONB, last_audit_at` |
| Audit results UI | 1.5d | `/dashboard/seo` — completeness score, optimization checklist, keyword rankings table |

### Week 7-8: Maps Competitor Tracking + AI Recommendations

| Deliverable | Effort | Details |
|---|---|---|
| Google Maps competitor visibility | 1.5d | Track competitor rankings for same keywords. Side-by-side Maps visibility. |
| Citation/NAP monitoring | 2d | Check NAP consistency across top directories (Yelp, Foursquare, YellowPages, etc.). Flag mismatches. |
| AI SEO recommendations | 1d | Weekly AI-generated SEO report: "Add 3 photos this week to improve GBP completeness from 60% → 80%" |
| Photo/post scheduler | 1d | Schedule GBP posts and photo uploads with reminders |

### Phase 2 Total: ~12.5 engineering days = 3 weeks with 1 dev

---

## Phase 3 — Customer Intelligence Graph (Start Week 6, run through Month 5)

**Narrative addition:** "We connect feedback to business outcomes."

Build the data plumbing in parallel with Phase 2, then layer insights on top.

### Data Connectors (Weeks 6-10)

| Connector | Effort | Priority |
|---|---|---|
| Support tickets (manual/Zendesk API) | 2d | High |
| Website chat (export existing) | 1d | High |
| CRM contacts (manual CSV import) | 1.5d | Medium |
| Orders/transactions (manual import) | 1.5d | Medium |
| Email feedback (forward-to-mailbox) | 2d | Low |

### Customer Intelligence Graph (Weeks 8-12)

| Deliverable | Effort | Details |
|---|---|---|
| `CustomerProfile` model (enhance existing) | 1d | Merge with touchpoint data from all connectors. Enriched with sentiment history, visit frequency, churn signals. |
| AI root-cause analysis engine | 3d | "Why are ratings dropping at the Downtown location?" — AI correlates review sentiment with operational data (staff changes, wait times, new menu items). |
| Customer segmentation | 1.5d | Segments: promoters, at-risk, detractors, high-value, lost. Per-location breakdown with AI recommendations. |
| Operational insights dashboard | 2d | `/dashboard/intelligence` — root-cause analyses, segment trends, recommended actions. |

### Phase 3 Total: ~15.5 engineering days (overlaps with Phase 2, so ~6-8 weeks calendar time)

### Go-to-Market Impact

> "We can tell you exactly why customers are leaving and what to fix."

Competitors show metrics. ReputationOS shows **answers**.

---

## Phase 4 — Competitor Intelligence (Months 3-5, parallel)

**Narrative addition:** "We watch your competitors so you don't have to."

| Deliverable | Effort | Details |
|---|---|---|
| Competitor pricing monitoring | 2d | Track competitor pricing changes. Manual price input + monitoring alerts. |
| Campaign detection | 2d | Detect competitor ad campaigns, social activity spikes, new promotions. |
| New location alerts | 1d | Monitor for new competitor locations opening in the area. |
| Weekly AI competitor report | 1.5d | Automated report: "Your main competitor dropped their price by 15%. Here's the impact on your reviews." |
| Competitive intelligence dashboard | 2d | `/dashboard/competitor-intel` — trends, alerts, reports |

**Total: ~8.5 engineering days (parallel, so months 3-5)**

---

## Phase 5 — Brand Intelligence (Months 4-7, parallel)

**Narrative addition:** "We protect your brand everywhere, not just Google."

| Deliverable | Effort | Details |
|---|---|---|
| Social media monitoring (Instagram, FB, X, TikTok, YouTube) | 4d | Connect via APIs or RSS. Track mentions, sentiment, engagement. |
| News + blog + forum monitoring | 2d | RSS-based tracking for brand mentions across news, Reddit, blogs. |
| Brand sentiment dashboard | 2d | Unified brand health score across all channels. Cross-channel sentiment trends. |
| Influencer detection | 1.5d | Identify high-impact mentions from accounts with significant followers. |
| Viral risk alerts | 1.5d | ML-based virality probability estimation + early warning system. |

**Total: ~11 engineering days (parallel, so months 4-7)**

---

## Phase 6 — Revenue Intelligence (Months 6-12)

**Narrative capstone:** "We connect customer sentiment to revenue."

| Deliverable | Effort | Details |
|---|---|---|
| Revenue data connector | 2d | Manual revenue import or Stripe/Square API integration. Per-location revenue tracking. |
| Revenue impact analysis | 3d | "A 0.5★ drop in rating correlates with a 12% revenue decline at this location." AI-powered correlation engine. |
| Churn prediction model | 2d | Predict churn risk per customer/location using review + engagement + operational data. |
| CLV insights | 1.5d | Customer lifetime value estimates based on review engagement and repeat business. |
| Marketing ROI recommendations | 2d | "Your Google Ads spend increased review volume by 8% but didn't affect ratings. Consider reallocating to reputation campaigns." |
| Executive AI Copilot | 3d | Natural language query: "What's our biggest revenue risk this quarter?" AI answers with data from all connected sources. |
| Executive business summary report | 2d | Automated monthly/quarterly executive brief: revenue trends, reputation health, competitive position, recommended actions. |

**Total: ~15.5 engineering days (months 6-12)**

---

## Summary: Compressed 12-Month Timeline

```
Month       1   2   3   4   5   6   7   8   9   10  11  12
           ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ───
Phase 0    ■■
(Quick Wins)

Phase 1    ■■■■
(Review Growth)

Phase 2         ■■■■
(Local SEO)

Phase 3              ■■■■■■■■■■■
(Customer Intel)     ─── parallel ───

Phase 4                   ■■■■■
(Competitor Intel)        ─── parallel ───

Phase 5                        ■■■■■■■
(Brand Intel)                  ─── parallel ───

Phase 6                              ■■■■■■■■■■■
(Revenue Intel)
```

## Engineering Resourcing

| Scenario | Devs | Calendar Time |
|---|---|---|
| Solo dev | 1 | 12 months |
| Small team | 2 | 6-7 months |
| Full team | 3 | 4-5 months |

## Narrative Arc (How the Market Sees ReputationOS)

| Phase | One-liner | Competitor Response |
|---|---|---|
| Now | "Another review platform with AI" | Ignore |
| After Phase 1 | "They generate reviews, not just manage them" | Notice |
| After Phase 2 | "They own local visibility too" | Concern |
| After Phase 3 | "They tell you WHY your business is struggling" | Threat |
| After Phase 4 | "They watch your competitors automatically" | Alarm |
| After Phase 5 | "They monitor your brand everywhere" | Panic |
| After Phase 6 | "They connect reputation to revenue" | Category killer |

## Pricing Alignment Per Phase

| Phase | Price Point | Sells To |
|---|---|---|
| Now | $49/$149/$399 | Agencies managing multiple clients |
| After Phase 1 | $79/$199/$499 | Add "Review Growth" as upsell |
| After Phase 2 | $99/$249/$599 | Add "Local SEO" as upsell |
| After Phase 3+ | $149/$349/$799 | Full platform, enterprise-ready |

## Key Assumptions & Risks

| Risk | Mitigation |
|---|---|
| Google Maps API rate limits / ToS changes | Use multiple data sources, cached results, manual fallback |
| Twilio/SendGrid costs for campaigns | Pass through as usage-based fee in Agency plan |
| Data connector complexity (CRM, orders) | Start with manual CSV import MVP, API connectors later |
| AI inference costs scale with usage | Cache aggressively, batch AI calls, use cheaper models for non-critical paths |
| Competitor monitoring accuracy | Human-in-the-loop validation, confidence scoring |
