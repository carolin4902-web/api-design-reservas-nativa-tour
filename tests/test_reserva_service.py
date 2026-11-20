import unittest
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.unit_of_work import UnitOfWork
from app.models.Guia import GuiaCreate
from app.models.Reserva import ReservaCreate, ReservaUpdate
from app.models.Tour import TourCreate, TourPublic, TourUpdate
from app.models.Turista import TuristaCreate
from app.repositories.guia import GuiaRepository
from app.repositories.reserva import ReservaRepository
from app.repositories.tour import TourRepository
from app.repositories.turista import TuristaRepository
from app.services.reserva import ReservaService


class FailingTourRepository(TourRepository):
    async def update(
        self,
        tour_id: int,
        tour_in: TourUpdate,
        *,
        cupos_disponibles: int | None = None,
    ) -> TourPublic | None:
        await super().update(
            tour_id,
            tour_in,
            cupos_disponibles=cupos_disponibles,
        )
        raise RuntimeError("abort reservation transaction")


class ReservaServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(SQLModel.metadata.create_all)
        self.session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def _seed_reservation_dependencies(
        self, session: AsyncSession
    ) -> tuple[int, int]:
        unit_of_work = UnitOfWork(session)
        guia_repo = GuiaRepository(session)
        turista_repo = TuristaRepository(session)
        tour_repo = TourRepository(session)

        async with unit_of_work.transaction():
            guia = await guia_repo.create(
                GuiaCreate(
                    nombre="Ana",
                    apellido="Guía",
                    correo="ana@example.com",
                    telefono="3001234567",
                    especialidad="Naturaleza",
                )
            )
            turista = await turista_repo.create(
                TuristaCreate(
                    nombre="Luis",
                    apellido="Turista",
                    correo="luis@example.com",
                    telefono="3007654321",
                )
            )
            tour = await tour_repo.create(
                TourCreate(
                    nombre="Caminata",
                    descripcion="Ruta de prueba",
                    ubicacion="Amazonas",
                    precio=100,
                    capacidad=5,
                    id_guia=guia.id_guia,
                )
            )

        return turista.id_turista, tour.id_tour

    def _service(
        self,
        session: AsyncSession,
        tour_repo: TourRepository | None = None,
    ) -> ReservaService:
        return ReservaService(
            reserva_repo=ReservaRepository(session),
            turista_repo=TuristaRepository(session),
            tour_repo=tour_repo or TourRepository(session),
            unit_of_work=UnitOfWork(session),
        )

    def _reservation_input(self, turista_id: int, tour_id: int) -> ReservaCreate:
        return ReservaCreate(
            fecha_reserva=date(2027, 1, 15),
            cantidad_personas=2,
            precio_total=Decimal(200),
            estado="confirmada",
            id_turista=turista_id,
            id_tour=tour_id,
        )

    async def test_create_reservation_and_decrement_availability_atomically(
        self,
    ) -> None:
        async with self.session_maker() as session:
            turista_id, tour_id = await self._seed_reservation_dependencies(session)
            service = self._service(session)

            reserva = await service.create(self._reservation_input(turista_id, tour_id))

            tour = await TourRepository(session).get_by_id(tour_id)
            self.assertEqual(reserva.id_tour, tour_id)
            self.assertIsNotNone(tour)
            self.assertEqual(tour.cupos_disponibles, 3)

    async def test_update_reservation_adjusts_tour_availability(self) -> None:
        async with self.session_maker() as session:
            turista_id, tour_id = await self._seed_reservation_dependencies(session)
            service = self._service(session)
            reserva = await service.create(self._reservation_input(turista_id, tour_id))

            updated_reserva = await service.update(
                reserva.id_reserva,
                ReservaUpdate(cantidad_personas=3),
            )

            tour = await TourRepository(session).get_by_id(tour_id)
            self.assertEqual(updated_reserva.cantidad_personas, 3)
            self.assertIsNotNone(tour)
            self.assertEqual(tour.cupos_disponibles, 2)

    async def test_move_reservation_transfers_available_spots_between_tours(
        self,
    ) -> None:
        async with self.session_maker() as session:
            turista_id, old_tour_id = await self._seed_reservation_dependencies(session)
            tour_repo = TourRepository(session)

            async with UnitOfWork(session).transaction():
                old_tour = await tour_repo.get_by_id(old_tour_id)
                self.assertIsNotNone(old_tour)
                new_tour = await tour_repo.create(
                    TourCreate(
                        nombre="Avistamiento",
                        descripcion="Segundo destino de prueba",
                        ubicacion="Amazonas",
                        precio=150,
                        capacidad=5,
                        id_guia=old_tour.id_guia,
                    )
                )

            service = self._service(session)
            reserva = await service.create(
                self._reservation_input(turista_id, old_tour_id)
            )
            updated_reserva = await service.update(
                reserva.id_reserva,
                ReservaUpdate(id_tour=new_tour.id_tour),
            )

            old_tour_after = await TourRepository(session).get_by_id(old_tour_id)
            new_tour_after = await TourRepository(session).get_by_id(new_tour.id_tour)
            self.assertEqual(updated_reserva.id_tour, new_tour.id_tour)
            self.assertIsNotNone(old_tour_after)
            self.assertIsNotNone(new_tour_after)
            self.assertEqual(old_tour_after.cupos_disponibles, 5)
            self.assertEqual(new_tour_after.cupos_disponibles, 3)

    async def test_delete_reservation_restores_tour_availability(self) -> None:
        async with self.session_maker() as session:
            turista_id, tour_id = await self._seed_reservation_dependencies(session)
            service = self._service(session)
            reserva = await service.create(self._reservation_input(turista_id, tour_id))

            await service.delete(reserva.id_reserva)

            tour = await TourRepository(session).get_by_id(tour_id)
            reservations = await ReservaRepository(session).get_multi()
            self.assertIsNotNone(tour)
            self.assertEqual(tour.cupos_disponibles, 5)
            self.assertEqual(reservations, [])

    async def test_failure_after_flush_rolls_back_reservation_and_availability(
        self,
    ) -> None:
        async with self.session_maker() as session:
            turista_id, tour_id = await self._seed_reservation_dependencies(session)
            failing_tour_repo = FailingTourRepository(session)
            service = self._service(session, failing_tour_repo)

            with self.assertRaisesRegex(RuntimeError, "abort reservation transaction"):
                await service.create(self._reservation_input(turista_id, tour_id))

            reservations = await ReservaRepository(session).get_multi()
            tour = await TourRepository(session).get_by_id(tour_id)
            self.assertEqual(reservations, [])
            self.assertIsNotNone(tour)
            self.assertEqual(tour.cupos_disponibles, 5)


if __name__ == "__main__":
    unittest.main()
