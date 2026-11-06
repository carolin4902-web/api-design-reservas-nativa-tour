# app/api/v1/reservas.py
from typing import Annotated
from fastapi import APIRouter, Depends, status

from app.api.deps import get_reserva_service
from app.models.Reserva import ReservaCreate, ReservaPublic, ReservaUpdate
from app.services.reserva import ReservaService

router = APIRouter(prefix="/reservas", tags=["Reservas"])


@router.post("", response_model=ReservaPublic, status_code=status.HTTP_201_CREATED)
async def create_reserva(
    reserva_in: ReservaCreate,
    service: Annotated[ReservaService, Depends(get_reserva_service)],
) -> ReservaPublic:
    """Crea una solicitud de reserva verificando cupos y estado del turista."""
    db_reserva = await service.create(reserva_in)
    return ReservaPublic.model_validate(db_reserva)


@router.get("", response_model=list[ReservaPublic])
async def list_reservas(
    service: Annotated[ReservaService, Depends(get_reserva_service)],
    skip: int = 0,
    limit: int = 100,
    turista_id: int | None = None,
) -> list[ReservaPublic]:
    """Obtiene el listado general de reservas o filtradas por turista."""
    reservas = await service.list_all(skip=skip, limit=limit, turista_id=turista_id)
    return [ReservaPublic.model_validate(r) for r in reservas]


@router.get("/{reserva_id}", response_model=ReservaPublic)
async def get_reserva(
    reserva_id: int,
    service: Annotated[ReservaService, Depends(get_reserva_service)],
) -> ReservaPublic:
    """Obtiene el detalle de una reserva específica."""
    db_reserva = await service.get_by_id(reserva_id)
    return ReservaPublic.model_validate(db_reserva)


@router.patch("/{reserva_id}", response_model=ReservaPublic)
async def update_reserva(
    reserva_id: int,
    reserva_in: ReservaUpdate,
    service: Annotated[ReservaService, Depends(get_reserva_service)],
) -> ReservaPublic:
    """Modifica el estado o cantidad de personas en una reserva."""
    db_reserva = await service.update(reserva_id, reserva_in)
    return ReservaPublic.model_validate(db_reserva)


@router.delete("/{reserva_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reserva(
    reserva_id: int,
    service: Annotated[ReservaService, Depends(get_reserva_service)],
) -> None:
    """Cancela o elimina una reserva activa."""
    await service.delete(reserva_id)