"""
backend/api/config.py

Configuration routes for managing runtime settings like active LLM models.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import urllib.request
import json
import os

from backend.config import get_settings
from backend.config.settings import LLMModels


router = APIRouter(prefix="/api/config", tags=["config"])


AVAILABLE_MODELS: dict[str, list[str]] = {
    "gemini": ["gemini-3.7-flash", "gemini-3.5-flash", "gemini-2.5-pro", "gemini-flash-latest"],
    "openai": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
    "anthropic": ["claude-3-haiku-20240307", "claude-3-5-sonnet-20240620", "claude-3-opus-20240229"],
    "ollama": ["llama3.2", "mistral", "gemma2"],
    "vertexai": ["gemini-3.7-flash", "gemini-3.5-flash", "gemini-2.5-pro"],
}

_models_fetched = False

def fetch_gemini_models():
    """Lazily fetch models from the Gemini API and cache them."""
    global _models_fetched
    if _models_fetched:
        return
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return
        
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        req = urllib.request.urlopen(url, timeout=3)
        data = json.loads(req.read())
        
        # Filter for models that support text generation
        valid_models = []
        for m in data.get("models", []):
            methods = m.get("supportedGenerationMethods", [])
            if "generateContent" in methods:
                name = m.get("name", "").replace("models/", "")
                valid_models.append(name)
                
        if valid_models:
            AVAILABLE_MODELS["gemini"] = valid_models
            AVAILABLE_MODELS["vertexai"] = valid_models
        
        _models_fetched = True
    except Exception as e:
        print(f"Warning: Failed to fetch Gemini models dynamically: {e}")


class LLMConfigResponse(BaseModel):
    provider: str
    model: str
    available_providers: list[str]
    available_models: dict[str, list[str]]

class LLMUpdateRequest(BaseModel):
    provider: str
    model: str

@router.get("/llm", response_model=LLMConfigResponse)
def get_llm_config() -> LLMConfigResponse:
    """Return the currently active LLM provider and model, and all available options."""
    fetch_gemini_models()
    
    cfg = get_settings()
    providers = list(AVAILABLE_MODELS.keys())

    return LLMConfigResponse(
        provider=cfg.llm.provider,
        model=cfg.llm.model,
        available_providers=providers,
        available_models=AVAILABLE_MODELS,
    )

@router.put("/llm")
def update_llm_config(request: LLMUpdateRequest) -> LLMConfigResponse:
    """
    Update the active LLM provider and model.
    This modifies the in-memory global settings object.
    """
    fetch_gemini_models()
    
    if request.provider not in AVAILABLE_MODELS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {request.provider}")
        
    if request.model not in AVAILABLE_MODELS[request.provider]:
        raise HTTPException(
            status_code=400, 
            detail=f"Model '{request.model}' is not in the list of available models for {request.provider}."
        )

    # Mutate the global singleton
    cfg = get_settings()
    cfg.llm.provider = request.provider
    cfg.llm.model = request.model
    
    return get_llm_config()
