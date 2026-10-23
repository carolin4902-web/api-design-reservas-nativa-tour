from datetime import date
from decimal import Decimal

from sqlmodel import Field, SQLModel


class Reserva(SQLModel, table=True):
    id_reserva: int | None = Field(default=None, primary_key=True)
    fecha_reserva: date
    cantidad_personas: int
    precio_total: Decimal
    estado: str
    id_turista: int = Field(foreign_key="turista.id_turista")
    id_tour: int = Field(foreign_key="tour.id_tour")