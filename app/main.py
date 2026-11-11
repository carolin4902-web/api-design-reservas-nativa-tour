from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models
from app.core.database import init_db, engine
from app.api.v1 import guias, reservas, tours, turistas


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el inicio y cierre de la aplicación."""

    await init_db()

    yield

    await engine.dispose()


app = FastAPI(
    title="Nativa Tour API",
    description="API REST para gestionar tours y reservas turísticas.",
    version="1.0.0",
    lifespan=lifespan,
)

# Registro de enrutadores modulares de la versión 1
app.include_router(turistas.router, prefix="/api/v1", tags=["turistas"])
app.include_router(guias.router, prefix="/api/v1", tags=["guias"])
app.include_router(tours.router, prefix="/api/v1", tags=["tours"])
app.include_router(reservas.router, prefix="/api/v1", tags=["reservas"])


@app.get("/")
async def root():
    return {
        "message": "Bienvenido a Nativa Tour API",
        "status": "running",
    }