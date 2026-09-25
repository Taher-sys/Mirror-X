# Product Roadmap

This roadmap defines the sequential evolution of MIRROR-X from foundational architecture to the ultimate Master Release.

## Phase 00: Blueprint (Current)
- Establish master architecture, domain models, and technical direction.
- Define agent operational constraints.

## Phase 01: Foundation (Completed)
- Set up Next.js frontend, FastAPI backend, and MySQL database.
- Implement core data models (Organization, Project).
- Established CI pipelines, testing frameworks, and baseline application shell.

## Phase 02: Command Center (Completed)
- Build the real Command Center control room with VengeanceUI design principles.
- Implement deep OLED dark theme, 3D perspective grids, and depth-layered glass panels.
- Add real data-driven telemetry endpoints (`/system/summary`, `/system/status`, `/repositories`, `/services`, `/findings`, `/activities`).
- Command & search palette (`Ctrl+K`), honest empty states, loading skeletons, error states, and responsive bento grid layout.


## Phase 03: Reality Graph (Completed)
- Implement the graph data structures (nodes and edges).
- Integrate React Flow / Three.js for interactive topology visualization.
- Enable API endpoints to serve graph data.

## Phase 04: Context Engine (Completed)
- Ingest repository metadata and API contracts.
- Link components to their explicit dependencies.
- Build the Context Explorer UI.

## Phase 05: Change Twin (Completed)
- Implement Git diff analysis.
- Build the calculation engine for Direct and Indirect Impact.
- Build the Change Twin visual dual-pane view.

## Phase 06: Scenario Lab (Completed)
- Develop deterministic synthetic scenario generation across 10 scenario classes.
- Support APIs, schemas, domain models, policies, tools, rules, and existing tests.
- Build the Scenario Engine UI with seed reproducibility and sandbox execution.

## Phase 07: Agent Lab (Completed)
- Implement controlled AI agent execution environment and trace telemetry.
- Models: Agent, AgentRun, AgentStep, AgentTool.
- Build Agent Behavior Lab UI with 8 measurable behaviors and version comparison matrix.

## Phase 08: Trust Layer (Completed)
- Implement RBAC/ABAC with Principal, Agent, Tool, Resource, Action, Permission, Policy, PolicyDecision.
- Three policy results: ALLOW, DENY, HUMAN_REVIEW_REQUIRED with sandbox-only enforcement.
- Build Policy & Permissions UI with sandbox matrix, decision simulator, and human sign-off.

## Phase 09: Evidence Ledger & Release Passport (Completed)
- Implement Evidence Ledger with SHA-256 cryptographic provenance across 8 evidence types.
- Implement Release and ReleasePassport with 6-domain evaluation, 5 statuses, and explicit uncertainty notes.
- Build Evidence Ledger UI and Release Passport UI.

## Phase 10: AI Core (Completed)
- Implement self-contained Behavioral Intelligence pipeline with 7 behavior labels and 21 numerical features.
- Baseline Softmax Logistic Regression, Centroid Anomaly Detector, and deep Sequence GRU models.
- Integrated Experiment Tracker, Model Registry, and Agent Behavior Lab evaluation.

## Phase 11: Edge (Completed)
- Build local-first SQLite execution capabilities for on-premise/edge deployment.
- Implement explicit synchronization protocol, HMAC-SHA256 signed snapshot replication, and conflict detection.
- Demonstrable ONLINE/OFFLINE mode toggle with boundary capability enforcement.

## Phase 12: Master Release
- End-to-end integration, performance optimization, and stabilization.
- Final security audits and open-source documentation polish.
