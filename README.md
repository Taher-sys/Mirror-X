# MIRROR-X
**Enterprise Reality Twin for AI-Native Software Systems**

MIRROR-X is an AI engineering control plane that builds a live, machine-readable model of a software organization's technical ecosystem. 

## Vision
It understands and connects source code, APIs, databases, infrastructure, documentation, AI agents, AI tools, permissions, policies, tests, deployments, and runtime behavior into a cohesive **Reality Graph**.

MIRROR-X answers critical questions:
- What will be affected by this change?
- Which services depend on this API?
- Is documentation inconsistent with the actual implementation?
- Has an AI agent changed its behavior after a model or prompt update?
- Can this agent access something it should not?
- What synthetic scenarios should be tested?
- What evidence supports this finding?
- Is this release ready for human review?

## Core Principles
- **Evidence-Driven**: AI suggestions must be explainable and traceable to real evidence whenever possible.
- **Not a Generic Chatbot**: MIRROR-X is a structural engineering tool, not a conversational assistant.
- **Not a RAG Application**: It relies on deterministic graphs, schemas, and traces.
- **Not a CI/CD Dashboard**: It analyzes impact and behavior, rather than just pipeline status.
- **Not Code-Generation**: It validates and audits, rather than writes production code autonomously.

## Documentation
- [Product Specification](docs/product-spec.md)
- [Architecture](docs/architecture.md)
- [Domain Model](docs/domain-model.md)
- [Data Model](docs/data-model.md)
- [API Contract](docs/api-contract.md)
- [Event Model](docs/event-model.md)
- [Security Model](docs/security-model.md)
- [AI Architecture](docs/ai-architecture.md)
- [UI System](docs/ui-system.md)
- [Roadmap](docs/roadmap.md)

## Development
See [AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md) for automated agent instructions.
