"""FastAPI routes for Phase 7 Agent Behavior Lab."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.agents.comparison import AgentVersionComparator
from app.core.agents.lab_engine import DEFAULT_SANDBOX_TOOLS, AgentBehaviorLabEngine
from app.core.database import get_db
from app.models.agent import Agent, AgentRun, AgentStep
from app.schemas.agent import (
    AgentCompareRequest,
    AgentCompareResponse,
    AgentCreateRequest,
    AgentResponse,
    AgentRunRequest,
    AgentRunResponse,
)
from app.schemas.common import StandardResponse

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post("", response_model=StandardResponse[AgentResponse], status_code=status.HTTP_201_CREATED)
async def create_agent(
    payload: AgentCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[AgentResponse]:
    """Register an agent version in the behavior lab."""
    agent = Agent(
        name=payload.name,
        version=payload.version,
        model_reference=payload.model_reference,
        purpose=payload.purpose,
        config_payload=payload.config_payload,
    )
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return StandardResponse(data=AgentResponse.model_validate(agent))


@router.get("", response_model=StandardResponse[list[AgentResponse]])
async def list_agents(
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[list[AgentResponse]]:
    """List registered agents and versions."""
    query = select(Agent).order_by(Agent.name, Agent.version.desc())
    result = await db.execute(query)
    agents = result.scalars().all()
    return StandardResponse(
        data=[AgentResponse.model_validate(a) for a in agents],
        meta={"total": len(agents)},
    )


@router.get("/tools", response_model=StandardResponse[list[dict[str, Any]]])
async def list_agent_tools() -> StandardResponse[list[dict[str, Any]]]:
    """List available sandbox tools for agent execution."""
    return StandardResponse(data=DEFAULT_SANDBOX_TOOLS)


@router.get("/{agent_id}", response_model=StandardResponse[AgentResponse])
async def get_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[AgentResponse]:
    """Retrieve agent details."""
    query = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(query)
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return StandardResponse(data=AgentResponse.model_validate(agent))


@router.post("/{agent_id}/run", response_model=StandardResponse[AgentRunResponse])
async def run_agent(
    agent_id: uuid.UUID,
    payload: AgentRunRequest,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[AgentRunResponse]:
    """Execute a controlled agent run in the Behavior Lab sandbox."""
    query = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(query)
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    lab = AgentBehaviorLabEngine()
    telemetry = lab.execute_run(
        agent_name=agent.name,
        agent_version=agent.version,
        model_reference=agent.model_reference,
        goal=payload.goal,
        context_reference=payload.context_reference,
        scenario_inputs=payload.scenario_inputs,
    )

    metrics = telemetry["metrics"]
    run = AgentRun(
        agent_id=agent.id,
        agent_version=agent.version,
        goal=payload.goal,
        context_reference=payload.context_reference,
        model_reference=agent.model_reference,
        trace_id=telemetry["trace_id"],
        plan=telemetry["plan"],
        status=telemetry["status"],
        result=telemetry["result"],
        errors=telemetry["errors"],
        timings=telemetry["timings"],
        successful_completion=metrics["successful_completion"],
        correct_tool_selection_count=metrics["correct_tool_selection_count"],
        incorrect_tool_use_count=metrics["incorrect_tool_use_count"],
        unnecessary_actions_count=metrics["unnecessary_actions_count"],
        policy_violations_count=metrics["policy_violations_count"],
        error_count=metrics["error_count"],
        latency_ms=metrics["latency_ms"],
        retry_count=metrics["retry_count"],
    )
    db.add(run)
    await db.flush()

    # Add steps
    for step_data in telemetry["steps"]:
        step = AgentStep(
            run_id=run.id,
            step_number=step_data["step_number"],
            thought=step_data["thought"],
            tool_call=step_data.get("tool_call"),
            arguments=step_data.get("arguments", {}),
            tool_output=step_data.get("tool_output"),
            policy_check=step_data.get("policy_check", {}),
            duration_ms=step_data.get("duration_ms", 0.0),
            status=step_data.get("status", "success"),
            error=step_data.get("error"),
        )
        db.add(step)

    await db.flush()

    # Re-fetch with steps
    q = select(AgentRun).where(AgentRun.id == run.id).options(selectinload(AgentRun.steps))
    res = await db.execute(q)
    saved_run = res.scalar_one()

    return StandardResponse(data=AgentRunResponse.model_validate(saved_run))


@router.get("/runs/list", response_model=StandardResponse[list[AgentRunResponse]])
async def list_agent_runs(
    agent_id: uuid.UUID | None = Query(None, description="Filter by agent ID"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[list[AgentRunResponse]]:
    """List execution runs from the Behavior Lab."""
    query = select(AgentRun).options(selectinload(AgentRun.steps)).order_by(AgentRun.created_at.desc()).limit(limit)
    if agent_id:
        query = query.where(AgentRun.agent_id == agent_id)

    result = await db.execute(query)
    runs = result.scalars().all()
    return StandardResponse(
        data=[AgentRunResponse.model_validate(r) for r in runs],
        meta={"total": len(runs)},
    )


@router.get("/runs/{run_id}", response_model=StandardResponse[AgentRunResponse])
async def get_agent_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[AgentRunResponse]:
    """Retrieve full trace telemetry for a specific agent run."""
    query = select(AgentRun).where(AgentRun.id == run_id).options(selectinload(AgentRun.steps))
    result = await db.execute(query)
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="AgentRun not found")
    return StandardResponse(data=AgentRunResponse.model_validate(run))


@router.post("/compare", response_model=StandardResponse[AgentCompareResponse])
async def compare_agent_runs(
    payload: AgentCompareRequest,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[AgentCompareResponse]:
    """Compare measurable behaviors across two agent runs without arbitrary scores."""
    q_base = select(AgentRun).where(AgentRun.id == payload.baseline_run_id)
    q_cand = select(AgentRun).where(AgentRun.id == payload.candidate_run_id)

    res_base = await db.execute(q_base)
    res_cand = await db.execute(q_cand)

    base_run = res_base.scalar_one_or_none()
    cand_run = res_cand.scalar_one_or_none()

    if not base_run or not cand_run:
        raise HTTPException(status_code=404, detail="One or both agent runs not found for comparison")

    comparison = AgentVersionComparator.compare_runs(
        {
            "agent_version": base_run.agent_version,
            "trace_id": base_run.trace_id,
            "metrics": {
                "successful_completion": base_run.successful_completion,
                "correct_tool_selection_count": base_run.correct_tool_selection_count,
                "incorrect_tool_use_count": base_run.incorrect_tool_use_count,
                "unnecessary_actions_count": base_run.unnecessary_actions_count,
                "policy_violations_count": base_run.policy_violations_count,
                "error_count": base_run.error_count,
                "latency_ms": base_run.latency_ms,
                "retry_count": base_run.retry_count,
            },
        },
        {
            "agent_version": cand_run.agent_version,
            "trace_id": cand_run.trace_id,
            "metrics": {
                "successful_completion": cand_run.successful_completion,
                "correct_tool_selection_count": cand_run.correct_tool_selection_count,
                "incorrect_tool_use_count": cand_run.incorrect_tool_use_count,
                "unnecessary_actions_count": cand_run.unnecessary_actions_count,
                "policy_violations_count": cand_run.policy_violations_count,
                "error_count": cand_run.error_count,
                "latency_ms": cand_run.latency_ms,
                "retry_count": cand_run.retry_count,
            },
        },
    )

    return StandardResponse(data=AgentCompareResponse(**comparison))
