from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import app.models
from app.api.v1 import guias, reservas, tours, turistas
from app.core.database import engine, init_db
from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    DomainError,
    NotFoundError,
)


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


@app.exception_handler(DomainError)
async def handle_domain_error(
    _request: Request,
    exc: DomainError,
) -> JSONResponse:
    if isinstance(exc, NotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ConflictError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, BusinessRuleError):
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
