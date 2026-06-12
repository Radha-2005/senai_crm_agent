"""
main.py - FastAPI application entry point.
Configures the app, routers, CORS, database initialization, and startup events.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from backend.config import settings
from backend.db.session import engine
from backend.db.models import Base

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # ---- STARTUP ----
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Create database tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized")

    # Seed knowledge base if empty
    try:
        from backend.rag.rag_service import get_kb_stats
        kb_stats = get_kb_stats()
        if kb_stats.get("document_count", 0) == 0:
            logger.info("Knowledge base empty, seeding from markdown files...")
            from backend.rag.kb_seed import seed_knowledge_base
            count = await seed_knowledge_base()
            logger.info(f"Knowledge base seeded with {count} chunks")
        else:
            logger.info(f"Knowledge base has {kb_stats['document_count']} documents")
    except Exception as e:
        logger.warning(f"KB seeding skipped: {e}")

    logger.info("Application startup complete")
    yield
    
    # ---- SHUTDOWN ----
    logger.info("Shutting down application")
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    **SenAI CRM Agentic Intelligence Platform**
    
    A production-grade AI-powered CRM system with:
    - Autonomous email triage using ReAct agent
    - Multi-layer classification (heuristics + LLM)
    - RAG-powered policy retrieval
    - Real-time analytics dashboard
    - GDPR, Security, and SLA breach detection
    """,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# --- Register Routers ---
from backend.api.ingest import router as ingest_router
from backend.api.status import router as status_router
from backend.api.threads import router as threads_router
from backend.api.contacts import router as contacts_router
from backend.api.rag import router as rag_router
from backend.api.analytics import router as analytics_router
from backend.api.agent import router as agent_router
from backend.api.dashboard import router as dashboard_router

app.include_router(ingest_router)
app.include_router(status_router)
app.include_router(threads_router)
app.include_router(contacts_router)
app.include_router(rag_router)
app.include_router(analytics_router)
app.include_router(agent_router)
app.include_router(dashboard_router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint — redirects to API docs."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
        "health": "/api/v1/health",
    }
