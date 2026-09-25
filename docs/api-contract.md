# MIRROR-X API Contract Specification

**Version**: 1.0.0 (Master Release)  
**Standard**: RESTful HTTP + JSON / MCP JSON-RPC 2.0  
**Status**: Authoritative & Active

---

## 1. Core API Principles

1. **Strict Content Negotiation**: All requests and responses use `application/json` (except Prometheus metrics, which expose `text/plain`).
2. **Deterministic Envelopes**: All REST responses follow consistent success and error envelopes.
3. **W3C Distributed Tracing**: Every response includes `X-Trace-ID`, `X-Span-ID`, and `traceparent` headers for correlated end-to-end observability.
4. **Rate Limit Headers**: Requests include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`. Throttled requests receive HTTP 429 with `Retry-After`.
5. **Strict Input & Error Sanitization**: All error messages strip sensitive secrets, tokens, and database credentials before transmission.

---

## 2. Response Envelope Patterns

### 2.1. Standard Success Envelope
```json
{
  "status": "success",
  "data": { ... },
  "meta": {
    "total": 100,
    "page": 1,
    "limit": 50
  }
}
```

### 2.2. Standard Error Envelope
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Field 'files' cannot contain directory traversal sequences.",
    "details": []
  }
}
```

---

## 3. API Endpoints Catalog

### 3.1. Health & System Observability (`/api/v1/system`)
- `GET /health` — Service readiness probe and uptime status.
- `GET /system/telemetry` — Retrieve active OpenTelemetry trace summaries, latency percentiles, error rates, and span logs.
  - Query parameters: `limit` (default 50), `status` (`OK`, `ERROR`), `name` (filter by span name).
- `GET /system/metrics` — Prometheus-compatible text exposition of request counts, latency histograms, error counts, and engine executions.

### 3.2. Reality Graph Engine (`/api/v1/graph`)
- `GET /nodes` — Query Reality Graph nodes (filter by `node_type`, `project_id`, `path`).
- `GET /nodes/{id}` — Retrieve detailed node metadata and adjacent edges.
- `GET /edges` — Query Reality Graph relationships (filter by `relation_type`, `source_id`, `target_id`).
- `POST /ingest` — Ingest repository payload into the Reality Graph (sandboxed, max 500 files / 15MB).
- `GET /stats` — Graph statistics including node counts, edge counts, and component breakdown.

### 3.3. Context Engine & Architecture Drift (`/api/v1/context`)
- `GET /drift` — Detect architectural drifts, orphaned nodes, broken dependencies, and schema-model mismatches.
- `GET /subgraph` — Extract contextual sub-graph for a specific entity or target service.

### 3.4. Change Twin & Blast Radius (`/api/v1/changes`)
- `POST /` — Register a Git diff / commit change for blast radius analysis.
- `GET /{id}/impact` — Calculate direct and indirect downstream blast radius across graph dependencies.
- `GET /{id}/findings` — Retrieve automated architectural and security findings associated with the change.

### 3.5. Synthetic Scenario Engine (`/api/v1/scenarios`)
- `POST /generate` — Synthesize algorithmic test scenarios across 10 deterministic scenario classes.
- `GET /` — List generated scenario definitions with pagination.
- `POST /{id}/execute` — Execute a scenario against an agent or mock service and record outcome metrics.

### 3.6. Agent Behavior Lab (`/api/v1/agents`)
- `GET /` — List registered AI agents.
- `POST /runs` — Record an agent execution run with prompt, tool calls, and trace ID.
- `GET /runs/{id}` — Retrieve complete telemetry and behavioral metrics for a specific agent execution.
- `POST /evaluate` — Evaluate agent behavior across 8 empirical metrics (drift, violation, hallucination risk, etc.).

### 3.7. Trust Layer & Policies (`/api/v1/trust`)
- `GET /policies` — List active zero-trust governance policies.
- `POST /policies` — Register a new governance policy (Admin only).
- `POST /evaluate` — Evaluate a candidate tool call or action against policy rules (`ALLOW`, `DENY`, `HUMAN_REVIEW_REQUIRED`).

### 3.8. Evidence Ledger & Release Passports (`/api/v1/evidence`, `/api/v1/releases`)
- `POST /evidence` — Record an immutable audit evidence item with SHA-256 payload hash.
- `GET /evidence` — Search evidence records by type, source, and finding reference.
- `POST /releases/passport` — Generate a Release Passport verifying 6 architectural health domains.
- `POST /releases/passport/{id}/sign` — Cryptographically sign a release passport (Admin role only).

### 3.9. AI Core & Reasoning Models (`/api/v1/ai`)
- `POST /datasets/generate` — Generate synthesized agent behavioral datasets.
- `POST /experiments/run` — Train or evaluate baseline logistic or GRU sequence models.
- `GET /models` — List registered AI models and active champion.
- `POST /models/{id}/predict` — Execute inference prediction for agent behavioral classification.

### 3.10. Edge Local-First Node (`/api/v1/edge`)
- `GET /status` — Edge node status, active network mode (`ONLINE` / `OFFLINE`), and local SQLite stats.
- `POST /network/mode` — Switch edge network mode.
- `POST /sync/inbound` — Pull and verify authoritative cloud snapshot via HMAC-SHA256 signature.
- `POST /sync/outbound/flush` — Flush queued offline events to the cloud engine with conflict detection.
- `GET /sync/queue` — Inspect pending outbound offline events.
- `GET /conflicts` — List detected data synchronization conflicts.
- `POST /conflicts/{id}/resolve` — Resolve a detected edge conflict.

---

## 4. MCP (Model Context Protocol) Integration

MIRROR-X provides an MCP-compliant server accessible via HTTP POST at `/api/v1/mcp/rpc` (JSON-RPC 2.0) and REST endpoints under `/api/v1/mcp/tools`.

### 4.1. Supported MCP Methods
- `initialize` — Handshake declaring server capabilities (`protocolVersion: 2024-11-05`, tools support).
- `tools/list` — Return catalog of 10 available architectural tools and their JSON schemas.
- `tools/call` — Execute a tool with validated arguments and permission checks.

### 4.2. Tool Catalog
1. `inspect_system` — Retrieve system architecture health, engine states, and database readiness.
2. `query_reality_graph` — Query nodes and edges from the Reality Graph.
3. `find_context_drift` — Scan for architectural drifts and contract inconsistencies.
4. `analyze_change` — Compute the blast radius of a code diff against graph dependencies.
5. `generate_scenario` — Synthesize algorithmic test scenarios.
6. `run_scenario` — Execute a scenario against target components.
7. `inspect_agent_run` — Retrieve telemetry, tool calls, and metrics for an agent run.
8. `check_policy` — Evaluate a proposed action against the Trust Layer.
9. `search_evidence` — Search the cryptographic evidence ledger.
10. `generate_release_passport` — Audit and generate an enterprise Release Passport.
