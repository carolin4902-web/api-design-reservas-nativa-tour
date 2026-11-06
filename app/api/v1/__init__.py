# app/api/v1/__init__.py
from fastapi import APIRouter

# Importación de los routers individuales
from app.api.v1.turistas import router as turistas_router
from app.api.v1.guias import router as guias_router
from app.api.v1.tours import router as tours_router
from app.api.v1.reservas import router as reservas_router

# Enrutador principal agrupador con el prefijo /v1
api_router = APIRouter(prefix="/v1")

# Inclusión de cada sub-router
api_router.include_router(turistas_router)
api_router.include_router(guias_router)
api_router.include_router(tours_router)
api_router.include_router(reservas_router)