"""
Sen2Nal FastAPI Application

Main entry point for the REST API server.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routers.alerts import router as alerts_router
from src.api.routers.experiments import router as experiments_router
from src.api.routers.pipeline import router as pipeline_router
from src.api.routers.stocks import router as stocks_router
from src.config import settings
from src.constants import API_VERSION

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("=" * 80)
    logger.info("Starting Sen2Nal API Server...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"API Version: {API_VERSION}")
    logger.info(f"Database: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    logger.info("=" * 80)

    # Check database connection
    from src.database.connection import check_db_connection

    if check_db_connection():
        logger.info("✓ Database connection successful")
    else:
        logger.warning("⚠ Database connection failed - check your configuration")

    # Start pipeline scheduler if enabled
    scheduler = None
    if settings.enable_scheduler:
        from src.pipeline.scheduler import start_scheduler

        scheduler = start_scheduler()
        logger.info("✓ Pipeline scheduler started")

    yield

    # Shutdown
    if scheduler:
        from src.pipeline.scheduler import stop_scheduler

        stop_scheduler()
    logger.info("Shutting down Sen2Nal API Server...")


# Create FastAPI application
app = FastAPI(
    title="Sen2Nal API",
    description="Stock Sentiment + Calendar Signal Analysis System",
    version="1.0.0",
    docs_url=f"/api/{API_VERSION}/docs",
    redoc_url=f"/api/{API_VERSION}/redoc",
    openapi_url=f"/api/{API_VERSION}/openapi.json",
    lifespan=lifespan,
)

# CORS Configuration
if settings.enable_cors:
    allowed_origins = ["*"] if settings.is_development else settings.allowed_hosts.split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS enabled for origins: {allowed_origins}")


# =============================================================================
# Health Check Endpoint
# =============================================================================


@app.get(f"/api/{API_VERSION}/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns system status and basic metrics.
    """
    from src.database.connection import check_db_connection

    db_status = "connected" if check_db_connection() else "disconnected"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "version": "1.0.0",
        "api_version": API_VERSION,
        "environment": settings.environment,
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


# =============================================================================
# Root Endpoint
# =============================================================================


@app.get("/", tags=["Root"])
async def root():
    """
    API root endpoint with basic information.
    """
    return {
        "message": "Sen2Nal API - Stock Sentiment + Calendar Signal Analysis",
        "version": "1.0.0",
        "docs": f"/api/{API_VERSION}/docs",
        "health": f"/api/{API_VERSION}/health",
    }


# =============================================================================
# Exception Handlers
# =============================================================================


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 Not Found errors."""
    return JSONResponse(
        status_code=404,
        content={"error": {"code": "NOT_FOUND", "message": "Resource not found", "details": None}},
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 Internal Server errors."""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal server error occurred",
                "details": None,
            }
        },
    )


app.include_router(stocks_router)
app.include_router(experiments_router)
app.include_router(pipeline_router)
app.include_router(alerts_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )
