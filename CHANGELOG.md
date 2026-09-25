# Changelog

All notable changes to the MIRROR-X project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-09-25 — Master Production Release

### Added
- **Phase 12A (Security Hardening)**:
  - Repository ingestion sandboxing (`validate_ingestion_payload`): max 500 files, 2MB per file, 15MB aggregate limit.
  - Path traversal and null byte guards (`is_safe_relative_path`, `sanitize_filename`).
  - Automated regex secret scrubbing pipeline (`sanitize_secrets`) stripping JWTs, API keys, private keys, database connection strings.
  - Dual-layer access control: Role-Based Access Control (`Role.ADMIN`, `ARCHITECT`, `ENGINEER`, `AUDITOR`, `AGENT`) and Attribute-Based Access Control (`check_abac_access`).
  - Sliding-window rate limiter middleware (`SlidingWindowRateLimiter`) with 120 req/min global ceiling and 30 req/min sensitive endpoint ceiling.
  - Safe error handling middleware returning standardized error envelopes while hiding internal tracebacks in production.
  - Comprehensive `docs/security-model.md` and `docs/threat-model.md` (STRIDE analysis).
- **Phase 12B (DevOps & CI/CD)**:
  - Multi-stage Linux `Dockerfile` with unprivileged runtime user (`mirrorx`, UID 10001) and healthcheck probe.
  - Production `docker-compose.yml` with backend and MySQL healthchecks and dependency coordination.
  - Comprehensive `.dockerignore` preventing credential or virtual environment leakage.
  - GitHub Actions CI/CD workflows: `.github/workflows/ci.yml` (multi-job matrix), `.github/workflows/security.yml` (Bandit, pip-audit, Gitleaks, Trivy), and `.github/workflows/release.yml` (checksummed release packaging).
- **Phase 12C (Observability & Telemetry)**:
  - OpenTelemetry W3C TraceContext compliant tracer (`Tracer`, `Span`, `@trace_span`).
  - `ObservabilityMiddleware` injecting `X-Trace-ID`, `X-Span-ID`, and `traceparent` headers.
  - Domain tracing across HTTP requests, ingestion, reality graph persistence, policy evaluation, scenario execution, agent runs, release passports, and edge sync.
  - New telemetry endpoints: `/api/v1/system/telemetry` (span querying, latency, error rates) and `/api/v1/system/metrics` (Prometheus text exposition).
- **Phase 12D (Model Context Protocol - MCP)**:
  - Native MCP server implementation supporting JSON-RPC 2.0 (`/api/v1/mcp/rpc`) and REST (`/api/v1/mcp/tools`).
  - 10 gated architectural tools: `inspect_system`, `query_reality_graph`, `find_context_drift`, `analyze_change`, `generate_scenario`, `run_scenario`, `inspect_agent_run`, `check_policy`, `search_evidence`, `generate_release_passport`.
  - Schema validation, role permission checks, and OpenTelemetry trace attribution for all MCP tool calls.
- **Phase 12E & 12F (Performance & Master Security Review)**:
  - In-memory AST ingestion benchmarks, sliding window memory bounding, and static security audit.
- **Phase 12H, 12I, 12J (Documentation & Master Release)**:
  - Updated `README.md`, `docs/architecture.md`, `docs/api-contract.md`.
  - Created `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `docs/phase-reports/phase-12.md`.
  - Master release verification: 62/62 tests passing cleanly (100%).

---

## [0.11.0] - 2026-09-25 — Phase 11: Edge and Local-First Operation
### Added
- Local-first edge node runtime with embedded SQLite storage (`artifacts/edge/edge_node.db`).
- Inbound cloud snapshot replication with HMAC-SHA256 signature verification.
- Outbound synchronization event queue with idempotent processing and retry mechanics.
- Explicit conflict detection ledger preventing silent data overwrites.
- Demonstrable `ONLINE` and `OFFLINE` network toggles with capability boundaries.
- 8 REST endpoints under `/api/v1/edge` for edge monitoring and conflict resolution.

---

## [0.10.0] - 2026-09-25 — Phase 10: AI Reasoning Engine
### Added
- Behavior dataset generator synthesizing balanced training datasets across agent action sequences.
- 16-dimensional tabular feature extractor and 8-dimensional sequence tensor encoder.
- Baseline multiclass Logistic Regression model with gradient descent and evaluation metrics.
- Deep sequence GRU neural network with forward-backward passes and teacher forcing.
- Model registry supporting candidate and champion promotion lifecycle.
- AI evaluation pipeline predicting trajectory anomalies and policy violation probabilities.

---

## [0.9.0] - 2026-09-25 — Phase 9: Evidence Ledger & Release Passports
### Added
- Cryptographic evidence ledger with canonical JSON SHA-256 payload hashing.
- Release Passport engine evaluating 6 architectural readiness domains.
- Cryptographic passport sign-off flow for enterprise release certification.
- REST endpoints under `/api/v1/evidence` and `/api/v1/releases`.

---

## [0.8.0] - 2026-09-25 — Phase 8: Trust Layer & Policy Engine
### Added
- Zero-trust policy engine evaluating proposed agent actions.
- Absolute sandbox boundary enforcement blocking all non-sandbox actions.
- Human-in-the-loop triggers for destructive actions and confidential data classifications.
- Structured audit evidence generation linked to policy decisions.

---

## [0.7.0] - 2026-09-25 — Phase 7: Agent Behavior Lab
### Added
- Agent execution logging and step-by-step telemetry capture.
- 8 quantitative behavioral evaluation metrics (drift, violation, hallucination risk, etc.).
- Comparative behavioral diff analysis across agent versions.

---

## [0.6.0] - 2026-09-25 — Phase 6: Synthetic Scenario Engine
### Added
- Deterministic algorithmic scenario generator across 10 distinct scenario classes.
- Scenario execution runtime evaluating agent response accuracy and safety.
- Scenario catalog and execution persistence.

---

## [0.5.0] - 2026-09-25 — Phase 5: Change Twin & Blast Radius
### Added
- Git commit and unified diff parser extracting modified files, functions, and lines.
- Transitive graph traversal algorithm computing direct and indirect blast radii.
- Automated finding generation linked to affected downstream dependencies.

---

## [0.4.0] - 2026-09-25 — Phase 4: Context Engine & Drift Detection
### Added
- Multi-source entity correlation linking OpenAPI specs, database schemas, and documentation.
- Algorithmic drift detection highlighting schema discrepancies and broken links.
- Context sub-graph extraction for focused component analysis.

---

## [0.3.0] - 2026-09-25 — Phase 3: Reality Graph Engine
### Added
- Pure Python AST parser ingesting Python, SQL, and configuration files into graph structures.
- Typed graph model (`RealityNode`, `RealityEdge`) with directional relationships.
- Ingestion API supporting repository payloads and graph persistence.

---

## [0.2.0] - 2026-09-25 — Phase 2: Vengeance UI Frontend
### Added
- Next.js operational dashboard featuring graph visualization, finding triage, and system monitoring.

---

## [0.1.0] - 2026-09-25 — Phase 1: Foundation & Command Center
### Added
- Initial modular backend with FastAPI, SQLAlchemy, Alembic, and MySQL integration.
- Repository, service, finding, and activity models and CRUD API endpoints.
