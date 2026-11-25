from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.exceptions import ConflictError
from app.models.task import Task, TaskCreate, TaskPublic, TaskUpdate


class TaskRepository:
    """Repositorio asíncrono para gestionar operaciones CRUD de tareas."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, task_id: int) -> TaskPublic | None:
        """Obtiene una tarea por su identificador."""
        task = await self.session.get(Task, task_id)
        if task is None:
            return None
        return TaskPublic.model_validate(task)

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        responsable_tipo: str | None = None,
        responsable_id: int | None = None,
    ) -> list[TaskPublic]:
        """Lista tareas con paginación y filtro opcional por responsable."""
        statement = select(Task)
        if responsable_tipo is not None:
            statement = statement.where(Task.responsable_tipo == responsable_tipo)
        if responsable_id is not None:
            statement = statement.where(Task.responsable_id == responsable_id)
        statement = statement.offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return [TaskPublic.model_validate(task) for task in result.scalars().all()]

    async def create(self, task_in: TaskCreate) -> TaskPublic:
        """Crea una nueva tarea en la sesión actual."""
        db_task = Task.model_validate(task_in)
        self.session.add(db_task)
        try:
            await self.session.flush()
        except IntegrityError as exc:
            raise ConflictError("No se pudo crear la tarea por conflicto de integridad.") from exc
        await self.session.refresh(db_task)
        return TaskPublic.model_validate(db_task)

    async def update(self, task_id: int, task_in: TaskUpdate) -> TaskPublic | None:
        """Actualiza parcialmente una tarea existente."""
        db_task = await self.session.get(Task, task_id)
        if db_task is None:
            return None

        update_data: dict[str, Any] = task_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_task, field, value)
        db_task.updated_at = datetime.now(timezone.utc)
        self.session.add(db_task)
        try:
            await self.session.flush()
        except IntegrityError as exc:
            raise ConflictError("No se pudo actualizar la tarea por conflicto de integridad.") from exc
        await self.session.refresh(db_task)
        return TaskPublic.model_validate(db_task)

    async def delete(self, task_id: int) -> bool:
        """Elimina una tarea por su ID y retorna True si existía."""
        db_task = await self.session.get(Task, task_id)
        if db_task is None:
            return False

        await self.session.delete(db_task)
        await self.session.flush()
        return True
