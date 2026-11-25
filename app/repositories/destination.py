from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.exceptions import ConflictError
from app.models.destination import (
    Destination,
    DestinationCreate,
    DestinationPublic,
    DestinationUpdate,
)


class DestinationRepository:
    """Repositorio asíncrono para gestionar destinos."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, destination_in: DestinationCreate) -> DestinationPublic:
        """Crea un nuevo destino en la base de datos."""
        db_destination = Destination.model_validate(destination_in)
        self.session.add(db_destination)
        try:
            await self.session.flush()
        except IntegrityError as exc:
            raise ConflictError("Ya existe un destino con ese nombre.") from exc
        await self.session.refresh(db_destination)
        return DestinationPublic.model_validate(db_destination)

    async def get_by_id(self, destination_id: int) -> DestinationPublic | None:
        """Obtiene un destino por su ID."""
        result = await self.session.execute(
            select(Destination).where(Destination.id == destination_id)
        )
        destination = result.scalar_one_or_none()
        if destination is None:
            return None
        return DestinationPublic.model_validate(destination)

    async def get_by_name(self, name: str) -> DestinationPublic | None:
        """Obtiene un destino por su nombre único."""
        result = await self.session.execute(
            select(Destination).where(Destination.name == name)
        )
        destination = result.scalar_one_or_none()
        if destination is None:
            return None
        return DestinationPublic.model_validate(destination)

    async def list_all(
        self, skip: int = 0, limit: int = 100
    ) -> Sequence[DestinationPublic]:
        """Lista destinos con soporte de paginación."""
        result = await self.session.execute(
            select(Destination).offset(skip).limit(limit)
        )
        return [
            DestinationPublic.model_validate(destination)
            for destination in result.scalars().all()
        ]

    async def update(
        self, destination_id: int, destination_in: DestinationUpdate
    ) -> DestinationPublic | None:
        """Actualiza parcialmente un destino existente."""
        db_destination = await self.session.get(Destination, destination_id)
        if db_destination is None:
            return None

        destination_data = destination_in.model_dump(exclude_unset=True)
        for key, value in destination_data.items():
            setattr(db_destination, key, value)

        self.session.add(db_destination)
        try:
            await self.session.flush()
        except IntegrityError as exc:
            raise ConflictError("Ya existe un destino con ese nombre.") from exc
        await self.session.refresh(db_destination)
        return DestinationPublic.model_validate(db_destination)

    async def delete(self, destination_id: int) -> bool:
        """Elimina un destino por su ID y retorna True si existía."""
        db_destination = await self.session.get(Destination, destination_id)
        if db_destination is None:
            return False

        await self.session.delete(db_destination)
        await self.session.flush()
        return True
