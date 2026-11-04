
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.task import Task, TaskCreate, TaskUpdate


class TaskRepository:
    """Capa 3 - Acceso a Datos puro para tareas."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session


    async def get_by_id(self, task_id: int) -> Task | None:
        """Busca una tarea por su clave primaria (ID)."""
        return await self.session.get(Task, task_id)

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        responsable_id: int | None = None,
        only_pending: bool = False,
    ) -> list[Task]:
        """Obtiene un listado paginado con filtros opcionales."""
        statement = select(Task)

        # Filtro opcional por responsable
        if responsable_id is not None:
            statement = statement.where(Task.responsable_id == responsable_id)

        # Filtro opcional para ver solo pendientes
        if only_pending:
            statement = statement.where(Task.is_completed == False)  # noqa: E712

        statement = statement.order_by(Task.id_task).offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())


    async def create(self, task_in: TaskCreate) -> Task:
        """Inserta una nueva tarea en la base de datos."""
        db_task = Task.model_validate(task_in)
        self.session.add(db_task)
        await self.session.commit()
        await self.session.refresh(db_task)
        return db_task


    async def update(self, db_task: Task, task_in: TaskUpdate) -> Task:
        """Actualiza únicamente los campos que el cliente envió."""
        update_data: dict[str, Any] = task_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_task, field, value)

        db_task.updated_at = datetime.now(timezone.utc)
        self.session.add(db_task)
        await self.session.commit()
        await self.session.refresh(db_task)
        return db_task


    async def delete(self, db_task: Task) -> None:
        """Elimina físicamente una tarea de la base de datos."""
        await self.session.delete(db_task)
        await self.session.commit()
