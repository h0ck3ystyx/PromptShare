"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.middleware import TimingMiddleware
from src.routers import (
    analytics,
    auth,
    categories,
    comments,
    follows,
    notifications,
    prompts,
    ratings,
    search,
    upvotes,
    users,
)

app = FastAPI(
    title=settings.app_name,
    description="Internal prompt-sharing web application",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Converted from comma-separated string
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(TimingMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(prompts.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(comments.router, prefix="/api")
app.include_router(ratings.router, prefix="/api")
app.include_router(upvotes.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(follows.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")


@app.get("/", summary="Root endpoint")
async def root() -> dict:
    """
    Root endpoint for health check.

    Returns:
        dict: Application information
    """
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/api/health", summary="Health check endpoint")
async def health_check() -> dict:
    """
    Health check endpoint.

    Returns:
        dict: Health status
    """
    return {"status": "healthy"}

