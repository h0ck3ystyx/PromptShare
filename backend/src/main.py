"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.middleware import TimingMiddleware
from src.routers import (
    analytics,
    auth,
    categories,
    collections,
    comments,
    faqs,
    follows,
    notifications,
    onboarding,
    prompts,
    ratings,
    search,
    upvotes,
    users,
)

app = FastAPI(
    title=settings.app_name,
    description=(
        "Internal prompt-sharing web application for employees to discover, submit, "
        "and collaborate on prompts for AI tools (GitHub Copilot, O365 Copilot, Cursor, Claude).\n\n"
        "## Features\n\n"
        "- **Prompt Management**: Create, update, and browse prompts with categories and platform tags\n"
        "- **Search & Discovery**: Full-text search with filters for platform, category, and keywords\n"
        "- **Collaboration**: Comments, ratings, and upvotes on prompts\n"
        "- **Collections**: Curated sets of prompts organized by theme or use case\n"
        "- **Notifications**: Get notified about new prompts in categories you follow\n"
        "- **Analytics**: Track usage statistics (views, copies, searches) - Admin only\n"
        "- **Onboarding**: Get started guides, best practices, and FAQs\n\n"
        "## Authentication\n\n"
        "All endpoints except `/api/onboarding` and `/api/faqs` (read-only) require authentication via LDAP/Active Directory.\n\n"
        "## Documentation\n\n"
        "- Interactive API docs: `/api/docs` (Swagger UI)\n"
        "- Alternative docs: `/api/redoc` (ReDoc)\n"
        "- Onboarding materials: `/api/onboarding`\n"
        "- Best practices: `/api/onboarding/best-practices`\n"
    ),
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
app.include_router(collections.router, prefix="/api")
app.include_router(faqs.router, prefix="/api")
app.include_router(onboarding.router, prefix="/api")


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

