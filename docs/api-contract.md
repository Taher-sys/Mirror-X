# API Contract

MIRROR-X follows an API-First methodology. The backend (FastAPI) exposes RESTful endpoints governed by strict Pydantic models, which are consumed by the frontend (Next.js) and future external CLI/agent tools.

## 1. Principles
- **JSON Only**: All requests and responses use `application/json`.
- **Standardized Responses**: Every response adheres to a common envelope.
- **Versioning**: API paths must include versions (e.g., `/api/v1/...`).
- **Pagination**: Any list endpoint must support `limit` and `offset` (or cursor-based pagination).

## 2. Response Envelope Pattern
**Success**
```json
{
  "status": "success",
  "data": { ... },
  "meta": { "total": 100, "page": 1 }
}
```

**Error**
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Invalid field 'endpoint'",
    "details": [...]
  }
}
```

## 3. Core Resource Endpoints

### `/api/v1/graph`
- `GET /nodes` - Query Reality Graph nodes (filter by type, project).
- `GET /edges` - Query Reality Graph relationships.
- `GET /impact?change_id={id}` - Retrieve the calculated direct and indirect impact of a specific change.

### `/api/v1/services`
- `GET /` - List services.
- `GET /{id}` - Get service details.
- `GET /{id}/apis` - Get exposed APIs for a service.

### `/api/v1/agents`
- `GET /` - List AI agents.
- `GET /{id}/runs` - Get historical executions of an agent.
- `POST /{id}/evaluate` - Trigger an evaluation against a known scenario.

### `/api/v1/changes`
- `POST /` - Register a new Git change (commit/PR) for analysis.
- `GET /{id}/findings` - Retrieve automated findings associated with this change.

## 4. Pydantic Models (Example)
```python
class AgentResponse(BaseModel):
    id: UUID
    name: str
    model_version: str
    purpose: str
    created_at: datetime
    
    class Config:
        orm_mode = True
```
