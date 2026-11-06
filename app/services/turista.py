from fastapi import HTTPException, status
from app.models.Turista import Turista, TuristaCreate, TuristaUpdate
from app.repositories.turista import TuristaRepository

class TuristaService:
    def _init_(self, turista_repo: TuristaRepository) -> None:
        self.turista_repo = turista_repo

    async def get_by_id(self, turista_id: int) -> Turista:
        turista = await self.turista_repo.get_by_id(turista_id)
        if not turista:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turista no encontrado.")
        return turista

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[Turista]:
        return await self.turista_repo.get_multi(skip=skip, limit=limit)

    async def create(self, turista_in: TuristaCreate) -> Turista:
        existing = await self.turista_repo.get_by_email(turista_in.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo ya está registrado.")
        return await self.turista_repo.create(turista_in)

    async def update(self, turista_id: int, turista_in: TuristaUpdate) -> Turista:
        turista = await self.get_by_id(turista_id)
        return await self.turista_repo.update(turista, turista_in)

    async def delete(self, turista_id: int) -> None:
        turista = await self.get_by_id(turista_id)
        await self.turista_repo.delete(turista)