import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.errors import AppException
from app.models.activity import Activity
from app.models.project import Project
from app.models.repository import Repository
from app.schemas.common import PaginationMeta, StandardResponse
from app.schemas.repository import RepositoryCreate, RepositoryResponse

router = APIRouter(prefix="/repositories", tags=["Repositories"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=StandardResponse[list[RepositoryResponse]])
async def list_repositories(
    db: DatabaseSession,
    search: Annotated[str | None, Query(description="Search term for repository name or URL")] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 50,
) -> StandardResponse[list[RepositoryResponse]]:
    """List all registered repositories with service and finding counts."""
    query = select(Repository).options(
        selectinload(Repository.services),
        selectinload(Repository.findings),
    )

    if search:
        search_filter = f"%{search}%"
        query = query.where((Repository.name.ilike(search_filter)) | (Repository.url.ilike(search_filter)))

    # Get total count
    count_query = select(func.count(Repository.id))
    if search:
        search_filter = f"%{search}%"
        count_query = count_query.where((Repository.name.ilike(search_filter)) | (Repository.url.ilike(search_filter)))
    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    # Paginate
    offset = (page - 1) * limit
    query = query.order_by(Repository.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    repos = result.scalars().all()

    items = [
        RepositoryResponse(
            id=r.id,
            name=r.name,
            url=r.url,
            default_branch=r.default_branch,
            language=r.language,
            status=r.status,
            project_id=r.project_id,
            services_count=len(r.services),
            findings_count=len(r.findings),
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in repos
    ]

    meta = PaginationMeta(
        total=total,
        page=page,
        limit=limit,
        pages=max(1, (total + limit - 1) // limit),
    ).model_dump()

    return StandardResponse(data=items, meta=meta)


@router.post("", response_model=StandardResponse[RepositoryResponse], status_code=status.HTTP_201_CREATED)
async def create_repository(
    payload: RepositoryCreate,
    db: DatabaseSession,
) -> StandardResponse[RepositoryResponse]:
    """Register a new repository."""
    # Verify project exists, or if none provided, create a default organization & project for local bootstrap
    project = await db.get(Project, payload.project_id)
    if not project:
        raise AppException(
            code="PROJECT_NOT_FOUND",
            message=f"Project with ID '{payload.project_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    repo = Repository(
        name=payload.name,
        url=payload.url,
        default_branch=payload.default_branch,
        language=payload.language,
        status=payload.status,
        project_id=payload.project_id,
    )
    db.add(repo)
    await db.flush()

    # Log activity
    activity = Activity(
        actor="user",
        action="repository_connected",
        entity_type="repository",
        entity_name=repo.name,
        details=f"Repository {repo.name} ({repo.url}) connected on branch {repo.default_branch}",
    )
    db.add(activity)
    await db.commit()
    await db.refresh(repo)

    response_data = RepositoryResponse(
        id=repo.id,
        name=repo.name,
        url=repo.url,
        default_branch=repo.default_branch,
        language=repo.language,
        status=repo.status,
        project_id=repo.project_id,
        services_count=0,
        findings_count=0,
        created_at=repo.created_at,
        updated_at=repo.updated_at,
    )
    return StandardResponse(data=response_data)


@router.get("/{repository_id}", response_model=StandardResponse[RepositoryResponse])
async def get_repository(
    repository_id: uuid.UUID,
    db: DatabaseSession,
) -> StandardResponse[RepositoryResponse]:
    """Get single repository by ID."""
    query = (
        select(Repository)
        .options(selectinload(Repository.services), selectinload(Repository.findings))
        .where(Repository.id == repository_id)
    )
    res = await db.execute(query)
    repo = res.scalar_one_or_none()

    if not repo:
        raise AppException(
            code="REPOSITORY_NOT_FOUND",
            message=f"Repository with ID '{repository_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    data = RepositoryResponse(
        id=repo.id,
        name=repo.name,
        url=repo.url,
        default_branch=repo.default_branch,
        language=repo.language,
        status=repo.status,
        project_id=repo.project_id,
        services_count=len(repo.services),
        findings_count=len(repo.findings),
        created_at=repo.created_at,
        updated_at=repo.updated_at,
    )
    return StandardResponse(data=data)
