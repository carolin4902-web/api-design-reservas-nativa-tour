from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models
from app.core.database import init_db, engine


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


@app.get("/")
async def root():
    return {
        "message": "Bienvenido a Nativa Tour API",
        "status": "running",
    }