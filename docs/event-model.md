# Event Model

As MIRROR-X evolves, it will ingest real-time and asynchronous events to maintain the accuracy of the Reality Graph and power the Context Engine.

## 1. Core Event Streams

### A. Change Events (Source Code & Schema)
Triggered by VCS (e.g., GitHub webhooks) or CI pipelines.
- `commit.created`
- `pull_request.opened`
- `schema.migrated`

### B. Agent Telemetry Events
Triggered by AI Agents operating within the ecosystem.
- `agent.run.started`
- `agent.tool.called`
- `agent.observation.received`
- `agent.run.completed`
- `agent.error.encountered`

### C. Test & Release Events
- `test.run.completed`
- `scenario.executed`
- `release.passport.issued`
- `deployment.started`
- `deployment.completed`

### D. Policy Events
- `policy.evaluated`
- `policy.violation.detected`

## 2. Event Payload Structure
All events should adhere to a standard envelope to allow generic processing and trace linking.

```json
{
  "event_id": "uuid-v4",
  "event_type": "agent.tool.called",
  "timestamp": "2026-09-23T10:00:00Z",
  "source": "payment-agent-v2",
  "trace_id": "req-xyz-789",
  "payload": {
    "tool_name": "query_database",
    "arguments": {"table": "users", "limit": 1}
  }
}
```

## 3. Ingestion Strategy
- **Phase 1-4**: Events are registered synchronously via REST API (`POST /api/v1/events`).
- **Phase 5+**: Introduction of async background tasks (e.g., Celery/Redis) for processing git diffs and telemetry without blocking the API.
- **Long-term**: OpenTelemetry (OTel) compliance for native trace ingestion.
