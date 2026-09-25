"""FastAPI routes for Phase 6 Synthetic Scenario Engine."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.scenarios.generator import VALID_SCENARIO_CLASSES, SyntheticScenarioEngine
from app.models.scenario import ScenarioRecord
from app.schemas.common import StandardResponse
from app.schemas.scenario import (
    ScenarioCreateRequest,
    ScenarioExecutionResult,
    ScenarioResponse,
)

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.post("/generate", response_model=StandardResponse[ScenarioResponse], status_code=status.HTTP_201_CREATED)
async def generate_scenario(
    payload: ScenarioCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ScenarioResponse]:
    """Generate a reproducible test scenario from API, schema, or policy specifications."""
    engine = SyntheticScenarioEngine(seed=payload.seed)
    data = engine.generate(
        target_name=payload.target_name,
        source_type=payload.source_type,
        scenario_class=payload.scenario_class,
        seed=payload.seed,
        parameters=payload.parameters,
    )

    record = ScenarioRecord(
        name=data["name"],
        scenario_class=data["scenario_class"],
        source_type=data["source_type"],
        seed=data["seed"],
        initial_state=data["initial_state"],
        generated_inputs=data["generated_inputs"],
        expected_constraints=data["expected_constraints"],
        participating_resources=data["participating_resources"],
        applicable_policies=data["applicable_policies"],
        metadata_payload=data["metadata"],
        status="generated",
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)

    return StandardResponse(data=ScenarioResponse.model_validate(record))


@router.get("", response_model=StandardResponse[list[ScenarioResponse]])
async def list_scenarios(
    scenario_class: str | None = Query(None, description="Filter by scenario class"),
    source_type: str | None = Query(None, description="Filter by source type"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[list[ScenarioResponse]]:
    """List stored synthetic test scenarios."""
    query = select(ScenarioRecord).order_by(ScenarioRecord.created_at.desc()).limit(limit)
    if scenario_class:
        query = query.where(ScenarioRecord.scenario_class == scenario_class)
    if source_type:
        query = query.where(ScenarioRecord.source_type == source_type)

    result = await db.execute(query)
    scenarios = result.scalars().all()

    return StandardResponse(
        data=[ScenarioResponse.model_validate(s) for s in scenarios],
        meta={"total": len(scenarios)},
    )


@router.get("/{scenario_id}", response_model=StandardResponse[ScenarioResponse])
async def get_scenario(
    scenario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ScenarioResponse]:
    """Retrieve details of a specific scenario."""
    query = select(ScenarioRecord).where(ScenarioRecord.id == scenario_id)
    result = await db.execute(query)
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    return StandardResponse(data=ScenarioResponse.model_validate(scenario))


@router.post("/{scenario_id}/execute", response_model=StandardResponse[ScenarioExecutionResult])
async def execute_scenario(
    scenario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ScenarioExecutionResult]:
    """Execute scenario in sandbox verification harness and assert constraints."""
    query = select(ScenarioRecord).where(ScenarioRecord.id == scenario_id)
    result = await db.execute(query)
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    engine = SyntheticScenarioEngine(seed=scenario.seed)
    exec_res = engine.execute_scenario(
        {
            "scenario_id": str(scenario.id),
            "scenario_class": scenario.scenario_class,
            "expected_constraints": scenario.expected_constraints,
        }
    )

    scenario.status = "passed" if exec_res["passed"] else "failed"
    scenario.execution_result = exec_res
    await db.flush()

    return StandardResponse(data=ScenarioExecutionResult(**exec_res))


@router.post("/batch", response_model=StandardResponse[list[ScenarioResponse]])
async def generate_batch_scenarios(
    target_name: str = Query("CheckoutService", description="Target service or entity"),
    source_type: str = Query("api", description="Source type"),
    seed: int = Query(42, description="Base seed"),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[list[ScenarioResponse]]:
    """Generate a full suite covering all 10 scenario classes."""
    engine = SyntheticScenarioEngine(seed=seed)
    created: list[ScenarioRecord] = []

    for idx, s_class in enumerate(VALID_SCENARIO_CLASSES):
        curr_seed = seed + idx * 7
        data = engine.generate(
            target_name=target_name,
            source_type=source_type,
            scenario_class=s_class,
            seed=curr_seed,
        )
        record = ScenarioRecord(
            name=data["name"],
            scenario_class=data["scenario_class"],
            source_type=data["source_type"],
            seed=curr_seed,
            initial_state=data["initial_state"],
            generated_inputs=data["generated_inputs"],
            expected_constraints=data["expected_constraints"],
            participating_resources=data["participating_resources"],
            applicable_policies=data["applicable_policies"],
            metadata_payload=data["metadata"],
            status="generated",
        )
        db.add(record)
        created.append(record)

    await db.flush()
    for r in created:
        await db.refresh(r)

    return StandardResponse(
        data=[ScenarioResponse.model_validate(r) for r in created],
        meta={"total": len(created)},
    )
