# AI Architecture

MIRROR-X takes a deterministic, evidence-driven approach to AI. It does not use opaque deep learning models for its core decision logic. Instead, it uses Graph Reasoning and explicit evaluation.

## 1. Change Impact Analysis
When a Git diff or schema change is introduced, MIRROR-X computes the impact mathematically by traversing the Reality Graph:
- **Direct Impact**: Which files, components, or APIs are modified directly?
- **Indirect Impact**: Which downstream services, agents, or policies rely on the modified nodes?
- **Context Drift**: If an API contract changes, does an Agent's prompt or memory now contain stale assumptions?

## 2. Agent Evaluation
Agents are evaluated by their measurable behavior, not by an arbitrary "intelligence score".
MIRROR-X records every run:
- **Goals & Context**: What was the agent asked to do, and what state was provided?
- **Model Version**: The exact LLM or model used.
- **Tool Calls & Arguments**: What functions did the agent invoke?
- **Observations**: What data was returned to the agent?
- **Outputs & Errors**: What was the final result?
- **Timing & Trace ID**: For OpenTelemetry correlation.

By comparing runs across model versions against synthetic scenarios, MIRROR-X determines regressions empirically.

## 3. Synthetic Testing
MIRROR-X generates synthetic scenarios strictly from:
- APIs contracts (OpenAPI specs)
- Domain entities (Database schemas)
- Policies & Business Rules
- Registered Tools

*It must not require a conventional ML dataset or opaque embeddings for its core workflow.*

## 4. Future Additions (Deferred)
- **Model Context Protocol (MCP)**: To standardize tool registration and execution context.
- **Deep Learning / Graph Neural Networks**: For advanced anomaly detection over the graph structure (only added *after* deterministic graph traversal is mature).
