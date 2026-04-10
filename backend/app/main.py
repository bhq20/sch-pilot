"""SCH Pilot — FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    auth,
    cost_centers,
    costing,
    dashboard,
    lancamentos,
    reports,
)

app = FastAPI(
    title="SCH — Sistema de Custeio Hospitalar (Piloto)",
    description=(
        "API multi-tenant para custeio hospitalar dual-segment "
        "(humana e veterinária). Métodos: RKW e Custeio Variável."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cost_centers.router)
app.include_router(lancamentos.router)
app.include_router(costing.router)
app.include_router(dashboard.router)
app.include_router(reports.router)


@app.get("/")
def root():
    return {
        "service": "SCH Pilot API",
        "version": "0.1.0",
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
