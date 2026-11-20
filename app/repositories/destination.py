from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.destination import Destination, DestinationCreate, DestinationUpdate


class DestinationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, destination_in: DestinationCreate) -> Destination:
        db_destination = Destination.model_validate(destination_in)
        self.session.add(db_destination)
        await self.session.commit()
        await self.session.refresh(db_destination)
        return db_destination

    async def get_by_id(self, destination_id: int) -> Destination | None:
        result = await self.session.execute(
            select(Destination).where(Destination.id == destination_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[Destination]:
        result = await self.session.execute(
            select(Destination).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def update(
        self, db_destination: Destination, destination_in: DestinationUpdate
    ) -> Destination:
        destination_data = destination_in.model_dump(exclude_unset=True)
        for key, value in destination_data.items():
            setattr(db_destination, key, value)

        self.session.add(db_destination)
        await self.session.commit()
        await self.session.refresh(db_destination)
        return db_destination

    async def delete(self, db_destination: Destination) -> None:
        await self.session.delete(db_destination)
        await self.session.commit()