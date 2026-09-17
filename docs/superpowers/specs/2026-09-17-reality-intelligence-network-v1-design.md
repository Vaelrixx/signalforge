# Reality Intelligence Network v1 — Design

**Status:** Approved direction; implementation plan pending  
**Date:** 2026-09-17  
**Project:** SignalForge / Reality Event Infrastructure / Reality Desk  
**Repository:** `Vaelrixx/signalforge`

## 1. Mission

Build a revenue-ready system that detects meaningful changes in the external world, turns them into evidence-backed machine-readable events, and sells the resulting intelligence as a managed service before expanding into a general infrastructure product.

The category is **Reality Event Infrastructure (REI)**: infrastructure for observing state that software does not control and emitting verified events when that state changes.

The commercial system is the **Reality Intelligence Network (RIN)**. It has four layers:

1. **SignalForge** — observation, normalization, snapshots, change detection, evidence, severity.
2. **REI-1** — the open event contract shared across collectors, APIs, automations, and agents.
3. **Reality Desk** — the managed paid intelligence service sold to companies now.
4. **Agent Feed** — the future API/webhook/MCP surface for machines consuming Reality Events directly.

The first implementation optimizes for earning the first legitimate customer revenue quickly without sacrificing the architecture needed for a larger platform.

## 2. Problem

Software has mature primitives for internal change: database events, logs, queues, tracing, webhooks, version control, and application telemetry.

External change remains fragmented. Pricing pages, product pages, documentation, APIs, policies, terms, public datasets, release notes, and competitor positioning change outside a customer's systems. Existing page monitors often stop at a text/visual diff or an alert for a human to inspect.

RIN makes external change a software primitive:

`observe -> normalize -> compare -> classify -> prove -> emit -> deliver -> act`

The product must answer four questions reliably:

- **What changed?**
- **Where did it change?**
- **How confident are we?**
- **What evidence proves the transition?**

## 3. V1 Business Wedge

V1 is intentionally service-led. Customers do not configure selectors, queues, browser workers, or alert rules themselves.

### Founding Watch — INR 2,499/month

- Up to 5 monitored entities.
- Daily checks.
- Pricing, product, documentation, positioning, and policy monitoring.
- Weekly intelligence brief.
- High-severity change alerts.

### Reality Desk — INR 7,499/month

- Up to 20 monitored entities.
- More frequent checks where technically and operationally justified.
- Pricing, products, documentation, APIs, terms/policies, and positioning.
- Structured event feed.
- Priority alerts and weekly brief.

The hosted product may show these as founding prices. Pricing can change later; existing customer commitments must not be changed silently.

### Pilot flow

1. Prospect receives or discovers the free 7-day pilot.
2. Prospect identifies its company/site plus competitors/vendors/topics to monitor.
3. An operator creates a workspace and sources.
4. SignalForge collects baselines and checks for changes.
5. Reality Events and a pilot brief are delivered.
6. If the prospect wants continued monitoring, the operator generates a Razorpay payment link for the chosen plan.
7. The customer pays through Razorpay.
8. A verified payment callback marks the subscription/customer as active.

There is **no automatic charging** in V1. Razorpay payment links are generated only for a prospect who has agreed to buy a specific plan.

## 4. V1 Success Criteria

The system is successful when it can:

- Onboard a managed pilot without engineering changes.
- Monitor at least 20 public sources for an early customer reliably.
- Detect and persist meaningful changes without generating duplicate events for the same transition.
- Produce human-readable evidence and a machine-readable REI event for every reported change.
- Deliver high-severity alerts and a weekly brief.
- Convert an accepted paid plan into a Razorpay checkout link.
- Verify successful payment through Razorpay before activating paid service.
- Record enough provenance to audit why an event was emitted.

Commercial target for the first 30 days: run several qualified pilots and convert at least one to paid service. This is a target, not a revenue guarantee.

## 5. Non-Goals for V1

V1 will **not** attempt to build:

- A general-purpose internet crawler.
- A full visual-diff SaaS competing feature-for-feature with incumbent monitors.
- A customer-configurable workflow builder.
- An app marketplace.
- A public marketplace for intelligence feeds.
- Autonomous purchasing, refunds, payouts, or bank-account operations.
- Credentialed scraping or bypassing authentication, CAPTCHAs, paywalls, or access controls.
- A universal news or social-listening platform.
- A native mobile application.
- Enterprise SSO, SCIM, or complex role administration.
- A large customer dashboard before the managed service proves demand.

These omissions are deliberate. The first customer should be paying for intelligence, not for configuration UI.

## 6. Repository and Service Boundaries

### `Vaelrixx/signalforge`

Owns the open core and hosted API runtime:

- Python observation engine.
- Normalizers.
- Snapshot hashing.
- Diff engines.
- Event classification.
- Severity/confidence rules.
- REI-1 JSON schema and validator.
- Hosted API endpoints.
- Scheduler/worker entry points.
- Integration tests and fixtures.

The dependency-free core remains usable independently. Hosted-only dependencies are optional extras rather than being forced into the core package.

### `Vaelrixx/signalforge-web`

Owns the hosted web surface:

- Public category/product site.
- Sample Reality Event explorer.
- Pilot CTA/form.
- Admin-only operations UI.
- Customer status/read-only views only if they materially reduce service work.

The existing static storefront will be migrated only as needed; visual polish must not delay the monitoring engine.

## 7. System Architecture

### 7.1 Control plane

**Primary database:** Supabase Postgres.

The database is the source of truth for customers, monitored entities, sources, schedules, check runs, snapshots, Reality Events, deliveries, briefs, and billing state.

### 7.2 Hosted API

The `signalforge` repository exposes a small Python HTTP API suitable for Vercel/serverless deployment.

Initial endpoints:

- `POST /v1/internal/check-due` — signed internal trigger that processes a bounded batch of due sources.
- `POST /v1/internal/check/{source_id}` — operator-triggered check.
- `GET /v1/events` — authenticated/internal event query for the admin and future Agent Feed.
- `GET /v1/events/{event_id}` — event plus evidence.
- `POST /v1/pilots` — create a managed pilot record.
- `POST /v1/billing/payment-link` — operator-only request to generate checkout after a customer agrees to a paid plan.
- `POST /v1/webhooks/razorpay` — payment status callback with signature verification.
- `GET /health` — dependency and deployment health.

No raw database credentials or payment secrets are returned to clients.

### 7.3 Scheduler

Supabase Postgres cron/HTTP scheduling triggers the signed `check-due` endpoint at a conservative interval.

The endpoint:

1. Claims a small bounded set of due sources using an idempotent lease.
2. Runs direct HTTP collectors for cheap sources.
3. Uses the browser collector only when the source requires rendering.
4. Persists the check result and releases the lease.
5. Advances `next_check_at` according to the source policy.

Batch size and timeouts remain small enough for serverless execution. If early paid usage outgrows this, the worker can move behind a dedicated queue without changing the REI contract.

### 7.4 Browser collector

Direct HTTP is the default.

E2B is the rendered-browser fallback for JavaScript-heavy sources and extraction that cannot be reproduced with normal HTTP.

The browser collector must:

- Use a clean isolated session.
- Load only public pages.
- Enforce timeout, page-size, and navigation limits.
- Never attempt CAPTCHA, login, access-control, or paywall bypass.
- Return deterministic extracted content plus evidence metadata.

### 7.5 Evidence storage

For V1, snapshots and evidence are stored in Postgres with retention limits. Large bodies are capped; the system stores the normalized content necessary to prove the reported transition plus hashes and relevant snippets.

A future object-storage adapter may move large raw snapshots out of Postgres without changing event IDs or evidence references.

## 8. Core Data Model

### `customers`

- `id`
- `name`
- `website`
- `contact_email`
- `status`: `lead | pilot | active | paused | closed`
- `plan`: nullable / `founding_watch | reality_desk`
- timestamps

### `monitored_entities`

A logical company, product, vendor, API, policy family, or competitor.

- `id`
- `customer_id`
- `name`
- `entity_type`
- `canonical_url`
- `active`

### `sources`

Concrete observable surfaces belonging to an entity.

- `id`
- `entity_id`
- `url`
- `source_type`: `html | json | docs | api | terms | pricing | other`
- `collector`: `http | browser`
- `interval_minutes`
- `next_check_at`
- `last_success_at`
- `consecutive_failures`
- `active`
- extraction config JSON

### `check_runs`

- `id`
- `source_id`
- `started_at`
- `finished_at`
- `status`: `running | unchanged | changed | failed`
- HTTP/status metadata
- collector version
- error category/message

### `snapshots`

- `id`
- `source_id`
- `check_run_id`
- `observed_at`
- `content_hash`
- normalized content
- extracted structured fields JSON
- provenance metadata JSON

### `reality_events`

- `id`
- `customer_id`
- `entity_id`
- `source_id`
- `event_type`
- `subject`
- `before_json`
- `after_json`
- `severity`
- `confidence`
- `summary`
- `observed_at`
- `previous_snapshot_id`
- `current_snapshot_id`
- `dedupe_key` unique
- `rei_version`

### `deliveries`

- `id`
- `event_id`
- `channel`: `email | webhook`
- `destination_ref`
- `status`
- `attempt_count`
- timestamps

### `briefs`

- `id`
- `customer_id`
- period start/end
- generated markdown/html
- included event IDs
- delivery status

### `billing_links`

- `id`
- `customer_id`
- `plan`
- `amount_paise`
- Razorpay payment-link ID
- reference ID
- `status`: `created | paid | expired | cancelled`
- timestamps

Payment credentials, API keys, bank details, passwords, and other secrets are never stored in these tables.

## 9. REI-1 Event Contract

Every externally visible change is represented as a versioned event.

Minimum envelope:

```json
{
  "specversion": "rei-1",
  "id": "evt_...",
  "type": "pricing.changed",
  "subject": "Acme Pro",
  "source": {
    "url": "https://example.com/pricing",
    "kind": "pricing"
  },
  "before": {"amount": 49, "currency": "USD"},
  "after": {"amount": 59, "currency": "USD"},
  "observed_at": "2026-09-17T09:30:00Z",
  "severity": 72,
  "confidence": 0.98,
  "evidence": [
    {
      "kind": "text",
      "before": "$49 / month",
      "after": "$59 / month",
      "locator": "pricing.pro.monthly"
    }
  ],
  "provenance": {
    "collector": "http",
    "normalizer": "html-text-v1",
    "previous_hash": "...",
    "current_hash": "..."
  }
}
```

Initial event taxonomy:

- `pricing.changed`
- `feature.added`
- `feature.removed`
- `feature.changed`
- `docs.changed`
- `api.changed`
- `terms.changed`
- `policy.changed`
- `positioning.changed`
- `availability.changed`
- `content.changed`

Unknown changes remain `content.changed` rather than forcing an incorrect semantic label.

## 10. Detection Pipeline

### Stage A — fetch

Collector returns body, headers, status, canonical URL, timestamps, and collector metadata.

### Stage B — normalize

Remove obvious noise such as volatile script/style content and normalize whitespace/ordering where safe. JSON inputs use canonical key ordering.

### Stage C — snapshot

Persist normalized content and a SHA-256 hash. If the hash matches the last successful snapshot, the run ends as `unchanged`.

### Stage D — diff

Compute deterministic differences:

- JSON path changes for structured sources.
- Text/section changes for HTML/docs.
- Extracted pricing/feature fields where configured.

### Stage E — classify

Map deterministic differences to the event taxonomy. Rules take precedence over semantic enrichment.

An optional model-based enrichment layer may improve summaries or suggest classifications, but it must never fabricate the underlying before/after evidence. Low-confidence semantic guesses fall back to `content.changed`.

### Stage F — confidence and severity

Confidence measures evidence quality, not business importance.

Example contributors:

- Direct structured field transition: high confidence.
- Stable text locator before/after: medium-high.
- Broad semantic inference with no stable locator: lower.

Severity measures likely importance to the monitored customer.

Example contributors:

- Price changed: high.
- API contract removed/broken: high.
- Terms/policy clause changed: medium-high.
- Marketing copy changed: low-medium unless configured as strategically important.

### Stage G — deduplicate

`dedupe_key` is derived from source + event type + relevant before/after fingerprint. Re-running the same state transition cannot emit a second event.

### Stage H — deliver

Only events above the configured alert threshold are sent immediately. All qualified events remain available for the weekly brief.

## 11. Evidence and Trust Model

RIN must be able to defend every event it reports.

Each event stores:

- Previous and current snapshot references.
- Before/after evidence snippets or structured values.
- Source URL.
- Observation timestamps.
- Content hashes.
- Collector and normalizer versions.
- Confidence score.

The system must distinguish clearly between:

- **Observed fact:** something actually present in source data.
- **Computed change:** deterministic difference between snapshots.
- **Interpretation:** a summary or business-impact explanation.

Interpretation may never overwrite or masquerade as observed fact.

## 12. Reliability and Error Handling

### Fetch failures

- Record failure category and status.
- Increment consecutive failure count.
- Retry with backoff only for transient classes.
- Do not emit a disappearance/removal event from a single failed fetch.

### Rendering failures

- Fall back to direct HTTP only if it still represents useful source state.
- Otherwise mark the run failed and preserve the last known good snapshot.

### Large/noisy changes

- Cap body size.
- Mark low-confidence broad changes as `content.changed`.
- Require stable repeated evidence before reporting disappearance/removal when source structure looks broken.

### Scheduler idempotency

A lease/claim field prevents overlapping workers from processing the same due source concurrently.

### Delivery failures

Delivery retries must be separate from event generation; a failed email/webhook cannot cause duplicate events.

## 13. Reporting

### Immediate alert

Concise format:

- What changed.
- Before -> after.
- Why it may matter.
- Confidence/severity.
- Direct source/evidence link.

### Weekly brief

Sections:

1. Executive summary.
2. Highest-severity changes.
3. Pricing and packaging.
4. Product/features.
5. Documentation/API/policy.
6. Positioning/marketing.
7. Watch-next recommendations.

A brief cites the underlying Reality Event IDs so every statement is traceable.

## 14. Billing and Razorpay

Razorpay is the V1 checkout provider for paid managed service.

Rules:

- A payment link is generated only after the prospect accepts a named plan and price.
- Amount is always displayed to the customer before payment.
- No automatic debit, subscription charge, refund, payout, or bank-operation automation in V1.
- The system stores Razorpay object IDs and status, never payment secrets or sensitive payment instruments.
- Razorpay webhook signatures must be verified before marking a payment as paid.
- Webhook handling is idempotent.
- Successful payment activates service only after verification.

The public/admin product can generate a shareable checkout URL, but financial account configuration remains outside the normal application workflow.

## 15. Security

- Secrets live in deployment secret storage/environment variables only.
- Internal scheduler/admin endpoints require signed authentication.
- Admin UI requires strong authentication.
- Database access is scoped through server-side APIs; browser clients do not receive privileged DB credentials.
- Customer/event queries are tenant-scoped.
- Razorpay webhook signatures are verified.
- External URLs are validated to reduce SSRF risk; private/internal network ranges are blocked.
- Fetches use explicit timeouts, redirect limits, and maximum body sizes.
- Logs redact credentials, authorization headers, cookies, and payment secrets.

## 16. Ethical Collection Rules

SignalForge V1 monitors only publicly accessible sources unless a future customer-authorized integration is designed separately.

Collectors must not:

- Bypass login or access controls.
- Solve or evade CAPTCHAs.
- Circumvent paywalls.
- Attempt stealth or anti-bot evasion.
- Collect private personal data unnecessarily.

The product is intended to observe public business information and customer-selected sources at a respectful rate.

## 17. Operator Workflow

V1 is admin-first to minimize time-to-revenue.

The operator can:

- Create/edit customer.
- Start/end pilot.
- Add entity and sources.
- Trigger a source check.
- Inspect check failures.
- View snapshots and Reality Events.
- Mark false positives/suppress noisy rules.
- Generate weekly brief.
- Generate an agreed Razorpay payment link.
- View billing status.

A full self-service customer dashboard is deferred until operator workload proves it is necessary.

## 18. Observability

The admin surface exposes:

- Sources due/healthy/failing.
- Last success time.
- Consecutive failures.
- Events emitted in last 24h/7d.
- Delivery failures.
- Pilot/customer status.
- Billing-link status.

System-level logs must include a correlation ID spanning scheduler claim -> fetch -> snapshot -> event -> delivery.

## 19. Testing Strategy

### Core tests

- Normalization fixtures.
- HTML/text diff fixtures.
- JSON-path diff fixtures.
- Event taxonomy rules.
- Severity/confidence rules.
- Deterministic dedupe keys.
- REI-1 schema validation.

### Integration tests

- Local fixture HTTP server representing unchanged/changed/failing sources.
- Database transaction tests for scheduler claiming/idempotency.
- Direct HTTP collector end-to-end.
- Mocked rendered-browser adapter.
- Delivery retry behavior.
- Razorpay webhook signature verification with fixtures/test credentials where available.

### Golden event tests

Representative before/after snapshots must produce stable expected REI events. These tests protect the event contract while implementation details evolve.

## 20. Implementation Sequence

The implementation plan should decompose V1 into the following milestones while preserving one coherent architecture:

1. **REI-1 foundation** — schema, event types, validator, golden fixtures.
2. **Persistent monitoring core** — database schema, sources, checks, snapshots, dedupe.
3. **Hosted execution** — API, scheduler trigger, direct HTTP worker, E2B browser adapter.
4. **Reality Desk operations** — admin views, pilots, event/evidence inspection, briefs.
5. **Delivery** — immediate alert + weekly brief adapters.
6. **Revenue path** — plan selection, agreed Razorpay payment-link creation, webhook verification, activation state.
7. **Public positioning** — update the web surface from generic monitoring toward Reality Event Infrastructure / Reality Desk.
8. **Production hardening** — security tests, failure handling, metrics, retention, deployment verification.

## 21. Future Expansion After V1

Only after managed service validates demand:

- Public Agent Feed API keys.
- MCP server for querying/subscribing to Reality Events.
- SDKs.
- Customer-configurable monitors.
- Webhook rules and integrations.
- Rich object storage/history.
- Public/custom intelligence feeds.
- Usage-based API billing.
- Additional collectors for feeds, files, and authorized integrations.

These features must reuse REI-1 rather than creating product-specific event formats.

## 22. Architectural Principle

**Reality Desk pays for the infrastructure while REI becomes the category.**

Every managed customer should strengthen the platform by producing better event taxonomies, extraction fixtures, evidence patterns, and reliability requirements. The managed service is not throwaway consulting; it is the revenue wedge for a reusable external-change event network.
