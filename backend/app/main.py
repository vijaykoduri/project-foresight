import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    alerts,
    analytics,
    auth,
    dashboard,
    forecast,
    health,
    inventory,
    products,
    recommendations,
    reports,
    sales,
    suppliers,
    users,
)
from app.core.config import get_settings
from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title="FORESIGHT API",
    description="AI-Powered Demand & Inventory Intelligence Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(sales.router, prefix="/api")
app.include_router(suppliers.router, prefix="/api")
app.include_router(forecast.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    logger.info("FORESIGHT API starting up in %s mode", settings.environment)


@app.get("/")
async def root():
    return {"message": "FORESIGHT API", "docs": "/api/docs", "health": "/api/health"}
