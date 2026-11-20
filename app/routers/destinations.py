from fastapi import APIRouter, status
from app.api.deps import DestinationServiceDep
from app.models.destination import DestinationCreate, DestinationPublic, DestinationUpdate

router = APIRouter(prefix="/destinations", tags=["Destinations"])

@router.post("/", response_model=DestinationPublic, status_code=status.HTTP_201_CREATED)
async def create_destination(
    destination_in: DestinationCreate,
    service: DestinationServiceDep,
) -> DestinationPublic:
    return await service.create(destination_in)

@router.get("/", response_model=list[DestinationPublic])
async def list_destinations(
    service: DestinationServiceDep,
    skip: int = 0,
    limit: int = 100,
) -> list[DestinationPublic]:
    return await service.list_all(skip=skip, limit=limit)

@router.get("/{destination_id}", response_model=DestinationPublic)
async def get_destination(
    destination_id: int,
    service: DestinationServiceDep,
) -> DestinationPublic:
    return await service.get_by_id(destination_id)

@router.patch("/{destination_id}", response_model=DestinationPublic)
async def update_destination(
    destination_id: int,
    destination_in: DestinationUpdate,
    service: DestinationServiceDep,
) -> DestinationPublic:
    return await service.update(destination_id, destination_in)

@router.delete("/{destination_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_destination(
    destination_id: int,
    service: DestinationServiceDep,
) -> None:
    await service.delete(destination_id)