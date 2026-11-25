from typing import Any

from sqlalchemy import case, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.Reserva import Reserva
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

    async def reserve_spots(self, tour_id: int, quantity: int) -> TourPublic | None:
        """Descuenta cupos de forma atómica en BD para evitar condiciones de carrera."""
        if quantity <= 0:
            return await self.get_by_id(tour_id)

        statement = (
            update(Tour)
            .where(
                Tour.id_tour == tour_id,
                Tour.activo.is_(True),
                Tour.cupos_disponibles >= quantity,
            )
            .values(cupos_disponibles=Tour.cupos_disponibles - quantity)
            .returning(Tour)
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(statement)
        db_tour = result.scalar_one_or_none()
        if db_tour is None:
            return None
        await self.session.flush()
        return TourPublic.model_validate(db_tour)

    async def release_spots(self, tour_id: int, quantity: int) -> TourPublic | None:
        """Libera cupos de forma atómica sin superar la capacidad máxima del tour."""
        if quantity <= 0:
            return await self.get_by_id(tour_id)

        restored_spots = case(
            (Tour.cupos_disponibles + quantity > Tour.capacidad, Tour.capacidad),
            else_=Tour.cupos_disponibles + quantity,
        )
        statement = (
            update(Tour)
            .where(Tour.id_tour == tour_id)
            .values(cupos_disponibles=restored_spots)
            .returning(Tour)
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(statement)
        db_tour = result.scalar_one_or_none()
        if db_tour is None:
            return None
        await self.session.flush()
        return TourPublic.model_validate(db_tour)

    async def has_reservas(self, tour_id: int) -> bool:
        statement = select(Reserva.id_reserva).where(Reserva.id_tour == tour_id).limit(1)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def delete(self, tour_id: int) -> bool:
        db_tour = await self.session.get(Tour, tour_id)
        if db_tour is None:
            return False

        await self.session.delete(db_tour)
        await self.session.flush()
        return True
