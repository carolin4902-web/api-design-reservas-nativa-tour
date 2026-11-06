from datetime import date, datetime, timezone
from decimal import Decimal

from sqlmodel import Field, SQLModel


# 1. Base Común
class ReservaBase(SQLModel):
    fecha_reserva: date

    cantidad_personas: int = Field(ge=1)

    precio_total: Decimal = Field(gt=0)

    estado: str = Field(min_length=1, max_length=50)


# 2. Tabla de Base de Datos
class Reserva(ReservaBase, table=True):
    __tablename__ = "reserva"

    id_reserva: int | None = Field(
        default=None,
        primary_key=True
    )

    id_turista: int = Field(
        foreign_key="turista.id_turista"
    )

    id_tour: int = Field(
        foreign_key="tour.id_tour"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )


# 3. DTO de Entrada (POST)
class ReservaCreate(ReservaBase):
    id_turista: int
    id_tour: int


# 4. DTO de Edición (PATCH)
class ReservaUpdate(SQLModel):
    fecha_reserva: date | None = None

    cantidad_personas: int | None = Field(default=None, ge=1)

    precio_total: Decimal | None = Field(default=None, gt=0)

    estado: str | None = Field(
        default=None,
        min_length=1,
        max_length=50
    )

    id_turista: int | None = None
    id_tour: int | None = None


# 5. DTO de Salida (GET)
class ReservaPublic(ReservaBase):
    id_reserva: int
    id_turista: int
    id_tour: int
    created_at: datetime
    updated_at: datetime