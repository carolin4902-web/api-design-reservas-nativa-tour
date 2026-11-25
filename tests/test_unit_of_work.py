import unittest

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.unit_of_work import UnitOfWork
from app.models.destination import Destination, DestinationCreate
from app.repositories.destination import DestinationRepository


class UnitOfWorkTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Destination.__table__.create)
        self.session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def test_successful_transaction_commits_flushed_repository_work(self) -> None:
        async with self.session_maker() as session:
            repository = DestinationRepository(session)
            unit_of_work = UnitOfWork(session)

            async with unit_of_work.transaction():
                destination = await repository.create(
                    DestinationCreate(
                        name="Bosque",
                        description="Reserva natural",
                        location="Amazonas",
                        price_per_night=120,
                        max_guests=4,
                    )
                )

            self.assertIsNotNone(destination.id)
            destinations = await repository.list_all()
            self.assertEqual([item.name for item in destinations], ["Bosque"])

    async def test_failed_transaction_rolls_back_flushed_repository_work(self) -> None:
        async with self.session_maker() as session:
            repository = DestinationRepository(session)
            unit_of_work = UnitOfWork(session)

            with self.assertRaisesRegex(RuntimeError, "abort transaction"):
                async with unit_of_work.transaction():
                    await repository.create(
                        DestinationCreate(
                            name="Montaña",
                            description="Destino de prueba",
                            location="Andes",
                            price_per_night=90,
                            max_guests=2,
                        )
                    )
                    raise RuntimeError("abort transaction")

            destinations = await repository.list_all()
            self.assertEqual(destinations, [])


if __name__ == "__main__":
    unittest.main()
