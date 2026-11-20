from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.Tour import Tour, TourCreate, TourPublic, TourUpdate


class TourRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, tour_id: int) -> TourPublic | None:
        tour = await self.session.get(Tour, tour_id)
        if tour is None:
            return None
        return TourPublic.model_validate(tour)

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        guia_id: int | None = None,
    ) -> list[TourPublic]:
        statement = select(Tour)
        if guia_id is not None:
            statement = statement.where(Tour.id_guia == guia_id)
        statement = statement.offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return [TourPublic.model_validate(tour) for tour in result.scalars().all()]

    async def create(self, tour_in: TourCreate) -> TourPublic:
        db_tour = Tour.model_validate(tour_in)
        db_tour.cupos_disponibles = db_tour.capacidad
        self.session.add(db_tour)
        await self.session.flush()
        await self.session.refresh(db_tour)
        return TourPublic.model_validate(db_tour)

    async def update(
        self,
        tour_id: int,
        tour_in: TourUpdate,
        *,
        cupos_disponibles: int | None = None,
    ) -> TourPublic | None:
        db_tour = await self.session.get(Tour, tour_id)
        if db_tour is None:
            return None

        update_data: dict[str, Any] = tour_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_tour, field, value)
        if cupos_disponibles is not None:
            db_tour.cupos_disponibles = cupos_disponibles
        self.session.add(db_tour)
        await self.session.flush()
        await self.session.refresh(db_tour)
        return TourPublic.model_validate(db_tour)

    async def delete(self, tour_id: int) -> bool:
        db_tour = await self.session.get(Tour, tour_id)
        if db_tour is None:
            return False

        await self.session.delete(db_tour)
        await self.session.flush()
        return True
