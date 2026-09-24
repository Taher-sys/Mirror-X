# Security Model

MIRROR-X is an enterprise system handling highly sensitive architectural data and observing AI behaviors. Security is a first-class architectural primitive.

## 1. Secure by Default
- **No Implicit Access**: All API endpoints require authentication.
- **Strict Network Boundaries**: The Reality Graph must never directly expose internal credentials, only structural metadata.
- **Data Minimization**: MIRROR-X analyzes structure (ASTs, schemas, graph links) and avoids mirroring raw PII or sensitive database contents.

## 2. Human-in-the-Loop (HITL)
In its initial releases, MIRROR-X will **not** execute autonomous production changes.
- If MIRROR-X detects a policy violation or drift, it creates a **Finding**.
- A human must review the Finding.
- "Release Passports" require cryptographically sound approval (or strict RBAC approval) before deployment.

## 3. Role-Based Access Control (RBAC)
- **Admin**: Can modify Policies, manage environments, and connect new repositories.
- **Architect/Engineer**: Can view the Reality Graph, trigger Scenario testing, and review findings.
- **Agent (Machine Role)**: Can submit telemetry and query permitted context sub-graphs via the Context Engine.

## 4. Policy Engine (Future)
Policies will be codified as strict rules (e.g., "Agents cannot write to Table X in Production").
- Policies are evaluated against the Reality Graph deterministically.
- Any tool call made by an Agent is checked against the Policy Engine before execution.
