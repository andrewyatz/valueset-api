"""Main FastAPI application."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers import health, terms, valuesets


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup: initialize database
    init_db()
    yield
    # Shutdown: SQLAlchemy handles cleanup automatically


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url=None,  # Disable default Redoc to use custom route
    openapi_url="/openapi.json" if settings.enable_docs or settings.enable_redoc else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include routers
app.include_router(health.router)
app.include_router(terms.router)
app.include_router(valuesets.router)


if settings.enable_redoc:

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html() -> HTMLResponse:
        """Custom Redoc documentation route with stable assets."""
        return get_redoc_html(
            openapi_url=app.openapi_url or "/openapi.json",
            title=app.title + " - ReDoc",
            redoc_js_url="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js",
        )


if settings.enable_browse:
    _static_dir = Path("static")
    if not _static_dir.is_dir():
        raise RuntimeError(
            "ENABLE_BROWSE=True but the 'static/' directory was not found. "
            "Ensure static files are present or set ENABLE_BROWSE=False."
        )
    # Serve static files for the /browse endpoint
    app.mount("/browse", StaticFiles(directory="static", html=True), name="static")

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        """Redirect root to browse interface if enabled, otherwise docs."""
        return RedirectResponse(url="/browse")


else:

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        """Redirect root to API documentation."""
        return RedirectResponse(url="/docs" if settings.enable_docs else "/list/valuesets")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers if not settings.reload else 1,
    )
