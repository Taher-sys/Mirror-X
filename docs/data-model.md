# Data Model

This document outlines the initial relational database design targeting MySQL. It is designed to be queried efficiently by SQLAlchemy, serving as the foundation for the Reality Graph.

## 1. Schema Strategy
- **Primary Keys**: UUID (v4) for distributed generation and security, or strongly-typed auto-incrementing integers where performance dictates.
- **Timestamps**: Every table includes `created_at` and `updated_at` (UTC).
- **Soft Deletes**: Active/Inactive flags or `deleted_at` timestamps for non-destructive history.
- **JSON Fields**: Used sparingly for unstructured payloads (e.g., `MemoryEntry.content`, `Trace.payload`), but core relationships must remain strictly relational.

## 2. Core Tables (Initial Draft)

### `organizations`
- `id` (PK)
- `name` (String)

### `projects`
- `id` (PK)
- `organization_id` (FK)
- `name` (String)

### `repositories`
- `id` (PK)
- `project_id` (FK)
- `url` (String)
- `default_branch` (String)

### `services`
- `id` (PK)
- `repository_id` (FK)
- `name` (String)

### `apis`
- `id` (PK)
- `service_id` (FK)
- `endpoint` (String)
- `method` (String)
- `schema_hash` (String)

### `agents`
- `id` (PK)
- `name` (String)
- `model_version` (String)
- `purpose` (String)

### `policies`
- `id` (PK)
- `name` (String)
- `rule_definition` (JSON/Text)

### `changes` (Commits / PRs)
- `id` (PK)
- `repository_id` (FK)
- `git_hash` (String)
- `author` (String)

### `findings`
- `id` (PK)
- `change_id` (FK, Optional)
- `severity` (Enum)
- `description` (Text)
- `evidence_payload` (JSON)

## 3. Graph Relationships (Join Tables)
To represent the Reality Graph relationally before migrating to a dedicated graph database, we use specific mapping tables.

### `graph_edges` (Generic approach for flexible querying)
- `id` (PK)
- `source_node_type` (Enum: 'Service', 'API', 'Agent', etc.)
- `source_node_id` (UUID/Int)
- `target_node_type` (Enum)
- `target_node_id` (UUID/Int)
- `relationship_type` (Enum: 'depends_on', 'calls', 'reads_from', 'writes_to', 'uses', 'governed_by')
- `properties` (JSON)

## 4. Migrations
All schema changes are strictly versioned using **Alembic**. Manual database modifications are prohibited.
