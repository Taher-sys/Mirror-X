"""Model Context Protocol (MCP) Tool Registry, Dispatcher, and JSON-RPC Server."""

import json
from typing import Any, Callable, Coroutine

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.mcp.tools import MCP_TOOL_DEFINITIONS, MCPToolHandlers
from app.core.mcp.types import (
    JsonRpcRequest,
    JsonRpcResponse,
    MCPToolCallContent,
    MCPToolCallResponse,
    MCPToolDefinition,
)
from app.core.observability import get_tracer
from app.core.security.auth import UserPrincipal
from app.core.security.sanitizer import sanitize_secrets


class MCPToolRegistry:
    """Registry managing available MCP tools, validation, authorization, and dispatch."""

    def __init__(self) -> None:
        self._tools: dict[str, MCPToolDefinition] = {t.name: t for t in MCP_TOOL_DEFINITIONS}
        self._handlers: dict[str, Callable[[AsyncSession, dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]] = {
            "inspect_system": MCPToolHandlers.inspect_system,
            "query_reality_graph": MCPToolHandlers.query_reality_graph,
            "find_context_drift": MCPToolHandlers.find_context_drift,
            "analyze_change": MCPToolHandlers.analyze_change,
            "generate_scenario": MCPToolHandlers.generate_scenario,
            "run_scenario": MCPToolHandlers.run_scenario,
            "inspect_agent_run": MCPToolHandlers.inspect_agent_run,
            "check_policy": MCPToolHandlers.check_policy,
            "search_evidence": MCPToolHandlers.search_evidence,
            "generate_release_passport": MCPToolHandlers.generate_release_passport,
        }

    def list_tools(self) -> list[MCPToolDefinition]:
        """Return all registered MCP tools."""
        return list(self._tools.values())

    def get_tool(self, tool_name: str) -> MCPToolDefinition | None:
        """Get definition of a specific tool."""
        return self._tools.get(tool_name)

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        db: AsyncSession,
        principal: UserPrincipal | None = None,
    ) -> MCPToolCallResponse:
        """Validate, authorize, and execute an MCP tool."""
        tool_def = self._tools.get(tool_name)
        if not tool_def:
            return MCPToolCallResponse(
                content=[MCPToolCallContent(text=f"Tool '{tool_name}' not found.")],
                isError=True,
            )

        handler = self._handlers.get(tool_name)
        if not handler:
            return MCPToolCallResponse(
                content=[MCPToolCallContent(text=f"No handler registered for tool '{tool_name}'.")],
                isError=True,
            )

        # 1. Authorization check
        if principal:
            if not principal.has_permission(tool_def.required_permission):
                return MCPToolCallResponse(
                    content=[
                        MCPToolCallContent(
                            text=f"Permission denied: Principal '{principal.username}' ({principal.role.value}) "
                            f"lacks required permission '{tool_def.required_permission}'."
                        )
                    ],
                    isError=True,
                )

        # 2. Input validation against required schema fields
        required_fields = tool_def.inputSchema.get("required", [])
        missing_fields = [f for f in required_fields if f not in arguments]
        if missing_fields:
            return MCPToolCallResponse(
                content=[MCPToolCallContent(text=f"Validation error: Missing required argument(s): {missing_fields}")],
                isError=True,
            )

        # 3. Instrumented Execution
        tracer = get_tracer()
        with tracer.start_span(f"mcp.tool.{tool_name}", {"mcp.tool": tool_name}) as span:
            try:
                raw_result = await handler(db, arguments)
                sanitized_result = sanitize_secrets(raw_result)

                # Format human/LLM-readable text preview and attach structured json
                text_preview = json.dumps(sanitized_result, indent=2)
                span.set_attribute("mcp.status", "success")

                return MCPToolCallResponse(
                    content=[MCPToolCallContent(type="text", text=text_preview)],
                    isError=False,
                    structured_data=sanitized_result,
                )
            except Exception as e:
                span.record_exception(e)
                error_msg = f"Tool execution failed: {str(e)}"
                return MCPToolCallResponse(
                    content=[MCPToolCallContent(type="text", text=error_msg)],
                    isError=True,
                )

    async def handle_jsonrpc(
        self,
        request: JsonRpcRequest,
        db: AsyncSession,
        principal: UserPrincipal | None = None,
    ) -> JsonRpcResponse:
        """Handle standard MCP JSON-RPC 2.0 request."""
        method = request.method
        req_id = request.id
        params = request.params or {}

        if method == "initialize":
            return JsonRpcResponse(
                id=req_id,
                result={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {
                        "name": "MIRROR-X MCP Server",
                        "version": "1.0.0",
                    },
                },
            )

        elif method == "tools/list":
            tools_list = [
                {
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": t.inputSchema,
                }
                for t in self.list_tools()
            ]
            return JsonRpcResponse(id=req_id, result={"tools": tools_list})

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            if not tool_name:
                return JsonRpcResponse(
                    id=req_id,
                    error={"code": -32602, "message": "Invalid params: 'name' is required for tools/call."},
                )

            tool_response = await self.call_tool(tool_name, arguments, db, principal)
            return JsonRpcResponse(
                id=req_id,
                result={
                    "content": [{"type": c.type, "text": c.text} for c in tool_response.content],
                    "isError": tool_response.isError,
                    "structured_data": tool_response.structured_data,
                },
            )

        elif method in ("ping", "health"):
            return JsonRpcResponse(id=req_id, result={"status": "ok"})

        else:
            return JsonRpcResponse(
                id=req_id,
                error={"code": -32601, "message": f"Method not found: '{method}'"},
            )


# Global singleton registry instance
_GLOBAL_MCP_REGISTRY = MCPToolRegistry()


def get_mcp_registry() -> MCPToolRegistry:
    """Access global MCPToolRegistry."""
    return _GLOBAL_MCP_REGISTRY
