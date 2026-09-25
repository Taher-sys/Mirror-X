import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.errors import AppException
from app.models.activity import Activity
from app.models.repository import Repository
from app.models.service import Service
from app.schemas.common import PaginationMeta, StandardResponse
from app.schemas.service import ServiceCreate, ServiceResponse

router = APIRouter(prefix="/services", tags=["Services"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=StandardResponse[list[ServiceResponse]])
async def list_services(
    db: DatabaseSession,
    repository_id: Annotated[uuid.UUID | None, Query(description="Filter by repository ID")] = None,
    status_filter: Annotated[str | None, Query(alias="status", description="Filter by service status")] = None,
    search: Annotated[str | None, Query(description="Search term for service name")] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 50,
) -> StandardResponse[list[ServiceResponse]]:
    """List software services with status and metadata."""
    query = select(Service).options(selectinload(Service.repository))

    if repository_id:
        query = query.where(Service.repository_id == repository_id)
    if status_filter:
        query = query.where(Service.status == status_filter)
    if search:
        query = query.where(Service.name.ilike(f"%{search}%"))

    # Count
    count_query = select(func.count(Service.id))
    if repository_id:
        count_query = count_query.where(Service.repository_id == repository_id)
    if status_filter:
        count_query = count_query.where(Service.status == status_filter)
    if search:
        count_query = count_query.where(Service.name.ilike(f"%{search}%"))
    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    offset = (page - 1) * limit
    query = query.order_by(Service.name.asc()).offset(offset).limit(limit)

    result = await db.execute(query)
    services = result.scalars().all()

    items = [
        ServiceResponse(
            id=s.id,
            name=s.name,
            service_type=s.service_type,
            status=s.status,
            runtime=s.runtime,
            version=s.version,
            repository_id=s.repository_id,
            repository_name=s.repository.name if s.repository else None,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in services
    ]

    meta = PaginationMeta(
        total=total,
        page=page,
        limit=limit,
        pages=max(1, (total + limit - 1) // limit),
    ).model_dump()

    return StandardResponse(data=items, meta=meta)


@router.post("", response_model=StandardResponse[ServiceResponse], status_code=status.HTTP_201_CREATED)
async def create_service(
    payload: ServiceCreate,
    db: DatabaseSession,
) -> StandardResponse[ServiceResponse]:
    """Register a new service."""
    repo = await db.get(Repository, payload.repository_id)
    if not repo:
        raise AppException(
            code="REPOSITORY_NOT_FOUND",
            message=f"Repository with ID '{payload.repository_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    service = Service(
        name=payload.name,
        service_type=payload.service_type,
        status=payload.status,
        runtime=payload.runtime,
        version=payload.version,
        repository_id=payload.repository_id,
    )
    db.add(service)
    await db.flush()

    activity = Activity(
        actor="system",
        action="service_registered",
        entity_type="service",
        entity_name=service.name,
        details=f"Service {service.name} ({service.service_type}) registered in repo {repo.name}",
    )
    db.add(activity)
    await db.commit()
    await db.refresh(service)

    return StandardResponse(
        data=ServiceResponse(
            id=service.id,
            name=service.name,
            service_type=service.service_type,
            status=service.status,
            runtime=service.runtime,
            version=service.version,
            repository_id=service.repository_id,
            repository_name=repo.name,
            created_at=service.created_at,
            updated_at=service.updated_at,
        )
    )
