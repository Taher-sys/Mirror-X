# Architecture

## 1. Architectural Principles
- **Modular**: Clear boundaries between Context, Graph, Policy, and UI.
- **Strongly Typed**: End-to-end type safety across backend and frontend.
- **API-First**: The frontend and any external tools interact exclusively via robust REST APIs.
- **Testable**: Components are designed for isolated unit testing and deterministic integration testing.
- **Observable**: Built-in telemetry for internal performance and accuracy monitoring.
- **Secure by Default**: Explicit permission gating, strict policy enforcement, and human-in-the-loop requirements.
- **Incremental**: Evolve progressively. No "big bang" rewrites.
- **Avoid Premature Microservices**: Start as a well-structured modular monolith.
- **Avoid Unnecessary Dependencies**: Keep the stack lean and standard.

## 2. Technology Stack

### Frontend
- **Framework**: Next.js (React)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui
- **Animation**: Motion
- **Data Visualization / Graphs**: Three.js, React Three Fiber, Apache ECharts, React Flow
- **State Management**: Zustand
- **Data Fetching**: TanStack Query

### Backend
- **Language**: Python
- **Web Framework**: FastAPI
- **Validation**: Pydantic
- **ORM**: SQLAlchemy
- **Migrations**: Alembic

### Database & Storage
- **Primary Database**: MySQL (Initial deployment)
- **Caching/PubSub**: Redis (only where genuinely needed for rate limiting, pub/sub, or transient state)
- **Edge DB (Future)**: SQLite for local-first edge support

### Infrastructure
- **Containerization**: Docker, Docker Compose (Initial local and CI testing)
- **CI/CD**: GitHub Actions (Later phases)
- **Deployment**: Cloud Deployment (Deferred to later phases)

### Future Technologies (Deferred)
- **MCP (Model Context Protocol)**
- **OpenTelemetry**
- **Graph Reasoning**
- **Deep Learning**
- **Synthetic Scenario Generation**
- **Local-first Edge Execution**
- **WebGPU**

## 3. Explicit Non-Goals (DO NOT IMPLEMENT YET)
- Deep Learning models
- Autonomous Agents built-in
- MCP Servers
- 3D Digital Twin visualization
- Synthetic Scenario Engine
- Complex Policy Engine
- Cloud Deployment / Kubernetes
- Vector Databases
- Advanced Distributed Systems logic
