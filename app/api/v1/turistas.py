# app/api/v1/turistas.py
from typing import Annotated
from fastapi import APIRouter, Depends, status

from app.api.deps import get_turista_service
from app.models.Turista import TuristaCreate, TuristaPublic, TuristaUpdate
from app.services.turista import TuristaService

router = APIRouter(prefix="/turistas", tags=["Turistas"])


@router.post("", response_model=TuristaPublic, status_code=status.HTTP_201_CREATED)
async def create_turista(
    turista_in: TuristaCreate,
    service: Annotated[TuristaService, Depends(get_turista_service)],
) -> TuristaPublic:
    """Registra un nuevo turista en Nativa-Tour."""
    db_turista = await service.create(turista_in)
    return TuristaPublic.model_validate(db_turista)


@router.get("", response_model=list[TuristaPublic])
async def list_turistas(
    service: Annotated[TuristaService, Depends(get_turista_service)],
    skip: int = 0,
    limit: int = 100,
) -> list[TuristaPublic]:
    """Obtiene la lista de turistas registrados."""
    turistas = await service.list_all(skip=skip, limit=limit)
    return [TuristaPublic.model_validate(t) for t in turistas]


@router.get("/{turista_id}", response_model=TuristaPublic)
async def get_turista(
    turista_id: int,
    service: Annotated[TuristaService, Depends(get_turista_service)],
) -> TuristaPublic:
    """Obtiene el detalle de un turista por su ID."""
    db_turista = await service.get_by_id(turista_id)
    return TuristaPublic.model_validate(db_turista)


@router.patch("/{turista_id}", response_model=TuristaPublic)
async def update_turista(
    turista_id: int,
    turista_in: TuristaUpdate,
    service: Annotated[TuristaService, Depends(get_turista_service)],
) -> TuristaPublic:
    """Actualiza la información de un turista."""
    db_turista = await service.update(turista_id, turista_in)
    return TuristaPublic.model_validate(db_turista)


@router.delete("/{turista_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_turista(
    turista_id: int,
    service: Annotated[TuristaService, Depends(get_turista_service)],
) -> None:
    """Elimina un turista del sistema."""
    await service.delete(turista_id)