import secrets
from typing import Annotated, Any, Literal

from pydantic import AnyUrl, BeforeValidator, computed_field
from pydantic_core import MultiHostUrl
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

    S3_ENDPOINT_URL: str = "tse-minio:9000"
    S3_ACCESS_KEY: str = "12345678"
    S3_SECRET_ACCESS_KEY: str = "password"
    S3_BUCKET_NAME: str = "tse"

    IMAGE_PROXY_URL: str = "http://172.17.0.1:8080"
    IMGPROXY_KEY: str = "736563726574"
    IMGPROXY_SALT: str = "68656C6C6F"

    APP_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []

    APP_NAME: str = "TSE"

    PROJECT_NAME: str = "TSE"

    DB_SCHEME: Literal["postgresql"] = "postgresql"
    DB_DRIVER: str = "asyncpg"
    DB_SERVER: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_DB: str = ""

    @computed_field
    @property
    def DATABASE_URI(self) -> MultiHostUrl:
        return MultiHostUrl.build(
            scheme=self.DB_SCHEME,
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_SERVER,
            port=self.DB_PORT,
            path=self.DB_DB,
        )


settings = Settings()
