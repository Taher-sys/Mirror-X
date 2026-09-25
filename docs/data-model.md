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

### `scenarios` (Phase 6)
- `id` (PK, UUID)
- `name` (String)
- `scenario_class` (Enum: normal, boundary, incomplete, malformed, contradictory, unauthorized, adversarial, outage, tool_failure, ambiguous)
- `seed` (BigInteger)
- `initial_state` (JSON)
- `generated_inputs` (JSON)
- `expected_constraints` (JSON)
- `participating_resources` (JSON)
- `applicable_policies` (JSON)
- `metadata_json` (JSON)
- `execution_result` (JSON)

### `agent_runs` & `agent_steps` (Phase 7)
- `agent_runs`: `id` (PK), `trace_id` (String), `agent_id` (FK), `goal` (Text), `plan` (JSON), behavioral counters (`successful_completion`, `correct_tool_selections`, `incorrect_tool_uses`, `unnecessary_actions`, `policy_violations`, `error_count`, `latency_ms`, `retry_count`)
- `agent_steps`: `id` (PK), `run_id` (FK), `step_number` (Int), `thought` (Text), `tool_name` (String), `tool_arguments` (JSON), `tool_output` (JSON), `policy_check_passed` (Bool), `is_error` (Bool)
- `agent_tools`: `id` (PK), `agent_id` (FK), `name` (String), `parameters_schema` (JSON), `is_sandbox_safe` (Bool)

### `trust_layer` (Phase 8)
- `trust_principals`: `id` (PK), `name` (String), `role` (String), `is_service_account` (Bool)
- `trust_resources`: `id` (PK), `name` (String), `resource_type` (String), `is_sandbox` (Bool), `sensitivity_level` (String)
- `trust_actions`: `id` (PK), `name` (String), `is_destructive` (Bool)
- `trust_permissions`: `id` (PK), `principal_id` (FK), `agent_id` (FK), `resource_id` (FK), `action_id` (FK)
- `trust_policies`: `id` (PK), `name` (String), `condition_json` (JSON), `effect` (ALLOW, DENY, HUMAN_REVIEW_REQUIRED)
- `policy_decisions`: `id` (PK), `result` (ALLOW, DENY, HUMAN_REVIEW_REQUIRED), `reason` (Text), `is_sandbox` (Bool), `review_status` (String)

### `evidence_records` (Phase 9)
- `id` (PK, UUID)
- `evidence_type` (Enum: source_file, graph_relationship, api_contract, test_execution, scenario_run, agent_execution, policy_decision, runtime_trace)
- `source_reference` (String)
- `summary` (Text)
- `raw_payload` (JSON)
- `hash_signature` (String, SHA-256)
- `confidence` (Float)
- `linked_finding_id` (FK, Optional)

### `releases` & `release_passports` (Phase 9)
- `releases`: `id` (PK), `name` (String), `version` (String), `target_environment` (String), `commit_hash` (String), `status` (String)
- `release_passports`: `id` (PK), `release_id` (FK, 1-to-1), `overall_status` (PASS, FAIL, WARNING, HUMAN_REVIEW_REQUIRED, NOT_EVALUATED), `code_change_analysis` (JSON), `context_findings` (JSON), `scenario_testing` (JSON), `agent_testing` (JSON), `policy_validation` (JSON), `evidence_completeness` (JSON), `uncertainty_notes` (Text), `passport_hash` (String, SHA-256)

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
