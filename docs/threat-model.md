# MIRROR-X Threat Model & Security Posture

**Framework**: STRIDE Threat Analysis  
**Classification**: Engineering Specification  
**Version**: 1.0.0 (Master Release)  
**Status**: Validated & Active

---

## 1. System Scope & Trust Boundaries

MIRROR-X ingests, processes, analyzes, and correlates sensitive architectural artifacts. The system is partitioned into explicit Trust Boundaries:

```
[ UNTRUSTED EXTERNAL ZONE ]
  │  - External Git Repositories
  │  - Incoming Webhook Events
  │  - MCP / Agent Client Requests
  ▼
────────────────── Trust Boundary 1: Perimeter & Transport ──────────────────
  │  - TLS / HTTPS
  │  - Sliding Window Rate Limiter
  │  - W3C TraceContext Middleware
  ▼
[ DEMILITARIZED INGESTION SANDBOX ]
  │  - Payload Bound Validator (500 files, 2MB max, 15MB total)
  │  - Path Traversal Guard (No ../, leading slashes, null bytes)
  │  - Binary / Executable Rejector
  │  - In-Memory AST / Schema Parsers (No subprocess / shell execution)
  ▼
────────────────── Trust Boundary 2: Application Security ───────────────────
  │  - Bearer Token Auth / Principal Resolver
  │  - RBAC Scope Guard
  │  - ABAC Context Evaluator
  ▼
[ CORE CONTROL PLANE RUNTIME ]
  │  - Reality Graph Engine
  │  - Context Engine & Drift Analyzer
  │  - Change Twin Impact Calculator
  │  - Synthetic Scenario Engine
  │  - Agent Behavior Lab
  │  - MCP Tool Server (10 Gated Tools)
  │  - OpenTelemetry Tracing Pipeline
  ▼
────────────────── Trust Boundary 3: Storage & Trust Core ───────────────────
  │  - MySQL Authoritative DB (Prepared Statements, SSL)
  │  - Trust Layer Policy Engine (Mandatory Sandbox Isolation)
  │  - Evidence Ledger (SHA-256 Cryptographic Hash Chain)
  │  - Release Passport Sign-off Vault
  ▼
────────────────── Trust Boundary 4: Distributed Edge ────────────────────────
  │  - Inbound Snapshot Verification (HMAC-SHA256 Signature)
  │  - Offline SQLite Cache (Credential Stripped)
  │  - Outbound Sync Queue with Idempotency & Conflict Ledger
```

---

## 2. STRIDE Threat Analysis & Mitigation Matrix

### 2.1. Spoofing (Identity & Origin)

| Threat ID | Threat Scenario | Impact | Mitigation Strategy | Verification Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **TH-SP-01** | Unauthorized caller forges agent or engineer identity to access Reality Graph. | High | Bearer token authentication required on all protected endpoints. Identity mapped to strict `UserPrincipal`. Unauthenticated requests denied with HTTP 401. | `test_auth_roles` in `test_phase12_production_hardening.py` |
| **TH-SP-02** | Malicious client submits fake edge synchronization events to cloud engine. | High | Inbound edge sync requires valid sync tokens; snapshot bundles verified with HMAC-SHA256 signatures; event origin validated against registered edge IDs. | Edge HMAC-SHA256 signature verification tests in `test_edge_local_first.py` |
| **TH-SP-03** | Malicious MCP client invokes sensitive tools without authorization. | High | MCP registry validates principal role against tool permission requirements before tool execution; unauthorized calls return MCP error code `-32003`. | `test_mcp_unauthorized_call_rejected` |

---

### 2.2. Tampering (Data Integrity)

| Threat ID | Threat Scenario | Impact | Mitigation Strategy | Verification Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **TH-TM-01** | Attacker modifies an evidence record to fake a passing security audit. | Critical | Evidence records compute an immutable SHA-256 payload hash at creation; modifying the record invalidates the verification hash. | `test_evidence_hashing` in `test_evidence_release.py` |
| **TH-TM-02** | Ingestion payload includes path traversal (`../../etc/passwd`) or null bytes to overwrite files. | Critical | `is_safe_relative_path` and `validate_ingestion_payload` reject any path with directory navigation, backslashes, or null bytes. | `test_path_traversal_prevention` |
| **TH-TM-03** | Malicious PR diff tampers with internal graph nodes to disguise blast radius. | High | Graph persistence enforces schema integrity; AST parsers validate syntactical correctness before node creation. | `test_reality_graph.py` AST ingestion tests |

---

### 2.3. Repudiation (Auditability)

| Threat ID | Threat Scenario | Impact | Mitigation Strategy | Verification Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **TH-RP-01** | User or agent denies executing a destructive operation or generating a release passport. | High | Every release passport requires explicit human or principal sign-off with audit metadata, timestamp, and linked evidence hashes. | `test_passport_generation_flow` in `test_evidence_release.py` |
| **TH-RP-02** | Actions performed in Agent Behavior Lab or MCP server are untracked. | Medium | OpenTelemetry tracer records distributed trace spans with unique `trace_id`, parent span, user principal, and operation status. | `test_observability_middleware_headers` and `/system/telemetry` |

---

### 2.4. Information Disclosure (Confidentiality)

| Threat ID | Threat Scenario | Impact | Mitigation Strategy | Verification Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **TH-ID-01** | Stack traces or SQL connection strings leaked in API error responses. | High | Production error handlers suppress tracebacks, returning generic HTTP 500 messages; error details logged privately to correlated trace IDs. | `test_safe_error_handling` in `test_phase12_production_hardening.py` |
| **TH-ID-02** | Ingested source files containing API keys, private keys, or JWT tokens exposed in telemetry. | High | `sanitize_secrets` runs across all telemetry attributes, log messages, and error responses, stripping sensitive tokens. | `test_secret_sanitization` in `test_phase12_production_hardening.py` |
| **TH-ID-03** | Edge offline database stolen containing production database credentials. | Critical | Inbound edge snapshot generation strips all sensitive credentials, database passwords, and private tokens before transmission to edge node. | `test_edge_local_first.py` |

---

### 2.5. Denial of Service (Availability)

| Threat ID | Threat Scenario | Impact | Mitigation Strategy | Verification Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **TH-DOS-01**| Client floods the API with high-frequency requests to exhaust server threads. | High | `SlidingWindowRateLimiter` enforces 120 req/min globally and 30 req/min on computational endpoints; returns HTTP 429 + `Retry-After`. | `test_rate_limiter_sliding_window` |
| **TH-DOS-02**| Attacker submits zip-bomb or millions of small files in repository ingestion payload. | Critical | `validate_ingestion_payload` enforces rigid ceilings: max 500 files, max 2MB per file, max 15MB aggregate payload. | `test_sandbox_payload_bounds` |
| **TH-DOS-03**| Synthetic scenario generator or agent lab causes runaway memory or CPU loop. | Medium | Scenario engine capped to maximum bounded counts; execution steps bounded in agent runtime with timeout controls. | `test_scenario_engine.py` and `test_agent_lab.py` |

---

### 2.6. Elevation of Privilege (Authorization)

| Threat ID | Threat Scenario | Impact | Mitigation Strategy | Verification Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **TH-EP-01** | An AI Agent or Engineer role executes autonomous mutations directly against production. | Critical | Policy Engine (`evaluate_policy`) unconditionally rejects actions with `is_sandbox=False`; destructive operations require Admin + Human Review. | `test_trust_layer.py` and `test_phase12_production_hardening.py` |
| **TH-EP-02** | User with `engineer` role attempts to bypass RBAC to approve release passport or manage users. | High | `require_permission("sign:passport")` and `require_role(Role.ADMIN)` reject unauthorized requests with HTTP 403 Forbidden. | `test_auth_roles` in `test_phase12_production_hardening.py` |
| **TH-EP-03** | Container breakout or process takeover from untrusted ingested code. | Critical | Ingestion parser is pure AST/regex parsing without code execution (`subprocess` banned); Docker container runs as unprivileged user `mirrorx` (UID 10001) with read-only root options. | `backend/Dockerfile` user declaration & `sandbox.py` |

---

## 3. Residual Risk Assessment & Hardening Recommendations

1. **Production Deployment with Reverse Proxy**:
   - In production, MIRROR-X must be deployed behind an enterprise reverse proxy (Envoy, NGINX, Cloudflare) terminating TLS 1.3 and providing DDoS scrubbing.
2. **Distributed Rate Limiting**:
   - For multi-instance clustered deployments, the in-memory sliding-window rate limiter should be backed by a centralized Redis cluster via `REDIS_URL`.
3. **Database Connection Hardening**:
   - In production environments, MySQL connections must enforce SSL/TLS encryption (`ssl_mode=REQUIRED`).
