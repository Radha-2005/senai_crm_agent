"""
db/session.py - Async SQLAlchemy engine and session factory.
Configures the database connection pool for both PostgreSQL and SQLite (testing).
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from backend.config import settings

# Detect if we are using SQLite (for testing) vs PostgreSQL (production)
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# For SQLite use NullPool (no connection pooling - required for async SQLite).
# For PostgreSQL use default pool settings for better performance.
if _is_sqlite:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=(settings.LOG_LEVEL == "DEBUG"),
        poolclass=NullPool,
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=(settings.LOG_LEVEL == "DEBUG"),
        pool_size=10,
        max_overflow=20,
    )

# Session factory: expire_on_commit=False keeps objects usable after commit
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """FastAPI dependency that provides a database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
