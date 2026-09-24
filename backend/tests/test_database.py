"""Tests for database initialization."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.project import Project


@pytest.mark.asyncio
async def test_database_session_can_create_organization(test_session: AsyncSession):
    """Test that we can create an organization in the database."""
    org = Organization(name="Test Organization")
    test_session.add(org)
    await test_session.commit()

    assert org.id is not None
    assert org.name == "Test Organization"
    assert org.created_at is not None
    assert org.updated_at is not None


@pytest.mark.asyncio
async def test_database_session_can_create_project(test_session: AsyncSession):
    """Test that we can create a project in the database."""
    org = Organization(name="Test Organization")
    test_session.add(org)
    await test_session.commit()

    project = Project(name="Test Project", organization_id=org.id)
    test_session.add(project)
    await test_session.commit()

    assert project.id is not None
    assert project.name == "Test Project"
    assert project.organization_id == org.id


@pytest.mark.asyncio
async def test_organization_project_relationship(test_session: AsyncSession):
    """Test the relationship between organization and projects."""
    org = Organization(name="Test Organization")
    test_session.add(org)
    await test_session.commit()

    project1 = Project(name="Project 1", organization_id=org.id)
    project2 = Project(name="Project 2", organization_id=org.id)
    test_session.add_all([project1, project2])
    await test_session.commit()

    # Refresh to load relationships
    await test_session.refresh(org, ["projects"])

    assert len(org.projects) == 2
    assert project1 in org.projects
    assert project2 in org.projects
