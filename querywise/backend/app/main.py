import os
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import Base, engine
from app.api import analyze, history, dashboard, recommendations, explorer
from app.scheduler import start_scheduler


# ============================================================
# Load environment variables from .env
# ============================================================

load_dotenv()


# ============================================================
# Logging
# ============================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("querywise")


# ============================================================
# Frontend configuration
# ============================================================

FRONTEND_ORIGIN = os.getenv(
    "FRONTEND_ORIGIN",
    "http://localhost:5173"
)

print("===================================")
print(">>> FRONTEND_ORIGIN:", FRONTEND_ORIGIN)
print("===================================")


# ============================================================
# Application lifespan
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    """

    # Create app-db tables if they don't exist yet.
    # This is a simple MVP approach without migrations.
    Base.metadata.create_all(bind=engine)

    # Start background scheduler
    scheduler = start_scheduler()

    yield

    # Shutdown scheduler
    scheduler.shutdown(wait=False)


# ============================================================
# FastAPI application
# ============================================================

app = FastAPI(
    title="QueryWise API",
    description="Intelligent Database Query Optimizer & Index Advisor",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# CORS Configuration
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ============================================================
# Global Exception Handler
# ============================================================

@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception
):
    """
    Catch-all exception handler.

    Raw Python/PostgreSQL tracebacks are never returned
    directly to the frontend.
    """

    logger.exception(
        "Unhandled error on %s",
        request.url.path
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Something went wrong on our end. Please try again.",
        },
    )


# ============================================================
# API Routers
# ============================================================

app.include_router(analyze.router)
app.include_router(history.router)
app.include_router(dashboard.router)
app.include_router(recommendations.router)
app.include_router(explorer.router)


# ============================================================
# Root Endpoint
# ============================================================

@app.get("/")
def root():
    return {
        "name": "QueryWise API",
        "status": "running"
    }


# ============================================================
# Health Check
# ============================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "ok"
    }