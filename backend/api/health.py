"""
backend/api/health.py

GET /api/health — liveness and provider info endpoint.

Returns:
    {
        "status": "ok",
        "llm": { "provider": "gemini", "model": "gemini-1.5-flash" },
        "embeddings": { "provider": "gemini", "model": "models/text-embedding-004" }
    }
"""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.config import get_settings

router = APIRouter(prefix="/api", tags=["health"])


class ProviderInfo(BaseModel):
    provider: str
    model: str


class HealthResponse(BaseModel):
    status: str
    llm: ProviderInfo
    embeddings: ProviderInfo


@router.get("/health", response_model=HealthResponse, summary="Health check + active provider info")
def health_check() -> HealthResponse:
    """
    Returns the server status and which LLM / embedding provider is active.
    Useful for confirming config changes took effect without restarting.
    """
    cfg = get_settings()
    return HealthResponse(
        status="ok",
        llm=ProviderInfo(provider=cfg.llm.provider, model=cfg.llm.model),
        embeddings=ProviderInfo(
            provider=cfg.embeddings.provider,
            model=cfg.embeddings.model,
        ),
    )
