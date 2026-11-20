# app/api/deps.py
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session

# Importación de Repositorios
from app.repositories.destination import DestinationRepository
from app.repositories.turista import TuristaRepository
from app.repositories.guia import GuiaRepository
from app.repositories.tour import TourRepository
from app.repositories.reserva import ReservaRepository

# Importación de Servicios
from app.services.destination import DestinationService
from app.services.turista import TuristaService
from app.services.guia import GuiaService
from app.services.tour import TourService
from app.services.reserva import ReservaService


# ==========================================
# Proveedores de Servicios (Inyección)
# ==========================================

def get_destination_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DestinationService:
    """Instancia y retorna el servicio de destinos con su respectivo repositorio."""
    return DestinationService(DestinationRepository(session))


def get_turista_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TuristaService:
    """Instancia y retorna el servicio de turistas con su respectivo repositorio."""
    return TuristaService(TuristaRepository(session))


def get_guia_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GuiaService:
    """Instancia y retorna el servicio de guías con su respectivo repositorio."""
    return GuiaService(GuiaRepository(session))


def get_tour_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TourService:
    """Instancia y retorna el servicio de tours coordinando los repositorios de Tour y Guía."""
    return TourService(
        tour_repo=TourRepository(session),
        guia_repo=GuiaRepository(session)
    )


def get_reserva_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ReservaService:
    """Instancia y retorna el servicio de reservas coordinando los repositorios necesarios."""
    return ReservaService(
        reserva_repo=ReservaRepository(session),
        turista_repo=TuristaRepository(session),
        tour_repo=TourRepository(session),
    )


# ==========================================
# Alias de Tipo para Inyección en Routers (Annotated)
# ==========================================

DestinationServiceDep = Annotated[DestinationService, Depends(get_destination_service)]
TuristaServiceDep = Annotated[TuristaService, Depends(get_turista_service)]
GuiaServiceDep = Annotated[GuiaService, Depends(get_guia_service)]
TourServiceDep = Annotated[TourService, Depends(get_tour_service)]
ReservaServiceDep = Annotated[ReservaService, Depends(get_reserva_service)]