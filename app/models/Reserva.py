from datetime import date, datetime, timezone
from decimal import Decimal

from pydantic import field_validator
from sqlmodel import Field, SQLModel

ESTADOS_RESERVA_VALIDOS = {"pendiente", "confirmada", "cancelada"}


# 1. Base Común
class ReservaBase(SQLModel):
    fecha_reserva: date

    cantidad_personas: int = Field(ge=1)

    precio_total: Decimal = Field(gt=0)

    estado: str = Field(default="confirmada", min_length=1, max_length=50)

    @field_validator("estado")
    @classmethod
    def validate_estado(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ESTADOS_RESERVA_VALIDOS:
            allowed = ", ".join(sorted(ESTADOS_RESERVA_VALIDOS))
            raise ValueError(f"Estado inválido '{value}'. Valores permitidos: {allowed}.")
        return normalized


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
class ReservaCreate(SQLModel):
    fecha_reserva: date
    cantidad_personas: int = Field(ge=1)
    precio_total: Decimal | None = Field(default=None, gt=0)
    estado: str = Field(default="confirmada", min_length=1, max_length=50)
    id_turista: int = Field(gt=0)
    id_tour: int = Field(gt=0)

    @field_validator("estado")
    @classmethod
    def validate_estado(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ESTADOS_RESERVA_VALIDOS:
            allowed = ", ".join(sorted(ESTADOS_RESERVA_VALIDOS))
            raise ValueError(f"Estado inválido '{value}'. Valores permitidos: {allowed}.")
        return normalized


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

    id_turista: int | None = Field(default=None, gt=0)
    id_tour: int | None = Field(default=None, gt=0)

    @field_validator("estado")
    @classmethod
    def validate_estado(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in ESTADOS_RESERVA_VALIDOS:
            allowed = ", ".join(sorted(ESTADOS_RESERVA_VALIDOS))
            raise ValueError(f"Estado inválido '{value}'. Valores permitidos: {allowed}.")
        return normalized


# 5. DTO de Salida (GET)
class ReservaPublic(ReservaBase):
    id_reserva: int
    id_turista: int
    id_tour: int
    created_at: datetime
    updated_at: datetime