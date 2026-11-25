# app/api/v1/tours.py
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_tour_service
from app.models.Tour import TourCreate, TourPublic, TourUpdate
from app.services.tour import TourService

router = APIRouter(prefix="/tours", tags=["tours"])


@router.post("", response_model=TourPublic, status_code=status.HTTP_201_CREATED)
async def create_tour(
    tour_in: TourCreate,
    service: Annotated[TourService, Depends(get_tour_service)],
) -> TourPublic:
    """Crea una nueva propuesta de tour guiado."""
    return await service.create(tour_in)


@router.get("", response_model=list[TourPublic])
async def list_tours(
    service: Annotated[TourService, Depends(get_tour_service)],
    skip: int = 0,
    limit: int = 100,
    guia_id: int | None = None,
) -> list[TourPublic]:
    """Consulta el listado de tours disponibles o filtrados por guía."""
    return await service.list_all(skip=skip, limit=limit, guia_id=guia_id)


@router.get("/{tour_id}", response_model=TourPublic)
async def get_tour(
    tour_id: int,
    service: Annotated[TourService, Depends(get_tour_service)],
) -> TourPublic:
    """Obtiene los detalles específicos de un tour."""
    return await service.get_by_id(tour_id)


@router.patch("/{tour_id}", response_model=TourPublic)
async def update_tour(
    tour_id: int,
    tour_in: TourUpdate,
    service: Annotated[TourService, Depends(get_tour_service)],
) -> TourPublic:
    """Actualiza la información de un tour."""
    return await service.update(tour_id, tour_in)


@router.delete("/{tour_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tour(
    tour_id: int,
    service: Annotated[TourService, Depends(get_tour_service)],
) -> None:
    """Elimina o desactiva un tour."""
    await service.delete(tour_id)
