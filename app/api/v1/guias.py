# app/api/v1/guias.py
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_guia_service
from app.models.Guia import GuiaCreate, GuiaPublic, GuiaUpdate
from app.services.guia import GuiaService

router = APIRouter(prefix="/guias", tags=["guias"])


@router.post("", response_model=GuiaPublic, status_code=status.HTTP_201_CREATED)
async def create_guia(
    guia_in: GuiaCreate,
    service: Annotated[GuiaService, Depends(get_guia_service)],
) -> GuiaPublic:
    """Registra un nuevo guía en la plataforma."""
    return await service.create(guia_in)


@router.get("", response_model=list[GuiaPublic])
async def list_guias(
    service: Annotated[GuiaService, Depends(get_guia_service)],
    skip: int = 0,
    limit: int = 100,
) -> list[GuiaPublic]:
    """Obtiene la lista de guías turísticos."""
    return await service.list_all(skip=skip, limit=limit)


@router.get("/{guia_id}", response_model=GuiaPublic)
async def get_guia(
    guia_id: int,
    service: Annotated[GuiaService, Depends(get_guia_service)],
) -> GuiaPublic:
    """Obtiene la información detallada de un guía."""
    return await service.get_by_id(guia_id)


@router.patch("/{guia_id}", response_model=GuiaPublic)
async def update_guia(
    guia_id: int,
    guia_in: GuiaUpdate,
    service: Annotated[GuiaService, Depends(get_guia_service)],
) -> GuiaPublic:
    """Actualiza los datos o estado de verificación de un guía."""
    return await service.update(guia_id, guia_in)


@router.delete("/{guia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_guia(
    guia_id: int,
    service: Annotated[GuiaService, Depends(get_guia_service)],
) -> None:
    """Elimina un guía del sistema."""
    await service.delete(guia_id)
