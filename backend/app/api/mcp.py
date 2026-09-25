"""Model Context Protocol (MCP) API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.mcp.registry import get_mcp_registry
from app.core.mcp.types import (
    JsonRpcRequest,
    JsonRpcResponse,
    MCPToolCallRequest,
    MCPToolCallResponse,
    MCPToolDefinition,
)
from app.core.security.auth import UserPrincipal, get_current_principal
from app.schemas.common import StandardResponse

router = APIRouter(prefix="/mcp", tags=["Model Context Protocol (MCP)"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
PrincipalDep = Annotated[UserPrincipal, Depends(get_current_principal)]


@router.get("/tools", response_model=StandardResponse[list[MCPToolDefinition]])
async def list_mcp_tools(
    principal: PrincipalDep,
) -> StandardResponse[list[MCPToolDefinition]]:
    """List all available MCP tools with their parameter JSON schemas."""
    registry = get_mcp_registry()
    tools = registry.list_tools()
    return StandardResponse(data=tools)


@router.post("/tools/{tool_name}/call", response_model=StandardResponse[MCPToolCallResponse])
async def call_mcp_tool(
    tool_name: Annotated[str, Path(description="Tool identifier")],
    payload: MCPToolCallRequest,
    db: DatabaseSession,
    principal: PrincipalDep,
) -> StandardResponse[MCPToolCallResponse]:
    """Execute an MCP tool directly via REST API."""
    registry = get_mcp_registry()
    result = await registry.call_tool(
        tool_name=tool_name,
        arguments=payload.arguments,
        db=db,
        principal=principal,
    )
    if result.isError and "Permission denied" in result.content[0].text:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.content[0].text,
        )
    return StandardResponse(data=result)


@router.post("/rpc", response_model=JsonRpcResponse)
async def handle_mcp_jsonrpc(
    payload: JsonRpcRequest,
    db: DatabaseSession,
    principal: PrincipalDep,
) -> JsonRpcResponse:
    """Handle standard JSON-RPC 2.0 requests for native MCP clients."""
    registry = get_mcp_registry()
    response = await registry.handle_jsonrpc(
        request=payload,
        db=db,
        principal=principal,
    )
    return response
