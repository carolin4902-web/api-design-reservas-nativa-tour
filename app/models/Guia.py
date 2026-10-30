from sqlmodel import Field, SQLModel


class Guia(SQLModel, table=True):
    id_guia: int | None = Field(default=None, primary_key=True)
    nombre: str
    apellido: str
    correo: str
    telefono: str
    especialidad: str

