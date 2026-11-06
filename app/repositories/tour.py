from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.Tour import Tour, TourCreate, TourUpdate

class TourRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, tour_id: int) -> Tour | None:
        return await self.session.get(Tour, tour_id)

    async def get_multi(self, *, skip: int = 0, limit: int = 100, guia_id: int | None = None) -> list[Tour]:
        statement = select(Tour)
        if guia_id is not None:
            statement = statement.where(Tour.id_guia == guia_id)
        statement = statement.offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def create(self, tour_in: TourCreate) -> Tour:
        db_tour = Tour.model_validate(tour_in)
        self.session.add(db_tour)
        await self.session.commit()
        await self.session.refresh(db_tour)
        return db_tour

    async def update(self, db_tour: Tour, tour_in: TourUpdate) -> Tour:
        update_data: dict[str, Any] = tour_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_tour, field, value)
        self.session.add(db_tour)
        await self.session.commit()
        await self.session.refresh(db_tour)
        return db_tour

    async def delete(self, db_tour: Tour) -> None:
        await self.session.delete(db_tour)
        await self.session.commit()