"""SmartBudget AI — FastAPI gateway."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import routes_auth, routes_budget, routes_expense, routes_profile
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging_config import configure_logging
from app.db import init_db
from app.rag.knowledge_base import seed_knowledge_base

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s (env=%s)", settings.app_name, settings.environment)
    init_db()
    seed_knowledge_base()
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(title=settings.app_name, version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

API_PREFIX = "/api/v1"
app.include_router(routes_auth.router, prefix=API_PREFIX)
app.include_router(routes_profile.router, prefix=API_PREFIX)
app.include_router(routes_expense.router, prefix=API_PREFIX)
app.include_router(routes_budget.router, prefix=API_PREFIX)


@app.get("/")
def root():
    return {"service": settings.app_name, "status": "running", "docs": "/docs"}


@app.get("/healthz")
def healthz():
    """Liveness/readiness probe for load balancers, Docker healthchecks, etc."""
    return {"status": "ok"}
