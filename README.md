# SignalForge

**Structured web-change intelligence for pages and APIs.**

SignalForge turns a URL into a durable event stream:

```text
fetch → normalize → snapshot → compare → score → JSON event
```

Most change monitors answer **“did this page change?”** SignalForge is being built to answer **“what changed, where, and how much should I care?”** in a format developers and agents can consume directly.

## v0.1

- HTML text normalization
- JSON normalization and path-level structured diffs
- Stable SHA-256 snapshots
- 0–10 severity scoring
- Local snapshot state
- CLI-friendly JSON output
- Zero AI dependency in the core detection path

## Install

```bash
python -m pip install -e .
```

## Use

```bash
signalforge https://example.com --pretty
```

Monitor a JSON API:

```bash
signalforge https://api.example.com/status --pretty
```

The first run captures a baseline. Later runs emit structured change events.

### Example JSON change

```json
{
  "changed": true,
  "kind": "json",
  "severity": 4,
  "summary": "2 structured JSON change(s)",
  "details": [
    {"path": "$.price", "type": "changed", "before": 10, "after": 12},
    {"path": "$.plan", "type": "added", "after": "pro"}
  ]
}
```

## Why this exists

The crowded part of the market is polling and notifications. SignalForge is aimed at the layer *after* fetching: deterministic normalization, field-level evidence, machine-readable change records, severity, and eventually routing into agents, webhooks, Discord/Telegram, databases, and dashboards.

## Roadmap

- [ ] Playwright/JS-rendered pages
- [ ] Ignore rules for noisy/dynamic regions
- [ ] PostgreSQL event store
- [ ] Scheduler + retries/backoff
- [ ] Webhooks / Discord / Telegram
- [ ] Semantic summaries as an optional layer
- [ ] Hosted dashboard and team monitors

## Design principles

1. **Evidence before summary.** Raw structured evidence stays available.
2. **Deterministic core.** AI can explain a change; it should not be required to detect one.
3. **Quiet by default.** Normalize noise before creating alerts.
4. **Agent-native output.** Events should be easy to route into other systems.

## License

MIT
