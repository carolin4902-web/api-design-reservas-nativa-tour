from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.exceptions import ConflictError
from app.models.Reserva import Reserva
from app.models.Turista import (
    Turista,
    TuristaCreate,
    TuristaPublic,
    TuristaUpdate,
)


class TuristaRepository:
    """Repositorio asíncrono para gestionar turistas."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, turista_id: int) -> TuristaPublic | None:
        """Obtiene un turista por su ID."""
        turista = await self.session.get(Turista, turista_id)
        if turista is None:
            return None
        return TuristaPublic.model_validate(turista)

    async def get_by_email(self, email: str) -> TuristaPublic | None:
        """Busca un turista por correo electrónico único."""
        statement = select(Turista).where(Turista.correo == email)
        result = await self.session.execute(statement)
        turista = result.scalar_one_or_none()
        if turista is None:
            return None
        return TuristaPublic.model_validate(turista)

    async def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> list[TuristaPublic]:
        """Lista turistas con paginación."""
        statement = select(Turista).offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return [
            TuristaPublic.model_validate(turista) for turista in result.scalars().all()
        ]

    async def create(self, turista_in: TuristaCreate) -> TuristaPublic:
        """Registra un nuevo turista y maneja conflictos de unicidad."""
        db_turista = Turista.model_validate(turista_in)
        self.session.add(db_turista)
        try:
            await self.session.flush()
        except IntegrityError as exc:
            raise ConflictError("El correo del turista ya está registrado.") from exc
        await self.session.refresh(db_turista)
        return TuristaPublic.model_validate(db_turista)

    async def update(
        self, turista_id: int, turista_in: TuristaUpdate
    ) -> TuristaPublic | None:
        """Actualiza parcialmente un turista existente."""
        db_turista = await self.session.get(Turista, turista_id)
        if db_turista is None:
            return None

        update_data: dict[str, Any] = turista_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_turista, field, value)
        db_turista.updated_at = datetime.now(timezone.utc)
        self.session.add(db_turista)
        try:
            await self.session.flush()
        except IntegrityError as exc:
            raise ConflictError("El correo del turista ya está registrado.") from exc
        await self.session.refresh(db_turista)
        return TuristaPublic.model_validate(db_turista)

    async def has_reservas(self, turista_id: int) -> bool:
        """Verifica si el turista tiene reservas asociadas."""
        statement = (
            select(Reserva.id_reserva).where(Reserva.id_turista == turista_id).limit(1)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def delete(self, turista_id: int) -> bool:
        """Elimina un turista por ID y retorna True si existía."""
        db_turista = await self.session.get(Turista, turista_id)
        if db_turista is None:
            return False

        await self.session.delete(db_turista)
        await self.session.flush()
        return True
