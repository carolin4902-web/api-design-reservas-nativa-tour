# app/api/deps.py
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.repositories.task import TaskRepository

def get_task_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TaskRepository:
    """Instancia TaskRepository con la sesión de BD activa."""
    return TaskRepository(session)