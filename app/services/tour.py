from fastapi import HTTPException, status
from app.models.Tour import Tour, TourCreate, TourUpdate
from app.repositories.tour import TourRepository
from app.repositories.guia import GuiaRepository

class TourService:
    def _init_(self, tour_repo: TourRepository, guia_repo: GuiaRepository) -> None:
        self.tour_repo = tour_repo
        self.guia_repo = guia_repo

    async def get_by_id(self, tour_id: int) -> Tour:
        tour = await self.tour_repo.get_by_id(tour_id)
        if not tour:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tour no encontrado.")
        return tour

    async def list_all(self, skip: int = 0, limit: int = 100, guia_id: int | None = None) -> list[Tour]:
        return await self.tour_repo.get_multi(skip=skip, limit=limit, guia_id=guia_id)

    async def create(self, tour_in: TourCreate) -> Tour:
        # Regla: Validar que el guía exista y esté verificado
        guia = await self.guia_repo.get_by_id(tour_in.guia_id)
        if not guia or not guia.verificado:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El guía asignado no existe o no está verificado.")
        return await self.tour_repo.create(tour_in)

    async def update(self, tour_id: int, tour_in: TourUpdate) -> Tour:
        tour = await self.get_by_id(tour_id)
        return await self.tour_repo.update(tour, tour_in)

    async def delete(self, tour_id: int) -> None:
        tour = await self.get_by_id(tour_id)
        await self.tour_repo.delete(tour)