from sqlmodel import SQLModel, Field

class Turista(SQLModel, table=True):
    """Tabla de base de datos 'turista'."""

    __tablename__ = "turista"

    id_turista: int | None = Field(default=None, primary_key=True)
    nombre: str
    apellido: str
    correo: str
    telefono: str

    