# Stripe Integration Design
**Date:** 2026-05-12

## Context

FSA website currently processes enrollments through GoHighLevel (GHL) at a separate domain (`enrollment.fullsteamahead.ca`). The exit-intent modal generates discount coupons via the GHL API proxied through nginx. GHL affiliate tracking is being abandoned entirely.

The goal is to move all payment handling to Stripe: hosted checkout pages, the Stripe customer portal for subscription management, and Stripe-generated promo codes in the exit-intent modal. GHL is retained only for post-purchase contact creation and course access tagging — triggered by a custom webhook middleware service.

---

## Architecture Overview

Three independent deliverables:

```
[Website] ──enroll links──► [Stripe Hosted Checkout]
                                      │
                          checkout.session.completed
                                      │
                                      ▼
                        [fsa-stripe-webhook service]
                         (Node/Express, Docker, this server)
                                      │
                              ┌───────┴───────┐
                              ▼               ▼
                         GHL Contact     GHL Tag
                         (create)     (fsa-basic OR fsa-premium)

[Exit-intent modal] ──POST /stripe-coupon──► [Cloudflare Worker]
                                                      │
                                              Stripe Promo Code API
                                                      │
                                              { code: "FSA-XXXXXX" }
```

---

## Piece 1: Website Changes (fsa-website repo)

### Enrollment links
- Replace all `enrollment.fullsteamahead.ca` links with Stripe-hosted checkout URLs (one per product)
- Stripe checkout URLs configured in Stripe dashboard; hardcoded in HTML
- No affiliate ID needs to be passed — the new affiliate platform connects directly to Stripe via its own webhook

### Exit-intent modal (`exit-intent.js`)
- Replace the `/api/coupon` fetch (currently proxied to GHL) with a call to the Cloudflare Worker URL (e.g., `https://workers.fullsteamahead.ca/stripe-coupon`)
- Response shape stays identical from the modal's perspective: `{ code: "FSA-XXXXXX" }`
- All existing modal logic (countdown timer, localStorage suppression, discount display) unchanged

### nginx cleanup
- Remove the `/api/coupon` proxy block from `nginx.conf.template`
- Remove `GHL_BEARER` env var reference (no longer needed for coupon proxy)

### GHL affiliate SDK
- Remove `link.msgsndr.com/js/am.js` script tag from all pages (affiliate tracking moved to new platform)

### Enrollment confirmation page
- Update Stripe checkout's success URL in Stripe dashboard to point to `/enrollment-confirmation.html?ref=enrolled` — no code change needed on the page itself

---

## Piece 2: Cloudflare Worker — `stripe-coupon`

### Purpose
Stateless edge function that generates a Stripe promo code on demand for the exit-intent modal.

### Behavior
- Accepts `POST` from exit-intent modal (CORS restricted to `fullsteamahead.ca`)
- Creates a Stripe promo code: single-use, 20% off (matching current GHL discount), 15-minute expiry
- Returns `{ code: "FSA-XXXXXX" }` to the browser

### Setup
- Deployed via Wrangler CLI (`npm install -g wrangler`, `wrangler deploy`)
- Stripe secret key stored as a Cloudflare Worker secret (`wrangler secret put STRIPE_SECRET_KEY`)
- Free tier: 100k requests/day — sufficient for this use case
- Does NOT conflict with the Cloudflare tunnel — Workers route on specific URL paths; the tunnel handles origin traffic on separate routes

### Worker code (outline)
```js
// POST /stripe-coupon
// 1. Verify Origin header is fullsteamahead.ca
// 2. Call Stripe API: create coupon (percent_off: 20, duration: once)
// 3. Call Stripe API: create promo code on that coupon (max_redemptions: 1, expires_at: now + 15min)
// 4. Return { code: promoCode.code }
```

---

## Piece 3: Stripe Webhook Middleware (`fsa-stripe-webhook`)

### Purpose
Receives Stripe `checkout.session.completed` webhooks and creates/tags contacts in GHL to trigger course access and welcome email workflows.

### New repo
`fsa-stripe-webhook` — standalone Node/Express service on this server

### Stack
- Node.js + Express
- Docker container, joins existing `cloudflare` Docker network
- Public hostname via Cloudflare tunnel: `stripe-webhook.fullsteamahead.ca`

### Endpoint: `POST /webhook`
1. Verify Stripe signature (`stripe.webhooks.constructEvent`)
2. Handle `checkout.session.completed` event only
3. Read `line_items` to determine which product was purchased
4. Map product → GHL tag:
   - Product A ID → tag `fsa-basic`
   - Product B ID → tag `fsa-premium`
5. Call GHL API: `POST /contacts/` with customer name + email from Stripe session
6. Call GHL API: `POST /contacts/{id}/tags` with the appropriate tag
7. Respond `200` to Stripe within 30 seconds

### Affiliate tracking
- Not handled here — new affiliate platform connects directly to Stripe via its own webhook; no `am_id` or affiliate data is passed to GHL

### Secrets (`.env` on server, shared with existing FSA `.env` or separate)
```
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRODUCT_A_ID=prod_...
STRIPE_PRODUCT_B_ID=prod_...
GHL_API_KEY=...
GHL_LOCATION_ID=SrttR5wZPQD7bIeOAplf
```

### Cloudflare tunnel config
Add a new public hostname entry pointing `stripe-webhook.fullsteamahead.ca` → `http://fsa-stripe-webhook:PORT` on the `cloudflare` Docker network.

---

## Out of Scope
- Stripe customer portal link (Stripe generates this; just link to it from the site — no custom code)
- Affiliate platform setup (handled separately; platform configures its own Stripe webhook)
- GHL workflow automation (user builds this in GHL dashboard, triggered by contact tags)
- Any changes to GHL course/email content

---

## Verification Plan
1. **Worker local test:** `wrangler dev` + send test POST, confirm Stripe test-mode promo code returned
2. **Exit-intent modal:** Trigger modal on local site, confirm promo code displays correctly using Worker
3. **Checkout links:** Click through to Stripe test-mode checkout, complete payment, confirm redirect to `enrollment-confirmation.html`
4. **Webhook:** Use `stripe trigger checkout.session.completed` CLI command, confirm GHL contact created with correct tag
5. **Signature rejection:** Send webhook with bad signature, confirm service returns 400 and does not call GHL
