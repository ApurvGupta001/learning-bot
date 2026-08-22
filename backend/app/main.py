"""FastAPI entrypoint.

Only the app skeleton and a health check live here for now. Routers for
sessions, progress, and the MCP registry are added in later steps.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import settings

app = FastAPI(
    title="Personalized Learning Bot",
    version=__version__,
    description="MCP-powered adaptive learning chatbot (backend API).",
)

# Allow the Next.js dev server to call the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health() -> dict:
    """Liveness check."""
    return {"status": "ok", "version": __version__, "env": settings.app_env}


# --- Routers (added in later steps) ---------------------------------------
# from app.routers import sessions, progress, mcp_registry
# app.include_router(sessions.router)
# app.include_router(progress.router)
# app.include_router(mcp_registry.router)
