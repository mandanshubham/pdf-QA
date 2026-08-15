"""
backend/main.py

FastAPI application entry point.

Mounts all API routers and configures CORS.
Each phase adds its router here as features are built.

Run:
    uvicorn backend.main:app --reload
    
Docs:
    http://localhost:8000/docs       (Swagger UI)
    http://localhost:8000/redoc      (ReDoc)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.health import router as health_router
from backend.config import get_settings

# ── App instance ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="PDF-QA API",
    description=(
        "Agentic PDF Question-Answering system. "
        "Upload PDFs and ask questions grounded in their content."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────

cfg = get_settings()

if cfg.api.cors_allow_all:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ── Routers ───────────────────────────────────────────────────────────────────
# Add new routers here as each phase is completed:

from backend.api.chat import router as chat_router
from backend.api.documents import router as documents_router

app.include_router(health_router)           # Phase 2  — /api/health
app.include_router(documents_router)        # Phase 3  — /api/documents
app.include_router(chat_router)             # Phase 4  — /api/chat
# app.include_router(agent_router)          # Phase 6  — /api/agent

# ── Root ─────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def root() -> dict:
    return {
        "name": "PDF-QA API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/health",
    }
