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

        nueva_reserva = Reserva.model_validate(reserva_in)
        self.reserva_repo.session.add(nueva_reserva)
        tour.cupos_disponibles -= reserva_in.cantidad_personas
        self.tour_repo.session.add(tour)
        await self.reserva_repo.session.commit()
        await self.reserva_repo.session.refresh(nueva_reserva)

        return nueva_reserva

    async def update(self, reserva_id: int, reserva_in: ReservaUpdate) -> Reserva:
        reserva = await self.get_by_id(reserva_id)
        update_data = reserva_in.model_dump(exclude_unset=True)
        old_tour = await self.tour_repo.get_by_id(reserva.id_tour)
        if not old_tour:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El tour asociado no existe.")

        new_tour_id = update_data.get("id_tour", reserva.id_tour)
        new_quantity = update_data.get("cantidad_personas", reserva.cantidad_personas)
        new_tour = old_tour if new_tour_id == reserva.id_tour else await self.tour_repo.get_by_id(new_tour_id)

        if not new_tour or not new_tour.activo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El tour seleccionado no está disponible.")

        if new_tour_id == reserva.id_tour:
            available = new_tour.cupos_disponibles + reserva.cantidad_personas
            if new_quantity > available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cupos insuficientes. Solo quedan {new_tour.cupos_disponibles} cupos disponibles.",
                )
            new_tour.cupos_disponibles = available - new_quantity
        else:
            old_tour.cupos_disponibles += reserva.cantidad_personas
            if new_tour.cupos_disponibles < new_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cupos insuficientes. Solo quedan {new_tour.cupos_disponibles} cupos disponibles.",
                )
            new_tour.cupos_disponibles -= new_quantity

        for field, value in update_data.items():
            setattr(reserva, field, value)

        self.reserva_repo.session.add(reserva)
        self.tour_repo.session.add(old_tour)
        if new_tour is not old_tour:
            self.tour_repo.session.add(new_tour)
        await self.reserva_repo.session.commit()
        await self.reserva_repo.session.refresh(reserva)
        return reserva

    async def delete(self, reserva_id: int) -> None:
        reserva = await self.get_by_id(reserva_id)
        tour = await self.tour_repo.get_by_id(reserva.id_tour)
        if tour:
            tour.cupos_disponibles = min(
                tour.capacidad,
                tour.cupos_disponibles + reserva.cantidad_personas,
            )
            self.tour_repo.session.add(tour)
        await self.reserva_repo.session.delete(reserva)
        await self.reserva_repo.session.commit()