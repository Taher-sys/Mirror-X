# MIRROR-X

[![CI](https://github.com/Taher-sys/Mirror-X/actions/workflows/ci.yml/badge.svg)](https://github.com/Taher-sys/Mirror-X/actions/workflows/ci.yml)
[![Security Scan](https://github.com/Taher-sys/Mirror-X/actions/workflows/security.yml/badge.svg)](https://github.com/Taher-sys/Mirror-X/actions/workflows/security.yml)
[![Release](https://github.com/Taher-sys/Mirror-X/actions/workflows/release.yml/badge.svg)](https://github.com/Taher-sys/Mirror-X/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/)

**Enterprise Reality Twin for AI-Native Software Systems**

MIRROR-X is an enterprise AI engineering control plane that builds a live, machine-readable model of a software organization's technical ecosystem. It understands and connects source code, APIs, databases, infrastructure, documentation, AI agents, AI tools, permissions, policies, tests, deployments, and runtime behavior into a unified **Reality Graph**.

---

## 🌟 Key Capabilities

- **Reality Graph Engine**: Ingests codebases and schemas into high-fidelity typed dependency graphs via pure in-memory AST and schema parsers.
- **Context Engine & Drift Detection**: Detects architectural drift, breaking schema migrations, and documentation inconsistencies before deployments.
- **Change Twin & Blast Radius**: Projects Git diffs and pull requests onto the Reality Graph to compute transitive blast radii across downstream dependencies.
- **Synthetic Scenario Engine**: Synthesizes algorithmic test scenarios across 10 deterministic scenario classes (boundary, malformed, adversarial, outage, etc.).
- **Agent Behavior Lab**: Monitors AI agent executions and evaluates behavioral drift across 8 quantitative metrics with full distributed trace telemetry.
- **Trust Layer & Policy Engine**: Zero-trust policy evaluation enforcing absolute non-sandbox isolation and mandatory human review for destructive operations.
- **Evidence Ledger & Release Passports**: SHA-256 cryptographic provenance for audit findings and multi-domain Release Passports governing production readiness.
- **AI Core & Sequence Reasoning**: Synthesizes behavioral datasets and executes deep sequence (GRU) models to detect anomalous agent trajectories.
- **Edge Local-First Architecture**: Embedded SQLite edge runtime operating autonomously offline with HMAC-SHA256 snapshot sync and conflict-detected event flushes.
- **Model Context Protocol (MCP) Server**: Exposes 10 permission-checked, schema-validated architectural tools to external AI agents via JSON-RPC 2.0 (`/api/v1/mcp/rpc`) and REST.
- **Production-Hardened & Observable**: OpenTelemetry distributed tracing, Prometheus metrics (`/api/v1/system/metrics`), sliding-window rate limiting, and RBAC/ABAC authorization.

---

## 🚀 Quickstart

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (optional for containerized deployment)
- Node.js 18+ (for frontend dashboard)

### 1. Local Backend Setup

```bash
# Clone the repository
git clone https://github.com/Taher-sys/Mirror-X.git
cd "Mirror X/backend"

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at `http://127.0.0.1:8000`. Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.

### 2. Docker Compose Setup

Run the complete production-grade stack (FastAPI backend, MySQL 8.0, and Prometheus telemetry):

```bash
docker-compose up --build -d
```

Check service health:
```bash
curl http://localhost:8000/api/v1/health
```

---

## 🤖 Model Context Protocol (MCP) Integration

MIRROR-X natively supports the **Model Context Protocol (MCP)**, allowing external AI coding agents (such as Claude Code, Cursor, and IDE extensions) to interact directly with the Reality Twin.

### Connecting via JSON-RPC 2.0
Send JSON-RPC 2.0 requests to `http://127.0.0.1:8000/api/v1/mcp/rpc`:

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/call",
  "params": {
    "name": "analyze_change",
    "arguments": {
      "diff_text": "diff --git a/app/core/auth.py b/app/core/auth.py\n+def bypass(): pass"
    }
  }
}
```

### Available MCP Tools
| Tool Name | Description |
| :--- | :--- |
| `inspect_system` | Query system status, engine health, and active configuration. |
| `query_reality_graph` | Search nodes and relationships in the Reality Graph. |
| `find_context_drift` | Scan for architectural drift and contract mismatches. |
| `analyze_change` | Calculate blast radius of a code diff against graph dependencies. |
| `generate_scenario` | Synthesize deterministic test scenarios across 10 classes. |
| `run_scenario` | Execute a synthetic scenario against target components. |
| `inspect_agent_run` | Retrieve telemetry, tool calls, and metrics for an agent run. |
| `check_policy` | Evaluate an action against Trust Layer governance policies. |
| `search_evidence` | Search the cryptographic evidence ledger by type and source. |
| `generate_release_passport` | Audit release readiness across 6 architectural domains. |

---

## 🔒 Security & Sandboxing

MIRROR-X is engineered with zero implicit trust:
- **Repository Ingestion Sandbox**: Maximum 500 files, 2MB per file, 15MB aggregate payload. Rejects path traversal sequences (`../`, null bytes) and executable binaries.
- **Zero Subprocess Execution**: Code parsing is performed purely in memory via AST and schema parsers without executing subprocesses or shell commands.
- **Automated Secret Scrubbing**: All logs, error messages, and telemetry spans pass through regex sanitizers stripping API keys, tokens, and database passwords.
- **Dual-Layer Access Control**: Role-Based Access Control (Admin, Architect, Engineer, Auditor, Agent) combined with Attribute-Based Access Control (ABAC).
- **Strict Sandbox Isolation**: Production mutations are strictly blocked; destructive actions mandate human review.

Read the complete [Security Model](docs/security-model.md) and [Threat Model](docs/threat-model.md).

---

## 📊 Observability & Metrics

- **Distributed Tracing**: Native OpenTelemetry W3C TraceContext headers (`traceparent`, `X-Trace-ID`, `X-Span-ID`) injected across all requests.
- **Telemetry Query API**: Inspect live trace spans and error rates at `/api/v1/system/telemetry`.
- **Prometheus Metrics**: Exposes Prometheus-compatible text metrics at `/api/v1/system/metrics`.

---

## 📚 Documentation Directory

- [Architecture Specification](docs/architecture.md)
- [API Contract](docs/api-contract.md)
- [Security Model](docs/security-model.md)
- [Threat Model](docs/threat-model.md)
- [Domain Model](docs/domain-model.md)
- [Data Model](docs/data-model.md)
- [AI Architecture](docs/ai-architecture.md)
- [Phase 12 Completion Report](docs/phase-reports/phase-12.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

---

## 📄 License

MIRROR-X is licensed under the MIT License.
