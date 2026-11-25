from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.Guia import Guia, GuiaCreate, GuiaPublic, GuiaUpdate
from app.models.Tour import Tour


class GuiaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, guia_id: int) -> GuiaPublic | None:
        guia = await self.session.get(Guia, guia_id)
        if guia is None:
            return None
        return GuiaPublic.model_validate(guia)

    async def get_by_email(self, email: str) -> GuiaPublic | None:
        statement = select(Guia).where(Guia.correo == email)
        result = await self.session.execute(statement)
        guia = result.scalar_one_or_none()
        if guia is None:
            return None
        return GuiaPublic.model_validate(guia)

    async def get_multi(self, *, skip: int = 0, limit: int = 100) -> list[GuiaPublic]:
        statement = select(Guia).offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return [GuiaPublic.model_validate(guia) for guia in result.scalars().all()]

    async def create(self, guia_in: GuiaCreate) -> GuiaPublic:
        db_guia = Guia.model_validate(guia_in)
        self.session.add(db_guia)
        await self.session.flush()
        await self.session.refresh(db_guia)
        return GuiaPublic.model_validate(db_guia)

    async def update(self, guia_id: int, guia_in: GuiaUpdate) -> GuiaPublic | None:
        db_guia = await self.session.get(Guia, guia_id)
        if db_guia is None:
            return None

        update_data: dict[str, Any] = guia_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_guia, field, value)
        self.session.add(db_guia)
        await self.session.flush()
        await self.session.refresh(db_guia)
        return GuiaPublic.model_validate(db_guia)

    async def has_tours(self, guia_id: int) -> bool:
        statement = select(Tour.id_tour).where(Tour.id_guia == guia_id).limit(1)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def delete(self, guia_id: int) -> bool:
        db_guia = await self.session.get(Guia, guia_id)
        if db_guia is None:
            return False

        await self.session.delete(db_guia)
        await self.session.flush()
        return True
