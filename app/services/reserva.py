import asyncio
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.unit_of_work import UnitOfWork
from app.models.Reserva import ReservaCreate, ReservaPublic, ReservaUpdate
from app.models.Tour import TourPublic
from app.models.Turista import TuristaPublic
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
        read_session_maker: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self.reserva_repo = reserva_repo
        self.turista_repo = turista_repo
        self.tour_repo = tour_repo
        self.unit_of_work = unit_of_work
        self.read_session_maker = read_session_maker

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
        if reserva_in.fecha_reserva < date.today():
            raise BusinessRuleError("La fecha de reserva no puede estar en el pasado.")

        turista, tour = await self._fetch_turista_and_tour(
            reserva_in.id_turista,
            reserva_in.id_tour,
        )
        if turista is None or not turista.activo:
            raise BusinessRuleError(
                "El turista no se encuentra registrado o está inactivo."
            )
        if tour is None or not tour.activo:
            raise NotFoundError("El tour seleccionado no está disponible.")

        async with self.unit_of_work.transaction():
            if reserva_in.estado != "cancelada":
                await self._reserve_spots_or_raise(
                    tour.id_tour,
                    reserva_in.cantidad_personas,
                )

            precio_total = self._calculate_total_price(
                tour.precio,
                reserva_in.cantidad_personas,
            )
            return await self.reserva_repo.create(
                reserva_in,
                precio_total=precio_total,
            )

    async def update(self, reserva_id: int, reserva_in: ReservaUpdate) -> ReservaPublic:
        async with self.unit_of_work.transaction():
            reserva = await self.get_by_id(reserva_id)

            new_turista_id = (
                reserva_in.id_turista
                if "id_turista" in reserva_in.model_fields_set
                else reserva.id_turista
            )
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
            new_estado = (
                reserva_in.estado
                if "estado" in reserva_in.model_fields_set
                else reserva.estado
            )
            new_fecha = (
                reserva_in.fecha_reserva
                if "fecha_reserva" in reserva_in.model_fields_set
                else reserva.fecha_reserva
            )

            if (
                new_turista_id is None
                or new_tour_id is None
                or new_quantity is None
                or new_estado is None
                or new_fecha is None
            ):
                raise BusinessRuleError(
                    "Los datos obligatorios de la reserva no pueden quedar vacíos."
                )

            if "fecha_reserva" in reserva_in.model_fields_set and new_fecha < date.today():
                raise BusinessRuleError("La fecha de reserva no puede estar en el pasado.")

            if new_turista_id != reserva.id_turista:
                turista = await self.turista_repo.get_by_id(new_turista_id)
                if turista is None or not turista.activo:
                    raise BusinessRuleError(
                        "El turista no se encuentra registrado o está inactivo."
                    )

            target_tour = await self.tour_repo.get_by_id(new_tour_id)
            if target_tour is None or (
                not target_tour.activo and new_estado != "cancelada"
            ):
                raise NotFoundError("El tour seleccionado no está disponible.")

            was_active = reserva.estado != "cancelada"
            will_be_active = new_estado != "cancelada"

            if was_active and not will_be_active:
                await self.tour_repo.release_spots(
                    reserva.id_tour,
                    reserva.cantidad_personas,
                )
            elif not was_active and will_be_active:
                await self._reserve_spots_or_raise(new_tour_id, new_quantity)
            elif was_active and will_be_active:
                if new_tour_id == reserva.id_tour:
                    quantity_diff = new_quantity - reserva.cantidad_personas
                    if quantity_diff > 0:
                        await self._reserve_spots_or_raise(new_tour_id, quantity_diff)
                    elif quantity_diff < 0:
                        await self.tour_repo.release_spots(new_tour_id, -quantity_diff)
                else:
                    await self._reserve_spots_or_raise(new_tour_id, new_quantity)
                    await self.tour_repo.release_spots(
                        reserva.id_tour,
                        reserva.cantidad_personas,
                    )

            precio_total: Decimal | None = None
            if (
                new_tour_id != reserva.id_tour
                or new_quantity != reserva.cantidad_personas
            ):
                precio_total = self._calculate_total_price(
                    target_tour.precio,
                    new_quantity,
                )

            reserva_actualizada = await self.reserva_repo.update(
                reserva_id,
                reserva_in,
                precio_total=precio_total,
            )
            if reserva_actualizada is None:
                raise NotFoundError("La reserva solicitada no existe.")
            return reserva_actualizada

    async def delete(self, reserva_id: int) -> None:
        async with self.unit_of_work.transaction():
            reserva = await self.get_by_id(reserva_id)
            if reserva.estado != "cancelada":
                await self.tour_repo.release_spots(
                    reserva.id_tour,
                    reserva.cantidad_personas,
                )
            deleted = await self.reserva_repo.delete(reserva_id)
            if not deleted:
                raise NotFoundError("La reserva solicitada no existe.")

    async def _fetch_turista_and_tour(
        self, turista_id: int, tour_id: int
    ) -> tuple[TuristaPublic | None, TourPublic | None]:
        """Consulta turista y tour en paralelo usando sesiones de lectura aisladas."""
        if self.read_session_maker is None:
            turista = await self.turista_repo.get_by_id(turista_id)
            tour = await self.tour_repo.get_by_id(tour_id)
            return turista, tour

        async def _get_turista() -> TuristaPublic | None:
            async with self.read_session_maker() as session:
                return await TuristaRepository(session).get_by_id(turista_id)

        async def _get_tour() -> TourPublic | None:
            async with self.read_session_maker() as session:
                return await TourRepository(session).get_by_id(tour_id)

        turista, tour = await asyncio.gather(_get_turista(), _get_tour())
        return turista, tour

    async def _reserve_spots_or_raise(self, tour_id: int, quantity: int) -> TourPublic:
        updated_tour = await self.tour_repo.reserve_spots(tour_id, quantity)
        if updated_tour is not None:
            return updated_tour

        tour = await self.tour_repo.get_by_id(tour_id)
        if tour is None or not tour.activo:
            raise NotFoundError("El tour seleccionado no está disponible.")
        raise BusinessRuleError(
            f"Cupos insuficientes. Solo quedan {tour.cupos_disponibles} cupos disponibles."
        )

    @staticmethod
    def _calculate_total_price(unit_price: float, quantity: int) -> Decimal:
        return (Decimal(str(unit_price)) * Decimal(quantity)).quantize(Decimal("0.01"))
