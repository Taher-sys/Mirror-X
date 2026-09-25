# MIRROR-X Production Security Model

**Classification**: Confidential / Engineering Specification  
**Version**: 1.0.0 (Master Release)  
**Status**: Active & Enforced

---

## 1. Security Architecture Overview

MIRROR-X is an enterprise AI engineering control plane operating in high-trust enterprise environments. It analyzes source code, architecture graphs, database schemas, execution traces, policy evaluations, and AI agent behaviors.

Security is designed as a **foundational, non-bypassable architectural primitive**. The system enforces:
1. **Zero Implicit Trust**: Every API endpoint and machine interface requires explicit identity validation.
2. **Strict Ingestion Sandboxing**: Repository parsing occurs exclusively in-memory within rigid structural boundaries, preventing arbitrary code or command execution.
3. **Automated Secret Scrubbing**: All logs, error messages, telemetry traces, and output payloads pass through an automated regex sanitization pipeline that strips credentials and tokens.
4. **Dual-Layer Access Control (RBAC + ABAC)**: Granular role-based permissions combined with contextual attribute-based access controls.
5. **Sliding-Window Rate Limiting**: Per-client IP and token sliding-window request throttling with automated burst protection.
6. **Cryptographic Immutability**: All evidence records and release passports are anchored with SHA-256 integrity hashes.
7. **Absolute Production Isolation**: Production actions cannot be executed directly; all non-sandbox actions trigger immediate denial or mandatory human review.

---

## 2. Identity and Authentication

All requests to MIRROR-X must be authenticated via Bearer tokens in the `Authorization` header:

```http
Authorization: Bearer <token>
```

### Principal Model
Every authenticated request is mapped to a `UserPrincipal`:
- `subject_id`: Unique identifier (UUID or external subject string).
- `name`: Human or service account identifier.
- `role`: One of `admin`, `architect`, `engineer`, `auditor`, `agent`.
- `organization_id`: Tenant boundary identifier.
- `is_authenticated`: Boolean identity status.
- `scopes`: Specific permission scopes assigned to the principal.
- `attributes`: Key-value metadata for ABAC evaluation (e.g., department, environment, clearance).

When running in testing or edge-offline mode, unauthenticated requests are assigned a restricted `ANONYMOUS` principal with zero write or execution privileges.

---

## 3. Role-Based Access Control (RBAC) Matrix

| Permission | Admin | Architect | Engineer | Auditor | Agent |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `read:graph` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `write:graph` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `ingest:repo` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `read:drift` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `analyze:change` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `generate:scenario` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `execute:scenario` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `inspect:agent` | ✅ | ✅ | ✅ | ✅ | ❌ |
| `run:agent_lab` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `evaluate:policy` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `manage:policy` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `search:evidence` | ✅ | ✅ | ✅ | ✅ | ❌ |
| `generate:passport` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `sign:passport` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `manage:users` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `read:telemetry` | ✅ | ✅ | ✅ | ✅ | ❌ |
| `manage:system` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `mcp:call` | ✅ | ✅ | ✅ | ❌ | ❌ |

---

## 4. Attribute-Based Access Control (ABAC)

In addition to RBAC roles, critical operations pass through attribute-based policy evaluation (`check_abac_access`):
- **Resource Environment Isolation**: An engineer or agent with staging clearance cannot trigger actions or generate passports against resources tagged `env: production`.
- **Destructive Operation Blocking**: Actions flagged as destructive (`delete`, `drop_table`, `schema_alter`, `retire_service`) require both `role: admin` and human multi-party sign-off.
- **Data Classification Filtering**: Nodes or evidence containing `restricted` or `confidential` classifications are filtered unless the principal explicitly possesses the matching security attribute.

---

## 5. Ingestion Sandboxing & Input Validation

The ingestion engine parses multi-file repositories to construct the Reality Graph. To guarantee system safety against malicious payloads:

1. **Strict Payload Bounds**:
   - `MAX_FILES_PER_INGESTION`: 500 files per request.
   - `MAX_FILE_SIZE_BYTES`: 2,097,152 bytes (2 MB) per file.
   - `MAX_AGGREGATE_PAYLOAD_BYTES`: 15,728,640 bytes (15 MB) aggregate.
2. **Directory Traversal Protection**:
   - Every file path is validated via `is_safe_relative_path`.
   - Paths containing `../`, `..\\`, leading slashes (`/`, `\`), null bytes (`\0`), or drive letters (`C:`, `/etc`) are immediately rejected with `IngestionSandboxViolation`.
3. **Executable & Binary Rejection**:
   - Payloads containing compiled binaries, DLLs, ELF executables, Windows executables (`.exe`, `.dll`, `.so`, `.bin`, `.pyc`, `.wasm`), or executable script extensions (`.sh`, `.bat`, `.cmd`, `.ps1`) are blocked.
4. **Pure In-Memory Processing**:
   - Files are parsed purely in-memory using AST and regex parsers.
   - No `subprocess`, `os.system`, or shell commands are invoked during ingestion.

---

## 6. Secret Redaction & Sanitization Pipeline

All inputs, logs, error responses, and telemetry spans pass through `app.core.security.sanitizer`:

- **Automated Regex Patterns**:
  - API Keys & Passwords: Matches `api[_-]?key`, `password`, `secret`, `access[_-]?token`, `auth[_-]?token`.
  - JSON Web Tokens (JWT): `eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+`.
  - Private Keys: `-----BEGIN [A-Z ]*PRIVATE KEY-----`.
  - Database Connection Strings: `postgres://`, `mysql://`, `redis://`, `mongodb://` containing embedded credentials.
  - AWS & Cloud Keys: `AKIA[0-9A-Z]{16}`.
- **Sanitized Outputs**: Replaced deterministically with `***REDACTED***`.

---

## 7. Sliding-Window Rate Limiting

The API is protected against denial-of-service and brute-force attacks via `SlidingWindowRateLimiter`:

- **Algorithm**: In-memory sliding time window with automatic entry expiration.
- **Default Limits**:
  - Global Default: 120 requests / minute per client identifier.
  - Sensitive / Computational Endpoints (`/api/v1/graph/ingest`, `/api/v1/ai/experiments/run`): 30 requests / minute.
  - MCP JSON-RPC Endpoint (`/api/v1/mcp/rpc`): 60 requests / minute.
- **Enforcement**:
  - HTTP 429 Too Many Requests response.
  - `Retry-After` header indicating seconds until retry is permitted.
  - Custom `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers.

---

## 8. Safe Error Handling & Information Leakage Prevention

MIRROR-X implements unified global exception handlers:
- **`AppException`**: Returns standardized error envelope `{ "status": "error", "error": { "code": "...", "message": "..." } }`.
- **`RequestValidationError`**: Converts Pydantic validation failures into structured, readable validation issues with zero raw memory addresses.
- **Unhandled Exceptions**:
  - In production (`ENVIRONMENT=production`), unhandled internal exceptions return a generic HTTP 500 error: `"An internal server error occurred. Please contact system administrator."`.
  - Raw Python tracebacks and environment internals are never sent to the client.
  - Internal tracebacks are logged exclusively to server logs with trace IDs for correlated debugging.

---

## 9. Cryptographic Evidence & Trust Layer

- **SHA-256 Hashing**: Every evidence item recorded in the evidence ledger calculates an immutable payload hash over its canonical JSON representation.
- **Release Passport Signing**: Release Passports require 6 green verification domains (reality sync, drift audit, scenario suite, agent safety, policy compliance, evidence completeness). Passports are cryptographically sealed with a unique passport hash.
- **Non-Sandbox Block**: The Trust Layer (`evaluate_policy`) unconditionally rejects any action where `is_sandbox=False`, ensuring zero autonomous mutations can reach production systems.
