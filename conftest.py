"""
conftest.py - Pytest configuration and shared fixtures.
Sets up async test database and session fixtures.
"""
import asyncio
import os
import pytest
import pytest_asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

# Use file-based SQLite for tests (background tasks need same DB file)
TEST_DB_PATH = Path(__file__).parent / "test_temp.db"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"


@pytest.fixture(scope="session")
def anyio_backend():
    """Force asyncio backend — required on Windows to avoid trio conflicts."""
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine (session-scoped)."""
    # Override settings for tests
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )
    
    # Patch session module to use test engine
    import backend.db.session as session_module
    session_module.engine = engine
    session_module.AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Also patch the worker module
    import backend.workers.email_processor as worker_module
    # Workers import AsyncSessionLocal at module level; patch it
    from backend.db.session import AsyncSessionLocal
    worker_module.AsyncSessionLocal = session_module.AsyncSessionLocal
    
    # Create tables
    from backend.db.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    
    # Remove test DB file
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest_asyncio.fixture
async def db(test_engine):
    """Provide an async database session for each test."""
    from backend.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
