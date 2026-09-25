# Security Policy

The MIRROR-X project takes the security of its Reality Twin control plane and enterprise integrations with the utmost seriousness.

---

## 1. Supported Versions

Only the latest active major/minor release receives security updates and patches:

| Version | Supported | Notes |
| :--- | :---: | :--- |
| **1.0.x (Master Release)** | ✅ Yes | Current production release |
| < 1.0.0 | ❌ No | Pre-release development snapshots |

---

## 2. Reporting a Vulnerability

If you discover a security vulnerability in MIRROR-X:

1. **Do not create a public GitHub issue.** Public issues disclose vulnerabilities before patches can be deployed.
2. Send an email to the security response team at `security@mirrorx.dev` (or the primary repository maintainer).
3. Include the following details in your advisory:
   - Type of vulnerability (e.g., path traversal, auth bypass, injection, DoS).
   - Step-by-step instructions or proof-of-concept script to reproduce.
   - Affected components (endpoints, engines, configuration files).
   - Potential impact if exploited in a production environment.
4. We acknowledge receipt of vulnerability reports within **24 hours** and provide a status update within **72 hours**.

---

## 3. Security Architecture & Threat Boundaries

MIRROR-X enforces multi-layered defense-in-depth:
- **Authentication & RBAC**: Every request is authenticated and mapped to a role (`admin`, `architect`, `engineer`, `auditor`, `agent`).
- **Ingestion Sandboxing**: Strict 500-file, 2MB/file, 15MB aggregate bounds with path traversal prevention and rejection of binary executables.
- **Pure In-Memory Parsing**: Zero shell or subprocess execution during repository ingestion.
- **Secret Scrubbing**: Automatic regex redaction of API keys, JWTs, private keys, and connection credentials across logs, errors, and traces.
- **Sliding-Window Rate Limiting**: 120 req/min global limit and 30 req/min sensitive endpoint limit to mitigate denial-of-service.
- **Cryptographic Evidence Ledger**: SHA-256 payload hashing ensures immutability of audit records.

For detailed analysis, refer to:
- [Security Model](docs/security-model.md)
- [Threat Model](docs/threat-model.md)

---

## 4. Production Deployment Hardening Guidelines

When deploying MIRROR-X in production:
1. Always run behind a TLS-terminating reverse proxy (Envoy, NGINX, Cloudflare).
2. Set `ENVIRONMENT=production` to ensure internal exception traces are suppressed from client responses.
3. Configure strong, unique credentials for MySQL and ensure `ssl_mode=REQUIRED`.
4. Deploy using the provided multi-stage Dockerfile which runs as an unprivileged user (`UID 10001`).
5. Ensure rate limiting is enabled (`RATE_LIMIT_ENABLED=true`).
