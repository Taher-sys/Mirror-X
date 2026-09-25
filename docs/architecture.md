# MIRROR-X Master Architecture Specification

**Version**: 1.0.0 (Master Release)  
**Status**: Authoritative & Implemented  
**Date**: 2026-09-25

---

## 1. Architectural Principles

1. **Modular Monolith**: Clean domain boundaries between Graph, Context, Scenarios, Trust, AI Core, Observability, and MCP with zero circular dependencies.
2. **Evidence-Driven Reality Twin**: Every finding, drift, blast radius calculation, and release passport is anchored by verifiable, cryptographic evidence (SHA-256).
3. **Strongly Typed & API-First**: End-to-end Pydantic validation across all HTTP REST and JSON-RPC 2.0 endpoints.
4. **Observable by Design**: Native W3C TraceContext OpenTelemetry tracing spanning all domain operations and HTTP lifecycles.
5. **Secure by Default & Human-in-the-Loop**: Dual-layer RBAC/ABAC authorization, strict in-memory ingestion sandboxing, sliding-window rate limiting, and zero autonomous production executions.
6. **Local-First & Distributed**: Embedded SQLite edge nodes synchronizing with authoritative cloud storage through idempotent, conflict-detected replication.
7. **External AI Integration via MCP**: Standardized Model Context Protocol (MCP) tool layer exposing 10 controlled, permission-checked tools to external AI agents.

---

## 2. Global Architecture Diagram

```
                                 ┌────────────────────────────────────────────────────────┐
                                 │                   AI AGENTS & CLIENTS                  │
                                 │    - Anthropic Claude / Claude Code                    │
                                 │    - IDE Extensions & Automated Assistants             │
                                 │    - Enterprise Frontend (Vengeance UI)                │
                                 └───────────────┬────────────────────────▲───────────────┘
                                                 │                        │
                                                 │ HTTP REST / JSON-RPC   │ W3C TraceContext
                                                 ▼                        │ X-Trace-ID Headers
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           MIRROR-X PRODUCTION CONTROL PLANE                                     │
│                                                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                       PERIMETER & SECURITY PIPELINE                                     │   │
│   │   - W3C Distributed Observability Middleware (Trace ID, Span ID, Duration, Status)                      │   │
│   │   - Sliding-Window Rate Limiter (120 req/min global, 30 req/min sensitive)                              │   │
│   │   - Bearer Authentication & UserPrincipal Resolver (Admin, Architect, Engineer, Auditor, Agent)         │   │
│   │   - Ingestion Sandbox (Max 500 files, 2MB/file, 15MB aggregate, Path Traversal Guard, Zero Subprocesses)│   │
│   │   - Automated Secret Scrubbing Pipeline (Regex sanitization across logs, traces, errors)                │   │
│   └────────────────────────────────────────────────────┬────────────────────────────────────────────────────┘   │
│                                                        │                                                        │
│   ┌────────────────────────────────────────────────────┴────────────────────────────────────────────────────┐   │
│   │                                            MODULAR DOMAIN ENGINES                                       │   │
│   │                                                                                                         │   │
│   │   ┌───────────────────────────┐    ┌───────────────────────────┐    ┌───────────────────────────────┐   │   │
│   │   │   Reality Graph Engine    │    │      Context Engine       │    │    Change Twin & Impact       │   │   │
│   │   │ - AST & Schema Ingestion  │───▶│ - Cross-System Linking    │───▶│ - Blast Radius Calculation    │   │   │
│   │   │ - Nodes, Edges, Relations │    │ - Contract Drift Detection│    │ - Git Diff Parsing & Findings │   │   │
│   │   └───────────────────────────┘    └───────────────────────────┘    └───────────────────────────────┘   │   │
│   │                 │                                │                                  │                   │   │
│   │                 ▼                                ▼                                  ▼                   │   │
│   │   ┌───────────────────────────┐    ┌───────────────────────────┐    ┌───────────────────────────────┐   │   │
│   │   │  Synthetic Scenario Engine│    │    Agent Behavior Lab     │    │   Trust Layer Policy Engine   │   │   │
│   │   │ - 10 Scenario Classes     │───▶│ - Run Telemetry & Spans   │───▶│ - Zero-Trust Guard (Sandbox)  │   │   │
│   │   │ - Boundary & Adversarial  │    │ - 8 Behavioral Metrics    │    │ - Human Review Enforcement    │   │   │
│   │   └───────────────────────────┘    └───────────────────────────┘    └───────────────────────────────┘   │   │
│   │                 │                                │                                  │                   │   │
│   │                 ▼                                ▼                                  ▼                   │   │
│   │   ┌───────────────────────────┐    ┌───────────────────────────┐    ┌───────────────────────────────┐   │   │
│   │   │  Evidence & Release Core  │    │    AI & Sequence Engine   │    │      MCP Protocol Server      │   │   │
│   │   │ - SHA-256 Evidence Ledger │───▶│ - Dataset Synthesis       │───▶│ - JSON-RPC 2.0 /tools/call    │   │   │
│   │   │ - 6-Domain Passports      │    │ - GRU & Baseline Models   │    │ - 10 Controlled Tools         │   │   │
│   │   └───────────────────────────┘    └───────────────────────────┘    └───────────────────────────────┘   │   │
│   └────────────────────────────────────────────────────┬────────────────────────────────────────────────────┘   │
│                                                        │                                                        │
│   ┌────────────────────────────────────────────────────┴────────────────────────────────────────────────────┐   │
│   │                                            DATA & STATE LAYER                                           │   │
│   │   - Primary Database: MySQL (SQLAlchemy Async ORM, Alembic Migrations)                                  │   │
│   │   - Distributed Edge Node: SQLite Local-First Replicas (`artifacts/edge/edge_node.db`)                  │   │
│   │   - Telemetry Ring Buffer: OpenTelemetry In-Memory Buffer + Prometheus Text Exposition                  │   │
│   └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Implemented Modular Engines (Phases 1 - 12)

1. **Command Center & Vengeance UI (Phases 1-2)**: High-performance operational dashboard for ecosystem health, repository overview, and finding triage.
2. **Reality Graph Engine (Phase 3)**: Pure Python AST and schema ingestion parsing repositories into directional graph nodes (files, classes, functions, endpoints, database tables) and typed edges.
3. **Context Engine (Phase 4)**: Correlates documentation, APIs, and schemas to pinpoint contract drift, orphaned components, and breaking modifications.
4. **Change Twin Engine (Phase 5)**: Git commit and PR diff parser projecting proposed alterations onto the Reality Graph to compute direct and transitive blast radius.
5. **Synthetic Scenario Engine (Phase 6)**: Algorithmic generator producing deterministic test scenarios across 10 classes (`normal`, `boundary`, `incomplete`, `malformed`, `contradictory`, `unauthorized`, `adversarial`, `outage`, `tool_failure`, `ambiguous`).
6. **Agent Behavior Lab (Phase 7)**: Execution lab tracking AI agent runs, tool calls, and behavioral evaluations across 8 quantitative metrics.
7. **Trust Layer & Policy Engine (Phase 8)**: Zero-trust governance evaluating action safety; enforces absolute non-sandbox isolation and flags destructive operations for human sign-off.
8. **Evidence Ledger & Release Passport (Phase 9)**: Cryptographic evidence anchoring (SHA-256) and multi-domain Release Passports governing enterprise deployment readiness.
9. **AI Core & Deep Sequence Reasoning (Phase 10)**: Dataset synthesis, Logistic baseline models, and GRU sequence architectures predicting agent trajectory deviations.
10. **Edge and Local-First Architecture (Phase 11)**: Embedded SQLite database, HMAC-SHA256 inbound snapshot synchronization, outbound sync queue, and demonstrable `ONLINE`/`OFFLINE` capability boundaries.
11. **Production Hardening, Observability, MCP & Master Release (Phase 12)**:
    - OpenTelemetry distributed tracing with Prometheus metrics exposition (`/system/telemetry`, `/system/metrics`).
    - Model Context Protocol (MCP) server providing 10 gated tools via JSON-RPC 2.0 (`/mcp/rpc`) and REST (`/mcp/tools`).
    - Ingestion sandboxing, path traversal guards, sliding-window rate limiting, and RBAC/ABAC role enforcement.
    - Multi-stage unprivileged Docker containers (`mirrorx:10001`), hardened Docker Compose, and automated GitHub Actions CI/CD workflows (`ci.yml`, `security.yml`, `release.yml`).

---

## 4. Production Deployment & Operational Readiness

- **Containerization**: Multi-stage Linux Dockerfile compiling Python dependencies in a builder stage and running as an unprivileged user (`UID 10001`) with read-only file capabilities.
- **Continuous Integration**: Multi-job GitHub Actions pipeline testing Python 3.11, 3.12, 3.13, 3.14 across linting, type checks, and complete pytest suites.
- **Security Audits**: Continuous automated scanning via Bandit, pip-audit, Gitleaks, and Trivy container vulnerability scanning.
