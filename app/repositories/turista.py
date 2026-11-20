from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.Turista import (
    Turista,
    TuristaCreate,
    TuristaPublic,
    TuristaUpdate,
)


class TuristaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, turista_id: int) -> TuristaPublic | None:
        turista = await self.session.get(Turista, turista_id)
        if turista is None:
            return None
        return TuristaPublic.model_validate(turista)

    async def get_by_email(self, email: str) -> TuristaPublic | None:
        statement = select(Turista).where(Turista.correo == email)
        result = await self.session.execute(statement)
        turista = result.scalar_one_or_none()
        if turista is None:
            return None
        return TuristaPublic.model_validate(turista)

    async def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> list[TuristaPublic]:
        statement = select(Turista).offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return [
            TuristaPublic.model_validate(turista) for turista in result.scalars().all()
        ]

    async def create(self, turista_in: TuristaCreate) -> TuristaPublic:
        db_turista = Turista.model_validate(turista_in)
        self.session.add(db_turista)
        await self.session.flush()
        await self.session.refresh(db_turista)
        return TuristaPublic.model_validate(db_turista)

    async def update(
        self, turista_id: int, turista_in: TuristaUpdate
    ) -> TuristaPublic | None:
        db_turista = await self.session.get(Turista, turista_id)
        if db_turista is None:
            return None

        update_data: dict[str, Any] = turista_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_turista, field, value)
        self.session.add(db_turista)
        await self.session.flush()
        await self.session.refresh(db_turista)
        return TuristaPublic.model_validate(db_turista)

    async def delete(self, turista_id: int) -> bool:
        db_turista = await self.session.get(Turista, turista_id)
        if db_turista is None:
            return False

        await self.session.delete(db_turista)
        await self.session.flush()
        return True
