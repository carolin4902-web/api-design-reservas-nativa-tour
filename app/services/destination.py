from app.core.exceptions import ConflictError, NotFoundError
from app.core.unit_of_work import UnitOfWork
from app.models.destination import (
    DestinationCreate,
    DestinationPublic,
    DestinationUpdate,
)
from app.repositories.destination import DestinationRepository


class DestinationService:
    """Servicio de lógica de negocio para la gestión de destinos."""

    def __init__(
        self,
        destination_repo: DestinationRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self.destination_repo = destination_repo
        self.unit_of_work = unit_of_work

    async def create(self, destination_in: DestinationCreate) -> DestinationPublic:
        """Crea un destino validando que su nombre no exista previamente."""
        async with self.unit_of_work.transaction():
            existing = await self.destination_repo.get_by_name(destination_in.name)
            if existing is not None:
                raise ConflictError("Ya existe un destino con ese nombre.")
            return await self.destination_repo.create(destination_in)

    async def list_all(
        self, skip: int = 0, limit: int = 100
    ) -> list[DestinationPublic]:
        """Retorna el listado paginado de destinos."""
        return list(await self.destination_repo.list_all(skip=skip, limit=limit))

    async def get_by_id(self, destination_id: int) -> DestinationPublic:
        """Obtiene un destino por su ID o lanza NotFoundError."""
        destination = await self.destination_repo.get_by_id(destination_id)
        if destination is None:
            raise NotFoundError("Destino no encontrado.")
        return destination

    async def update(
        self,
        destination_id: int,
        destination_in: DestinationUpdate,
    ) -> DestinationPublic:
        """Actualiza un destino validando unicidad de nombre si se modifica."""
        async with self.unit_of_work.transaction():
            if destination_in.name is not None:
                existing = await self.destination_repo.get_by_name(destination_in.name)
                if existing is not None and existing.id != destination_id:
                    raise ConflictError("Ya existe un destino con ese nombre.")
            destination = await self.destination_repo.update(
                destination_id, destination_in
            )
            if destination is None:
                raise NotFoundError("Destino no encontrado.")
            return destination

    async def delete(self, destination_id: int) -> None:
        """Elimina un destino por su ID."""
        async with self.unit_of_work.transaction():
            deleted = await self.destination_repo.delete(destination_id)
            if not deleted:
                raise NotFoundError("Destino no encontrado.")
