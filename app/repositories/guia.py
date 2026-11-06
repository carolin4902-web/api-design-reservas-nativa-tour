from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.Guia import Guia, GuiaCreate, GuiaUpdate

class GuiaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, guia_id: int) -> Guia | None:
        return await self.session.get(Guia, guia_id)

    async def get_by_email(self, email: str) -> Guia | None:
        statement = select(Guia).where(Guia.email == email)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_multi(self, *, skip: int = 0, limit: int = 100) -> list[Guia]:
        statement = select(Guia).offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def create(self, guia_in: GuiaCreate) -> Guia:
        db_guia = Guia.model_validate(guia_in)
        self.session.add(db_guia)
        await self.session.commit()
        await self.session.refresh(db_guia)
        return db_guia

    async def update(self, db_guia: Guia, guia_in: GuiaUpdate) -> Guia:
        update_data: dict[str, Any] = guia_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_guia, field, value)
        self.session.add(db_guia)
        await self.session.commit()
        await self.session.refresh(db_guia)
        return db_guia

    async def delete(self, db_guia: Guia) -> None:
        await self.session.delete(db_guia)
        await self.session.commit()