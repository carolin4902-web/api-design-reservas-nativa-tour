from typing import Literal
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración global de la aplicación cargada desde variables de entorno."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "FastAPI SQLModel API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Selector de base de datos: "sqlite" o "postgres"
    DB_TYPE: Literal["sqlite", "postgres"] = "sqlite"

    # Cadenas de conexión configurables
    SQLITE_URL: str = "sqlite+aiosqlite:///./fastapi_demo.db"
    POSTGRES_URL: str = ""
    RENDER_DATABASE_URL: str = Field(default="", validation_alias="DATABASE_URL")

    ECHO_SQL: bool = False

    @model_validator(mode="after")
    def validate_database_config(self) -> "Settings":
        """Valida que exista una cadena de conexión cuando DB_TYPE es 'postgres'."""
        if self.DB_TYPE == "postgres" and not self.raw_postgres_url:
            raise ValueError(
                "POSTGRES_URL o DATABASE_URL debe configurarse cuando DB_TYPE='postgres'."
            )
        return self

    @property
    def raw_postgres_url(self) -> str:
        """Retorna la URL de PostgreSQL configurada en POSTGRES_URL o DATABASE_URL."""
        return (self.POSTGRES_URL or self.RENDER_DATABASE_URL).strip()

    @property
    def is_postgres(self) -> bool:
        """Indica si la aplicación debe conectarse a PostgreSQL."""
        if self.DB_TYPE == "postgres" and self.raw_postgres_url:
            return True
        return bool(self.RENDER_DATABASE_URL.strip()) and not self.POSTGRES_URL.strip()

    @property
    def DATABASE_URL(self) -> str:
        """Retorna la URL asíncrona adecuada adaptando cadenas de Render/Neon para asyncpg."""
        if self.is_postgres and self.raw_postgres_url:
            url = self.raw_postgres_url
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://") and not url.startswith(
                "postgresql+asyncpg://"
            ):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

            # asyncpg no acepta ?sslmode=... ni ?channel_binding=... en el querystring
            parts = urlsplit(url)
            if parts.query:
                query_params = parse_qs(parts.query, keep_blank_values=True)
                query_params.pop("sslmode", None)
                query_params.pop("channel_binding", None)
                clean_query = urlencode(query_params, doseq=True)
                url = urlunsplit(
                    (parts.scheme, parts.netloc, parts.path, clean_query, parts.fragment)
                )
            return url
        return self.SQLITE_URL


# Instancia única reutilizable en toda la aplicación (Singleton)
settings = Settings()