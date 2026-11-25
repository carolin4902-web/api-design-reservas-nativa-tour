import asyncio
import os
import tempfile
import unittest
from datetime import date
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.core.exceptions import BusinessRuleError
from app.core.unit_of_work import UnitOfWork
from app.models.Guia import GuiaCreate
from app.models.Reserva import ReservaCreate, ReservaUpdate
from app.models.Tour import TourCreate, TourPublic
from app.models.Turista import TuristaCreate
from app.repositories.guia import GuiaRepository
from app.repositories.reserva import ReservaRepository
from app.repositories.tour import TourRepository
from app.repositories.turista import TuristaRepository
from app.services.reserva import ReservaService


class FailingTourRepository(TourRepository):
    async def reserve_spots(self, tour_id: int, quantity: int) -> TourPublic | None:
        await super().reserve_spots(tour_id, quantity)
        raise RuntimeError("abort reservation transaction")


class ReservaServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
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
            read_session_maker=self.session_maker,
        )

    def _reservation_input(
        self,
        turista_id: int,
        tour_id: int,
        cantidad_personas: int = 2,
    ) -> ReservaCreate:
        return ReservaCreate(
            fecha_reserva=date(2027, 1, 15),
            cantidad_personas=cantidad_personas,
            precio_total=Decimal(100 * cantidad_personas),
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
            self.assertEqual(reserva.precio_total, Decimal("200.00"))
            self.assertIsNotNone(tour)
            self.assertEqual(tour.cupos_disponibles, 3)

    async def test_concurrent_reservations_prevent_overselling(self) -> None:
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        concurrent_engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}",
            connect_args={"timeout": 30},
        )
        try:
            async with concurrent_engine.begin() as connection:
                await connection.run_sync(SQLModel.metadata.create_all)

            concurrent_session_maker = async_sessionmaker(
                concurrent_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
            )

            async with concurrent_session_maker() as session:
                turista_id, tour_id = await self._seed_reservation_dependencies(session)

            async def _book_three() -> object:
                async with concurrent_session_maker() as req_session:
                    service = ReservaService(
                        reserva_repo=ReservaRepository(req_session),
                        turista_repo=TuristaRepository(req_session),
                        tour_repo=TourRepository(req_session),
                        unit_of_work=UnitOfWork(req_session),
                        read_session_maker=concurrent_session_maker,
                    )
                    return await service.create(
                        self._reservation_input(turista_id, tour_id, cantidad_personas=3)
                    )

            results = await asyncio.gather(
                _book_three(),
                _book_three(),
                return_exceptions=True,
            )

            successes = [r for r in results if not isinstance(r, Exception)]
            errors = [r for r in results if isinstance(r, BusinessRuleError)]
            self.assertEqual(len(successes), 1)
            self.assertEqual(len(errors), 1)

            async with concurrent_session_maker() as session:
                tour = await TourRepository(session).get_by_id(tour_id)
                reservations = await ReservaRepository(session).get_multi()
                self.assertIsNotNone(tour)
                self.assertEqual(tour.cupos_disponibles, 2)
                self.assertEqual(len(reservations), 1)
        finally:
            await concurrent_engine.dispose()
            if os.path.exists(db_path):
                os.remove(db_path)

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
            self.assertEqual(updated_reserva.precio_total, Decimal("300.00"))
            self.assertIsNotNone(tour)
            self.assertEqual(tour.cupos_disponibles, 2)

    async def test_cancel_reservation_via_patch_restores_availability_once(self) -> None:
        async with self.session_maker() as session:
            turista_id, tour_id = await self._seed_reservation_dependencies(session)
            service = self._service(session)
            reserva = await service.create(self._reservation_input(turista_id, tour_id))

            canceled = await service.update(
                reserva.id_reserva,
                ReservaUpdate(estado="cancelada"),
            )
            self.assertEqual(canceled.estado, "cancelada")

            tour_after_cancel = await TourRepository(session).get_by_id(tour_id)
            self.assertIsNotNone(tour_after_cancel)
            self.assertEqual(tour_after_cancel.cupos_disponibles, 5)

            await service.delete(reserva.id_reserva)
            tour_after_delete = await TourRepository(session).get_by_id(tour_id)
            self.assertIsNotNone(tour_after_delete)
            self.assertEqual(tour_after_delete.cupos_disponibles, 5)

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

    async def test_migration_preserves_sold_out_tours_on_sqlite(self) -> None:
        async with self.session_maker() as session:
            _, tour_id = await self._seed_reservation_dependencies(session)
            async with UnitOfWork(session).transaction():
                await TourRepository(session).reserve_spots(tour_id, 5)

            async with self.engine.begin() as conn:
                await conn.execute(
                    text("UPDATE tour SET cupos_disponibles = 0 WHERE id_tour = :id"),
                    {"id": tour_id},
                )

            tour = await TourRepository(session).get_by_id(tour_id)
            self.assertIsNotNone(tour)
            self.assertEqual(tour.cupos_disponibles, 0)


if __name__ == "__main__":
    unittest.main()
