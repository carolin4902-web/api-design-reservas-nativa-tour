import unittest

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

import app.models  # noqa: F401
from app.core.config import Settings
from app.core.exceptions import ConflictError
from app.core.unit_of_work import UnitOfWork
from app.models.destination import DestinationCreate, DestinationUpdate
from app.models.task import TaskCreate, TaskUpdate
from app.repositories.destination import DestinationRepository
from app.repositories.task import TaskRepository
from app.services.destination import DestinationService


class RepositoriesAndConfigTests(unittest.IsolatedAsyncioTestCase):
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

    def test_settings_requires_postgres_url_when_db_type_is_postgres(self) -> None:
        with self.assertRaises(ValidationError):
            Settings(
                _env_file=None,
                DB_TYPE="postgres",
                POSTGRES_URL="",
                DATABASE_URL="",
            )

    async def test_task_repository_crud_lifecycle(self) -> None:
        async with self.session_maker() as session:
            repo = TaskRepository(session)
            uow = UnitOfWork(session)

            async with uow.transaction():
                created = await repo.create(
                    TaskCreate(
                        title="Confirmar equipo",
                        description="Revisar chalecos salvavidas",
                        responsable_tipo="guia",
                        responsable_id=1,
                    )
                )

            fetched = await repo.get_by_id(created.id_task)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.title, "Confirmar equipo")

            filtered = await repo.get_multi(responsable_tipo="guia", responsable_id=1)
            self.assertEqual(len(filtered), 1)

            async with uow.transaction():
                updated = await repo.update(
                    created.id_task,
                    TaskUpdate(is_completed=True),
                )
            self.assertIsNotNone(updated)
            self.assertTrue(updated.is_completed)

            async with uow.transaction():
                deleted = await repo.delete(created.id_task)
            self.assertTrue(deleted)
            self.assertIsNone(await repo.get_by_id(created.id_task))

    async def test_destination_service_rejects_duplicate_name(self) -> None:
        async with self.session_maker() as session:
            service = DestinationService(
                destination_repo=DestinationRepository(session),
                unit_of_work=UnitOfWork(session),
            )
            await service.create(
                DestinationCreate(
                    name="Caño Cristales",
                    description="Río de cinco colores",
                    location="Meta",
                    price_per_night=250.0,
                    max_guests=4,
                )
            )
            with self.assertRaises(ConflictError):
                await service.create(
                    DestinationCreate(
                        name="Caño Cristales",
                        description="Duplicado",
                        location="Meta",
                        price_per_night=300.0,
                        max_guests=2,
                    )
                )


if __name__ == "__main__":
    unittest.main()
