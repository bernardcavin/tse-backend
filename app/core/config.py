import secrets
from typing import Annotated, Any, Literal

from pydantic import AnyUrl, BeforeValidator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, (list, str)):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    DOMAIN: str = "localhost"
    PORT: int = 8000
    ROOT_PATH: str = "/backend"
    SECRET_KEY: str = secrets.token_urlsafe(32)

    LIMITER_TIMES: int = 9999
    LIMITER_SECONDS: int = 9999

    LOCAL_UPLOAD_DIR: str = "/uploads"

    SQL_ECHO: bool = False
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    APP_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []

    APP_NAME: str = "SIGAP"
    OTLP_GRPC_ENDPOINT: str = "sigap-tempo:4317"

    PROJECT_NAME: str = "SIGAP"

    DB_SCHEME: Literal["sqlite"] = "sqlite"
    DB_PATH: str = "./sigap.db"  # or absolute path if you want

    @computed_field
    @property
    def DATABASE_URI(self) -> str:
        # SQLite don’t use username, password, host, port
        # For async SQLAlchemy, use `sqlite+aiosqlite:///`
        return f"{self.DB_SCHEME}:///{self.DB_PATH}"


settings = Settings()
