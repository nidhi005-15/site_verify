from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routes.health import router as health_router
from routes.upload import router as upload_router

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Deterministic PDF claim, citation, integrity, and grounded Q&A verification API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(upload_router)
