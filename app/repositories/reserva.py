from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.Reserva import Reserva, ReservaCreate, ReservaPublic, ReservaUpdate


class ReservaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, reserva_id: int) -> ReservaPublic | None:
        reserva = await self.session.get(Reserva, reserva_id)
        if reserva is None:
            return None
        return ReservaPublic.model_validate(reserva)

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        turista_id: int | None = None,
    ) -> list[ReservaPublic]:
        statement = select(Reserva)
        if turista_id is not None:
            statement = statement.where(Reserva.id_turista == turista_id)
        statement = statement.offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return [
            ReservaPublic.model_validate(reserva) for reserva in result.scalars().all()
        ]

    async def create(self, reserva_in: ReservaCreate) -> ReservaPublic:
        db_reserva = Reserva.model_validate(reserva_in)
        self.session.add(db_reserva)
        await self.session.flush()
        await self.session.refresh(db_reserva)
        return ReservaPublic.model_validate(db_reserva)

    async def update(
        self, reserva_id: int, reserva_in: ReservaUpdate
    ) -> ReservaPublic | None:
        db_reserva = await self.session.get(Reserva, reserva_id)
        if db_reserva is None:
            return None

        update_data: dict[str, Any] = reserva_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_reserva, field, value)
        self.session.add(db_reserva)
        await self.session.flush()
        await self.session.refresh(db_reserva)
        return ReservaPublic.model_validate(db_reserva)

    async def delete(self, reserva_id: int) -> bool:
        db_reserva = await self.session.get(Reserva, reserva_id)
        if db_reserva is None:
            return False

        await self.session.delete(db_reserva)
        await self.session.flush()
        return True
