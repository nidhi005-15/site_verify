from __future__ import annotations

from fastapi import APIRouter

from config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, object]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "llm_enabled": settings.llm_enabled,
        "llm_provider": settings.llm_provider if settings.llm_enabled else "disabled",
        "local_nlp_enabled": settings.local_nlp_enabled,
    }
