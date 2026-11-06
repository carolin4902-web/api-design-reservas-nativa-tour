from fastapi import HTTPException, status
from app.models.Guia import Guia, GuiaCreate, GuiaUpdate
from app.repositories.guia import GuiaRepository

class GuiaService:
    def _init_(self, guia_repo: GuiaRepository) -> None:
        self.guia_repo = guia_repo

    async def get_by_id(self, guia_id: int) -> Guia:
        guia = await self.guia_repo.get_by_id(guia_id)
        if not guia:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guía no encontrado.")
        return guia

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[Guia]:
        return await self.guia_repo.get_multi(skip=skip, limit=limit)

    async def create(self, guia_in: GuiaCreate) -> Guia:
        existing = await self.guia_repo.get_by_email(guia_in.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo del guía ya existe.")
        return await self.guia_repo.create(guia_in)

    async def update(self, guia_id: int, guia_in: GuiaUpdate) -> Guia:
        guia = await self.get_by_id(guia_id)
        return await self.guia_repo.update(guia, guia_in)

    async def delete(self, guia_id: int) -> None:
        guia = await self.get_by_id(guia_id)
        await self.guia_repo.delete(guia)