"""Database engine and session management for the Edge SQLite Runtime."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.edge.models import EdgeBase


EDGE_DIR = Path(__file__).resolve().parent.parent.parent / "artifacts" / "edge"
EDGE_DB_PATH = EDGE_DIR / "edge_node.db"


class EdgeDatabaseManager:
    """Manages the lifecycle of the local SQLite database for the Edge runtime."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or EDGE_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_url = f"sqlite+aiosqlite:///{self.db_path}"
        self.engine: AsyncEngine = create_async_engine(self.db_url, echo=False)
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def init_db(self) -> None:
        """Create all edge tables in SQLite."""
        async with self.engine.begin() as conn:
            await conn.run_sync(EdgeBase.metadata.create_all)

    async def reset_db(self) -> None:
        """Drop and recreate all edge tables for testing."""
        async with self.engine.begin() as conn:
            await conn.run_sync(EdgeBase.metadata.drop_all)
            await conn.run_sync(EdgeBase.metadata.create_all)

    async def close(self) -> None:
        """Dispose of the engine connection pool."""
        await self.engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager for an async database session with automatic commit/rollback."""
        async with self.session_factory() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise


# Default singleton instance
_edge_db_manager = EdgeDatabaseManager()


def get_edge_db_manager() -> EdgeDatabaseManager:
    """Access the singleton EdgeDatabaseManager instance."""
    return _edge_db_manager


async def get_edge_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for obtaining an edge database session."""
    async with _edge_db_manager.session() as session:
        yield session
