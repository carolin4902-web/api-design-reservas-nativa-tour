from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.Turista import Turista, TuristaCreate, TuristaUpdate

class TuristaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, turista_id: int) -> Turista | None:
        return await self.session.get(Turista, turista_id)

    async def get_by_email(self, email: str) -> Turista | None:
        statement = select(Turista).where(Turista.correo == email)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_multi(self, *, skip: int = 0, limit: int = 100) -> list[Turista]:
        statement = select(Turista).offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def create(self, turista_in: TuristaCreate) -> Turista:
        db_turista = Turista.model_validate(turista_in)
        self.session.add(db_turista)
        await self.session.commit()
        await self.session.refresh(db_turista)
        return db_turista

    async def update(self, db_turista: Turista, turista_in: TuristaUpdate) -> Turista:
        update_data: dict[str, Any] = turista_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_turista, field, value)
        self.session.add(db_turista)
        await self.session.commit()
        await self.session.refresh(db_turista)
        return db_turista

    async def delete(self, db_turista: Turista) -> None:
        await self.session.delete(db_turista)
        await self.session.commit()