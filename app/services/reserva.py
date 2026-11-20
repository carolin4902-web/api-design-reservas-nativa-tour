from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.unit_of_work import UnitOfWork
from app.models.Reserva import ReservaCreate, ReservaPublic, ReservaUpdate
from app.models.Tour import TourUpdate
from app.repositories.reserva import ReservaRepository
from app.repositories.tour import TourRepository
from app.repositories.turista import TuristaRepository


class ReservaService:
    def __init__(
        self,
        reserva_repo: ReservaRepository,
        turista_repo: TuristaRepository,
        tour_repo: TourRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self.reserva_repo = reserva_repo
        self.turista_repo = turista_repo
        self.tour_repo = tour_repo
        self.unit_of_work = unit_of_work

    async def get_by_id(self, reserva_id: int) -> ReservaPublic:
        reserva = await self.reserva_repo.get_by_id(reserva_id)
        if reserva is None:
            raise NotFoundError("La reserva solicitada no existe.")
        return reserva

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        turista_id: int | None = None,
    ) -> list[ReservaPublic]:
        return await self.reserva_repo.get_multi(
            skip=skip, limit=limit, turista_id=turista_id
        )

    async def create(self, reserva_in: ReservaCreate) -> ReservaPublic:
        async with self.unit_of_work.transaction():
            turista = await self.turista_repo.get_by_id(reserva_in.id_turista)
            if turista is None or not turista.activo:
                raise BusinessRuleError(
                    "El turista no se encuentra registrado o está inactivo."
                )

            tour = await self.tour_repo.get_by_id(reserva_in.id_tour)
            if tour is None or not tour.activo:
                raise NotFoundError("El tour seleccionado no está disponible.")

            if tour.cupos_disponibles < reserva_in.cantidad_personas:
                raise BusinessRuleError(
                    f"Cupos insuficientes. Solo quedan "
                    f"{tour.cupos_disponibles} cupos disponibles."
                )

            reserva = await self.reserva_repo.create(reserva_in)
            await self._set_tour_availability(
                tour.id_tour,
                tour.cupos_disponibles - reserva_in.cantidad_personas,
            )
            return reserva

    async def update(self, reserva_id: int, reserva_in: ReservaUpdate) -> ReservaPublic:
        async with self.unit_of_work.transaction():
            reserva = await self.get_by_id(reserva_id)
            old_tour = await self.tour_repo.get_by_id(reserva.id_tour)
            if old_tour is None:
                raise NotFoundError("El tour asociado no existe.")

            new_tour_id = (
                reserva_in.id_tour
                if "id_tour" in reserva_in.model_fields_set
                else reserva.id_tour
            )
            new_quantity = (
                reserva_in.cantidad_personas
                if "cantidad_personas" in reserva_in.model_fields_set
                else reserva.cantidad_personas
            )
            if new_tour_id is None or new_quantity is None:
                raise BusinessRuleError(
                    "El tour y la cantidad de personas no pueden quedar vacíos."
                )

            new_tour = (
                old_tour
                if new_tour_id == reserva.id_tour
                else await self.tour_repo.get_by_id(new_tour_id)
            )
            if new_tour is None or not new_tour.activo:
                raise NotFoundError("El tour seleccionado no está disponible.")

            if new_tour_id == reserva.id_tour:
                available = new_tour.cupos_disponibles + reserva.cantidad_personas
                if new_quantity > available:
                    raise BusinessRuleError(
                        f"Cupos insuficientes. Solo quedan "
                        f"{new_tour.cupos_disponibles} cupos disponibles."
                    )
                await self._set_tour_availability(
                    new_tour_id,
                    available - new_quantity,
                )
            else:
                restored_spots = min(
                    old_tour.capacidad,
                    old_tour.cupos_disponibles + reserva.cantidad_personas,
                )
                if new_tour.cupos_disponibles < new_quantity:
                    raise BusinessRuleError(
                        f"Cupos insuficientes. Solo quedan "
                        f"{new_tour.cupos_disponibles} cupos disponibles."
                    )
                await self._set_tour_availability(
                    old_tour.id_tour,
                    restored_spots,
                )
                await self._set_tour_availability(
                    new_tour_id,
                    new_tour.cupos_disponibles - new_quantity,
                )

            reserva_actualizada = await self.reserva_repo.update(reserva_id, reserva_in)
            if reserva_actualizada is None:
                raise NotFoundError("La reserva solicitada no existe.")
            return reserva_actualizada

    async def delete(self, reserva_id: int) -> None:
        async with self.unit_of_work.transaction():
            reserva = await self.get_by_id(reserva_id)
            tour = await self.tour_repo.get_by_id(reserva.id_tour)
            if tour is not None:
                await self._set_tour_availability(
                    tour.id_tour,
                    min(
                        tour.capacidad,
                        tour.cupos_disponibles + reserva.cantidad_personas,
                    ),
                )
            deleted = await self.reserva_repo.delete(reserva_id)
            if not deleted:
                raise NotFoundError("La reserva solicitada no existe.")

    async def _set_tour_availability(
        self, tour_id: int, cupos_disponibles: int
    ) -> None:
        tour = await self.tour_repo.update(
            tour_id,
            TourUpdate(),
            cupos_disponibles=cupos_disponibles,
        )
        if tour is None:
            raise NotFoundError("El tour seleccionado no está disponible.")
