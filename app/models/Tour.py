
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.Guia import Guia
    from app.models.Reserva import Reserva


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
        foreign_key="guia.id_guia",
        gt=0,
    )
    activo: bool = Field(default=True, nullable=False)
    cupos_disponibles: int = Field(default=0, ge=0)

    guia: Optional["Guia"] = Relationship(back_populates="tours")
    reservas: list["Reserva"] = Relationship(back_populates="tour")


class TourCreate(TourBase):
    id_guia: int = Field(gt=0)


class TourUpdate(SQLModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100)
    descripcion: Optional[str] = Field(default=None, min_length=1, max_length=500)
    ubicacion: Optional[str] = Field(default=None, min_length=1, max_length=150)
    precio: Optional[float] = Field(default=None, gt=0)
    capacidad: Optional[int] = Field(default=None, gt=0)
    id_guia: Optional[int] = Field(default=None, gt=0)
    activo: Optional[bool] = None


class TourPublic(TourBase):
    id_tour: int
    id_guia: int
    activo: bool
    cupos_disponibles: int
