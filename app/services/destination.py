from fastapi import HTTPException, status
from app.models.destination import Destination, DestinationCreate, DestinationUpdate
from app.repositories.destination import DestinationRepository


class DestinationService:
    def __init__(self, destination_repo: DestinationRepository) -> None:
        self.destination_repo = destination_repo

    async def get_by_id(self, destination_id: int) -> Destination:
        destination = await self.destination_repo.get_by_id(destination_id)
        if not destination:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Destino no encontrado.",
            )
        return destination

    async def list_all(self, skip: int = 0, limit: int = 100):
        return await self.destination_repo.list_all(skip=skip, limit=limit)

    async def create(self, destination_in: DestinationCreate) -> Destination:
        return await self.destination_repo.create(destination_in)

    async def update(
        self,
        destination_id: int,
        destination_in: DestinationUpdate,
    ) -> Destination:
        destination = await self.get_by_id(destination_id)
        return await self.destination_repo.update(destination, destination_in)

    async def delete(self, destination_id: int) -> None:
        destination = await self.get_by_id(destination_id)
        await self.destination_repo.delete(destination)