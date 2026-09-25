"""Model Context Protocol (MCP) data structures and protocol definitions."""

from typing import Any

from pydantic import BaseModel, Field


class MCPToolInputSchema(BaseModel):
    """JSON Schema defining the accepted arguments for an MCP tool."""

    type: str = "object"
    properties: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)


class MCPToolDefinition(BaseModel):
    """Specification of an MCP tool exposed to external AI agents."""

    name: str
    description: str
    inputSchema: dict[str, Any]
    required_permission: str = "mcp:call"


class MCPToolCallRequest(BaseModel):
    """Direct REST request to invoke an MCP tool."""

    arguments: dict[str, Any] = Field(default_factory=dict)


class MCPToolCallContent(BaseModel):
    """MCP Content item returned in a tool call response."""

    type: str = "text"
    text: str


class MCPToolCallResponse(BaseModel):
    """Standardized response from an MCP tool invocation."""

    content: list[MCPToolCallContent]
    isError: bool = False
    structured_data: dict[str, Any] | None = None


# JSON-RPC 2.0 Protocol Types for Standard MCP Client Compatibility
class JsonRpcRequest(BaseModel):
    """Standard JSON-RPC 2.0 Request."""

    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str
    params: dict[str, Any] | None = None


class JsonRpcResponse(BaseModel):
    """Standard JSON-RPC 2.0 Response."""

    jsonrpc: str = "2.0"
    id: str | int | None = None
    result: Any | None = None
    error: dict[str, Any] | None = None
