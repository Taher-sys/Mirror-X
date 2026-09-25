"""Tests for Phase 12: Production-Hardening, Security, Observability, and MCP Integration."""

import pytest
from httpx import AsyncClient

from app.core.security.auth import Role, UserPrincipal
from app.core.security.rate_limit import SlidingWindowRateLimiter
from app.core.security.sandbox import (
    IngestionSandboxViolation,
    validate_ingestion_payload,
)
from app.core.security.sanitizer import (
    is_safe_relative_path,
    sanitize_filename,
    sanitize_secrets,
)


def test_security_sanitization_and_path_traversal():
    """Verify secrets redaction and path traversal defense."""
    # 1. Secret scrubbing
    payload = {
        "user": "alice",
        "api_key": "supersecretkey12345678",
        "token": "bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "nested": {"db_password": "mypassword123", "normal": "safe_value"},
        "headers": ["Bearer abcdef1234567890"],
    }
    scrubbed = sanitize_secrets(payload)
    assert scrubbed["api_key"] == "***REDACTED***"
    assert scrubbed["token"] == "***REDACTED***"
    assert scrubbed["nested"]["db_password"] == "***REDACTED***"
    assert scrubbed["nested"]["normal"] == "safe_value"
    assert "***REDACTED***" in scrubbed["headers"][0]

    # 2. Path Traversal Protection
    assert is_safe_relative_path("src/app.py") is True
    assert is_safe_relative_path("package.json") is True
    assert is_safe_relative_path("../etc/passwd") is False
    assert is_safe_relative_path("..\\windows\\system32") is False
    assert is_safe_relative_path("/root/secrets.txt") is False
    assert is_safe_relative_path("C:\\config.ini") is False
    assert is_safe_relative_path("file\x00.py") is False

    # 3. Filename Sanitization
    assert sanitize_filename("../../../etc/shadow") == "etc/shadow"
    assert sanitize_filename("src/code.py") == "src/code.py"


def test_ingestion_sandbox_boundaries():
    """Verify repository ingestion rejects binaries, empty files, and path traversal."""
    # Binary rejected
    with pytest.raises(IngestionSandboxViolation, match="Binary or executable file types are disallowed"):
        validate_ingestion_payload({"malicious.exe": "binary content"})

    # Directory traversal rejected
    with pytest.raises(IngestionSandboxViolation, match="malicious or invalid file path"):
        validate_ingestion_payload({"../../config.json": "{}"})

    # Empty payload rejected
    with pytest.raises(IngestionSandboxViolation, match="cannot be empty"):
        validate_ingestion_payload({})

    # Valid payload passes
    validate_ingestion_payload({"package.json": '{"name": "test"}', "README.md": "# Test"})


def test_rbac_and_abac_authorization():
    """Verify role-based and attribute-based permissions."""
    admin = UserPrincipal(user_id="u1", username="admin", role=Role.ADMIN)
    architect = UserPrincipal(user_id="u2", username="arch", role=Role.ARCHITECT)
    engineer = UserPrincipal(user_id="u3", username="eng", role=Role.ENGINEER)
    agent = UserPrincipal(user_id="u4", username="bot", role=Role.AGENT)

    # Admin has all permissions
    assert admin.has_permission("policy:manage") is True
    assert admin.has_permission("graph:ingest") is True

    # Architect permissions
    assert architect.has_permission("graph:ingest") is True
    assert architect.has_permission("policy:manage") is False

    # Engineer permissions
    assert engineer.has_permission("graph:read") is True
    assert engineer.has_permission("graph:ingest") is False

    # Agent permissions
    assert agent.has_permission("context:query") is True
    assert agent.has_permission("repository:create") is False

    # ABAC rules: Agent cannot target non-sandbox
    allowed, reason = agent.check_abac_access(is_sandbox=False)
    assert allowed is False
    assert "strictly confined to sandbox" in reason

    allowed_sbx, _ = agent.check_abac_access(is_sandbox=True)
    assert allowed_sbx is True

    # Restricted classification requires elevated role
    allowed_eng, _ = engineer.check_abac_access(resource_classification="confidential")
    assert allowed_eng is False

    allowed_arch, _ = architect.check_abac_access(resource_classification="confidential")
    assert allowed_arch is True


def test_rate_limiter_logic():
    """Verify in-memory sliding window rate limiter."""
    limiter = SlidingWindowRateLimiter(limit_per_minute=3)
    client_ip = "192.168.1.100"

    allowed1, rem1, _ = limiter.is_allowed(client_ip)
    assert allowed1 is True
    assert rem1 == 2

    allowed2, rem2, _ = limiter.is_allowed(client_ip)
    assert allowed2 is True
    assert rem2 == 1

    allowed3, rem3, _ = limiter.is_allowed(client_ip)
    assert allowed3 is True
    assert rem3 == 0

    # 4th request exceeds quota
    allowed4, _, retry_after = limiter.is_allowed(client_ip)
    assert allowed4 is False
    assert retry_after > 0


@pytest.mark.asyncio
async def test_opentelemetry_observability_middleware_and_api(client: AsyncClient):
    """Verify OpenTelemetry headers, trace context, and telemetry endpoints."""
    # 1. Execute an API request with incoming W3C traceparent
    trace_id_in = "4bf92f3577b34da6a3ce929d0e0e4736"
    span_id_in = "00f067aa0ba902b7"
    traceparent = f"00-{trace_id_in}-{span_id_in}-01"

    resp = await client.get("/api/v1/health", headers={"traceparent": traceparent})
    assert resp.status_code == 200

    # Trace headers propagated back
    assert "X-Trace-ID" in resp.headers
    assert resp.headers["X-Trace-ID"] == trace_id_in
    assert "X-Span-ID" in resp.headers
    assert "traceparent" in resp.headers

    # 2. Query Telemetry Endpoint
    telemetry_resp = await client.get("/api/v1/system/telemetry")
    assert telemetry_resp.status_code == 200
    tel_data = telemetry_resp.json()["data"]
    assert "summary" in tel_data
    assert "spans" in tel_data
    assert tel_data["summary"]["total_spans"] > 0

    # 3. Query Prometheus Metrics Endpoint
    metrics_resp = await client.get("/api/v1/system/metrics")
    assert metrics_resp.status_code == 200
    assert "mirrorx_uptime_seconds" in metrics_resp.text
    assert "mirrorx_spans_total" in metrics_resp.text


@pytest.mark.asyncio
async def test_mcp_tools_and_rpc_protocol(client: AsyncClient):
    """Verify MCP tools discovery, direct invocation, and JSON-RPC 2.0 compliance."""
    # 1. List MCP tools
    tools_resp = await client.get("/api/v1/mcp/tools")
    assert tools_resp.status_code == 200
    tools = tools_resp.json()["data"]
    assert len(tools) == 10

    tool_names = {t["name"] for t in tools}
    expected_tools = {
        "inspect_system",
        "query_reality_graph",
        "find_context_drift",
        "analyze_change",
        "generate_scenario",
        "run_scenario",
        "inspect_agent_run",
        "check_policy",
        "search_evidence",
        "generate_release_passport",
    }
    assert tool_names == expected_tools

    # 2. Call tool: inspect_system
    call_resp = await client.post(
        "/api/v1/mcp/tools/inspect_system/call",
        json={"arguments": {"include_metrics": True}},
    )
    assert call_resp.status_code == 200
    tool_out = call_resp.json()["data"]
    assert tool_out["isError"] is False
    assert "structured_data" in tool_out
    assert tool_out["structured_data"]["status"] in ("healthy", "degraded")

    # 3. Call tool: check_policy
    pol_call = await client.post(
        "/api/v1/mcp/tools/check_policy/call",
        json={
            "arguments": {
                "principal_name": "agent_alpha",
                "resource_name": "db_customers",
                "action_name": "read",
                "is_sandbox": True,
            }
        },
    )
    assert pol_call.status_code == 200
    assert pol_call.json()["data"]["structured_data"]["result"] == "ALLOW"

    # 4. Call tool: generate_release_passport
    passport_call = await client.post(
        "/api/v1/mcp/tools/generate_release_passport/call",
        json={"arguments": {"release_version": "v1.2.0-rc1"}},
    )
    assert passport_call.status_code == 200
    passport_data = passport_call.json()["data"]["structured_data"]
    assert passport_data["release_version"] == "v1.2.0-rc1"
    assert "passport_hash" in passport_data

    # 5. JSON-RPC 2.0 initialize
    init_rpc = await client.post(
        "/api/v1/mcp/rpc",
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize"},
    )
    assert init_rpc.status_code == 200
    rpc_res = init_rpc.json()
    assert rpc_res["result"]["serverInfo"]["name"] == "MIRROR-X MCP Server"

    # 6. JSON-RPC 2.0 tools/list
    list_rpc = await client.post(
        "/api/v1/mcp/rpc",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    )
    assert list_rpc.status_code == 200
    assert len(list_rpc.json()["result"]["tools"]) == 10

    # 7. JSON-RPC 2.0 tools/call
    exec_rpc = await client.post(
        "/api/v1/mcp/rpc",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "check_policy",
                "arguments": {
                    "principal_name": "ci_pipeline",
                    "resource_name": "prod_database",
                    "action_name": "delete",
                    "is_sandbox": False,
                },
            },
        },
    )
    assert exec_rpc.status_code == 200
    rpc_call_res = exec_rpc.json()["result"]
    assert rpc_call_res["structured_data"]["result"] == "DENY"
