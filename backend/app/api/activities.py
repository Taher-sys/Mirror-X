from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.activity import Activity
from app.schemas.activity import ActivityCreate, ActivityResponse
from app.schemas.common import PaginationMeta, StandardResponse

router = APIRouter(prefix="/activities", tags=["Activities"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=StandardResponse[list[ActivityResponse]])
async def list_activities(
    db: DatabaseSession,
    entity_type: Annotated[str | None, Query(description="Filter by entity type (repository, service, finding, system)")] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> StandardResponse[list[ActivityResponse]]:

    """List recent activity log events in reverse chronological order."""
    query = select(Activity)

    if entity_type:
        query = query.where(Activity.entity_type == entity_type)

    count_query = select(func.count(Activity.id))
    if entity_type:
        count_query = count_query.where(Activity.entity_type == entity_type)
    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    offset = (page - 1) * limit
    query = query.order_by(Activity.created_at.desc()).offset(offset).limit(limit)

    res = await db.execute(query)
    activities = res.scalars().all()

    items = [
        ActivityResponse(
            id=a.id,
            actor=a.actor,
            action=a.action,
            entity_type=a.entity_type,
            entity_name=a.entity_name,
            details=a.details,
            metadata_payload=a.metadata_payload,
            created_at=a.created_at,
        )
        for a in activities
    ]

    meta = PaginationMeta(
        total=total,
        page=page,
        limit=limit,
        pages=max(1, (total + limit - 1) // limit),
    ).model_dump()

    return StandardResponse(data=items, meta=meta)


@router.post("", response_model=StandardResponse[ActivityResponse], status_code=status.HTTP_201_CREATED)
async def create_activity(
    payload: ActivityCreate,
    db: DatabaseSession,
) -> StandardResponse[ActivityResponse]:

    """Manually record an activity event."""
    activity = Activity(
        actor=payload.actor,
        action=payload.action,
        entity_type=payload.entity_type,
        entity_name=payload.entity_name,
        details=payload.details,
        metadata_payload=payload.metadata_payload,
    )
    db.add(activity)
    await db.commit()
    await db.refresh(activity)

    return StandardResponse(
        data=ActivityResponse(
            id=activity.id,
            actor=activity.actor,
            action=activity.action,
            entity_type=activity.entity_type,
            entity_name=activity.entity_name,
            details=activity.details,
            metadata_payload=activity.metadata_payload,
            created_at=activity.created_at,
        )
    )
