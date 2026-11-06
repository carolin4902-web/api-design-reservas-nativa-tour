from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.Reserva import Reserva, ReservaCreate, ReservaUpdate

class ReservaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, reserva_id: int) -> Reserva | None:
        return await self.session.get(Reserva, reserva_id)

    async def get_multi(self, *, skip: int = 0, limit: int = 100, turista_id: int | None = None) -> list[Reserva]:
        statement = select(Reserva)
        if turista_id is not None:
            statement = statement.where(Reserva.id_turista == turista_id)
        statement = statement.offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def create(self, reserva_in: ReservaCreate) -> Reserva:
        db_reserva = Reserva.model_validate(reserva_in)
        self.session.add(db_reserva)
        await self.session.commit()
        await self.session.refresh(db_reserva)
        return db_reserva

    async def update(self, db_reserva: Reserva, reserva_in: ReservaUpdate) -> Reserva:
        update_data: dict[str, Any] = reserva_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_reserva, field, value)
        self.session.add(db_reserva)
        await self.session.commit()
        await self.session.refresh(db_reserva)
        return db_reserva

    async def delete(self, db_reserva: Reserva) -> None:
        await self.session.delete(db_reserva)
        await self.session.commit()