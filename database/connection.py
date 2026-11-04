# -*- coding: utf-8 -*-
"""
Database Connection & Session Management
Uses SQLAlchemy 2.0 Async with native support for SQLite and PostgreSQL.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine
)
from config import settings
from database.models import Base

# Configure engine with pooling and sanity checks
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)

# Async session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def init_db() -> None:
    """Initialize database tables asynchronously on bot startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency helper for acquiring an active database session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
