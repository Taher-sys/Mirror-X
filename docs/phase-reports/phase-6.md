# Phase 6: SYNTHETIC SCENARIO ENGINE — Completion Report

**Date**: 2026-09-25  
**Status**: ✅ Complete  

---

## Executive Summary

Phase 6: **SYNTHETIC SCENARIO ENGINE** has been designed, implemented, and verified. The Scenario Engine produces reproducible, deterministic synthetic execution test scenarios directly from system sources:
- APIs and OpenAPI endpoints
- Schemas and Pydantic validation specs
- Domain models
- Policies and access constraints
- Tool definitions and parameter boundaries
- Validation rules
- Existing test suites

Crucially, in accordance with the MIRROR-X core tenets, the engine **does not depend on any external ML dataset or black-box generator**. Every scenario is produced deterministically from an integer seed using isolated pseudorandom state (`random.Random(seed)`), ensuring strict bit-for-bit reproducibility.

---

## Requirements Verification

| Requirement | Implementation Details | Status |
| :--- | :--- | :---: |
| **10 Scenario Classes** | `normal`, `boundary`, `incomplete`, `malformed`, `contradictory`, `unauthorized`, `adversarial`, `outage`, `tool_failure`, `ambiguous` | ✅ Complete |
| **System Sources** | Ingestion of APIs, schemas, domain models, policies, tool definitions, validation rules, existing tests | ✅ Complete |
| **Mandatory Schema** | `scenario_id`, `seed`, `initial_state`, `generated_inputs`, `expected_constraints`, `participating_resources`, `applicable_policies`, `metadata` | ✅ Complete |
| **Seed Reproducibility** | Exact identical scenario generation when executed with the same integer seed | ✅ Complete |
| **No External ML Dataset** | Fully algorithmic generator based on structural constraint mutation | ✅ Complete |
| **Sandboxed Execution** | Executable validation engine verifying assertion constraints against mock states | ✅ Complete |
| **Data Persistence** | `ScenarioRecord` model storing scenarios, execution results, status, timings | ✅ Complete |
| **REST API Suite** | `POST /api/v1/scenarios/generate`, `POST /api/v1/scenarios/{id}/execute`, `GET /api/v1/scenarios`, `GET /api/v1/scenarios/{id}`, `GET /api/v1/scenarios/classes` | ✅ Complete |
| **High-Density Frontend UI** | `/scenarios` built with dark charcoal `#14151a`, electric amber accents, thick glass panels, and live generation/execution | ✅ Complete |
| **Automated Tests** | 4 pytest test suites covering all 10 classes, seed determinism, execution logic, and REST routes | ✅ Complete |

---

## Architectural & Technical Implementation

### 1. Synthetic Scenario Engine (`backend/app/core/scenarios/generator.py`)

- **Class Dispatchers**:
  - `_gen_normal`: Generates compliant, valid entity payloads within standard operating thresholds.
  - `_gen_boundary`: Generates maximum/minimum field boundary values (e.g., maximum string lengths, max integer limits, precision extremes).
  - `_gen_incomplete`: Strips required fields (e.g., missing authentication tokens, omitted foreign keys, missing request bodies).
  - `_gen_malformed`: Injects schema typing violations (e.g., boolean strings in integer fields, corrupted date formats, invalid JSON).
  - `_gen_contradictory`: Generates mutually conflicting inputs (e.g., order with `status='completed'` but `items_count=0` and negative subtotal).
  - `_gen_unauthorized`: Injects unauthorized roles, expired tokens, or attempts access to forbidden tenants.
  - `_gen_adversarial`: Tests injection attacks (SQL injection, path traversal, shell delimiters, oversized payload attempts).
  - `_gen_outage`: Simulates downstream dependent infrastructure failure (database connection timeouts, payment gateway 503s).
  - `_gen_tool_failure`: Tests tool invocation exceptions (e.g., tool API quota exhaustion, unhandled schema mismatch).
  - `_gen_ambiguous`: Tests conflicting parameters where multiple interpretations exist.

- **Deterministic Generation**:
  - Utilizes local `random.Random(seed)` instances to ensure thread-safe, isolated pseudorandom sequences.
  - Guarantees that passing `seed=42` produces identical initial states, inputs, and constraint sets on every execution.

- **Sandbox Execution Engine**:
  - Evaluates generated constraints (`is_array`, `status_match`, `not_null`, `no_sql_injection`, `error_handled`) against simulated outputs.
  - Persists execution runtimes, passed/failed constraint evaluations, and execution status (`passed`, `failed`).

### 2. Scenario Storage Model (`backend/app/models/scenario.py`)

- **`ScenarioRecord`**:
  - Stores UUID primary key `id`, human-readable `name`, `scenario_class`, `seed`, `source_type`.
  - JSON columns: `initial_state`, `generated_inputs`, `expected_constraints`, `participating_resources`, `applicable_policies`, `metadata_json`, `execution_result`.
  - Timestamp tracking: `created_at`, `updated_at`.

### 3. API Router (`backend/app/api/scenarios.py`)

- `POST /api/v1/scenarios/generate`: Generates scenario record from payload `{ name, scenario_class, source_type, seed, parameters }`.
- `POST /api/v1/scenarios/{id}/execute`: Executes scenario constraints within sandbox, updating status to `passed` or `failed`.
- `GET /api/v1/scenarios`: Returns paginated list of generated scenarios with optional class filtering.
- `GET /api/v1/scenarios/{id}`: Returns detailed scenario with input payloads, constraints, and execution traces.
- `GET /api/v1/scenarios/classes`: Lists available scenario classes and their formal definitions.

### 4. Frontend Interface (`frontend/src/app/scenarios/page.tsx`)

- **Class Selector Matrix**: 10 clickable category pills highlighting specific scenario types.
- **Generation Form**: Name, source type (`api`, `schema`, `domain_model`, `policy`, `tool_definition`, `validation_rule`, `test`), and explicit integer seed input with quick "Randomize Seed" button.
- **Scenario Inspector**:
  - Participating resources & applicable policies tags.
  - Collapsible JSON panels for initial state, generated inputs, and expected constraints.
  - Live "Execute Scenario in Sandbox" trigger with immediate visual feedback and execution latency readout.

---

## Verification & Test Results

- **Backend Pytest**: `tests/test_scenario_engine.py` (4 tests) passing.
- **Deterministic Check**: Verified that runs with seed `1337` and seed `42` generate 100% byte-identical scenario records.
- **Frontend Vitest**: `src/app/scenarios/page.test.tsx` passing.
- **Design System Conformance**: Heavyweight charcoal canvas (`#14151a`), thick glassmorphism (`border-2 border-orange-500/35 border-t-2 border-white/25`), electric amber accents, zero blue elements.
