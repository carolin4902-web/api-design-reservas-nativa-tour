from fastapi import HTTPException, status
from app.models.Reserva import Reserva, ReservaCreate, ReservaUpdate
from app.repositories.reserva import ReservaRepository
from app.repositories.turista import TuristaRepository
from app.repositories.tour import TourRepository

class ReservaService:
    def __init__(
        self,
        reserva_repo: ReservaRepository,
        turista_repo: TuristaRepository,
        tour_repo: TourRepository,
    ) -> None:
        self.reserva_repo = reserva_repo
        self.turista_repo = turista_repo
        self.tour_repo = tour_repo

    async def get_by_id(self, reserva_id: int) -> Reserva:
        reserva = await self.reserva_repo.get_by_id(reserva_id)
        if not reserva:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La reserva solicitada no existe."
            )
        return reserva

    async def list_all(self, skip: int = 0, limit: int = 100, turista_id: int | None = None) -> list[Reserva]:
        return await self.reserva_repo.get_multi(skip=skip, limit=limit, turista_id=turista_id)

    async def create(self, reserva_in: ReservaCreate) -> Reserva:
        # Regla de Negocio 1: Validar que el turista exista
        turista = await self.turista_repo.get_by_id(reserva_in.turista_id)
        if not turista or not turista.activo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El turista no se encuentra registrado o está inactivo."
            )

        # Regla de Negocio 2: Validar que el tour exista y tenga cupos suficientes
        tour = await self.tour_repo.get_by_id(reserva_in.tour_id)
        if not tour or not tour.activo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El tour seleccionado no está disponible."
            )
        
        if tour.cupos_disponibles < reserva_in.cantidad_personas:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cupos insuficientes. Solo quedan {tour.cupos_disponibles} cupos disponibles."
            )

        # Crear la reserva
        nueva_reserva = await self.reserva_repo.create(reserva_in)
        
        # Actualizar cupos del tour restando los reservados
        tour.cupos_disponibles -= reserva_in.cantidad_personas
        await self.tour_repo.session.commit()

        return nueva_reserva

    async def update(self, reserva_id: int, reserva_in: ReservaUpdate) -> Reserva:
        reserva = await self.get_by_id(reserva_id)
        return await self.reserva_repo.update(reserva, reserva_in)

    async def delete(self, reserva_id: int) -> None:
        reserva = await self.get_by_id(reserva_id)
        await self.reserva_repo.delete(reserva)