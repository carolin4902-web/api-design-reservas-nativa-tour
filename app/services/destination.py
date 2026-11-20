from app.core.exceptions import NotFoundError
from app.core.unit_of_work import UnitOfWork
from app.models.destination import (
    DestinationCreate,
    DestinationPublic,
    DestinationUpdate,
)
from app.repositories.destination import DestinationRepository


class DestinationService:
    def __init__(
        self,
        destination_repo: DestinationRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self.destination_repo = destination_repo
        self.unit_of_work = unit_of_work

    async def create(self, destination_in: DestinationCreate) -> DestinationPublic:
        async with self.unit_of_work.transaction():
            return await self.destination_repo.create(destination_in)

    async def list_all(
        self, skip: int = 0, limit: int = 100
    ) -> list[DestinationPublic]:
        return list(await self.destination_repo.list_all(skip=skip, limit=limit))

    async def get_by_id(self, destination_id: int) -> DestinationPublic:
        destination = await self.destination_repo.get_by_id(destination_id)
        if destination is None:
            raise NotFoundError("Destino no encontrado.")
        return destination

    async def update(
        self,
        destination_id: int,
        destination_in: DestinationUpdate,
    ) -> DestinationPublic:
        async with self.unit_of_work.transaction():
            destination = await self.destination_repo.update(
                destination_id, destination_in
            )
            if destination is None:
                raise NotFoundError("Destino no encontrado.")
            return destination

    async def delete(self, destination_id: int) -> None:
        async with self.unit_of_work.transaction():
            deleted = await self.destination_repo.delete(destination_id)
            if not deleted:
                raise NotFoundError("Destino no encontrado.")
