
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class TaskBase(SQLModel):
    title: str = Field(min_length=1, max_length=120)

    description: Optional[str] = Field(
        default=None,
        max_length=500
    )

    is_completed: bool = Field(default=False)

    responsable_tipo: str = Field(
        regex="^(GUIA|ADMINISTRADOR)$"
    )

    responsable_id: int = Field(gt=0)


class Task(TaskBase, table=True):
    __tablename__ = "tasks"

    id_task: Optional[int] = Field(
        default=None,
        primary_key=True
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class TaskCreate(TaskBase):
    pass


class TaskUpdate(SQLModel):
    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=120
    )

    description: Optional[str] = Field(
        default=None,
        max_length=500
    )

    is_completed: Optional[bool] = Field(default=None)


class TaskPublic(TaskBase):
    id_task: int
    created_at: datetime
    updated_at: datetime
