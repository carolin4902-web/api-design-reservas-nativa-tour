
from typing import Optional

from sqlmodel import Field, SQLModel


class TourBase(SQLModel):
    nombre: str = Field(min_length=1, max_length=100)
    descripcion: str = Field(min_length=1, max_length=500)
    ubicacion: str = Field(min_length=1, max_length=150)
    precio: float = Field(gt=0)
    capacidad: int = Field(gt=0)


class Tour(TourBase, table=True):
    __tablename__ = "tour"

    id_tour: Optional[int] = Field(
        default=None,
        primary_key=True
    )

    id_guia: int = Field(
        foreign_key="guia.id_guia"
    )


class TourCreate(TourBase):
    id_guia: int = Field(gt=0)


class TourUpdate(SQLModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100)
    descripcion: Optional[str] = Field(default=None, min_length=1, max_length=500)
    ubicacion: Optional[str] = Field(default=None, min_length=1, max_length=150)
    precio: Optional[float] = Field(default=None, gt=0)
    capacidad: Optional[int] = Field(default=None, gt=0)
    id_guia: Optional[int] = Field(default=None, gt=0)


class TourPublic(TourBase):
    id_tour: int
    id_guia: int
