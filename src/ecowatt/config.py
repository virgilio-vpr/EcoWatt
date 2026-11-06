"""Configuração sem efeitos de escrita ou conexão ao importar."""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from urllib.parse import urlsplit
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    environment: Literal["development", "test"] = "development"
    data_dir: Path = Path("data")
    database_url: SecretStr = Field(default=SecretStr("sqlite:///data/ecowatt.sqlite3"))
    email_provider: Literal["disabled"] = "disabled"
    local_secret: SecretStr = SecretStr("")
    seed_admin_password: SecretStr = SecretStr("")
    seed_client_password: SecretStr = SecretStr("")
    public_origin: str = "http://127.0.0.1:8000"
    cookie_secure: bool = True
    session_idle_seconds: int = Field(default=1800, ge=60, le=86400)
    session_absolute_seconds: int = Field(default=43200, ge=60, le=604800)

    @field_validator("public_origin")
    @classmethod
    def trusted_origin(cls, value: str) -> str:
        url = urlsplit(value)
        if (url.scheme not in {"http", "https"} or not url.hostname or url.username
                or url.password or url.path not in {"", "/"} or url.query or url.fragment):
            raise ValueError("Origem HTTP(S) sem caminho/credenciais exigida")
        if url.scheme == "http" and url.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("HTTP permitido somente em loopback local")
        return value.rstrip("/")

    @field_validator("database_url")
    @classmethod
    def local_sqlite_only(cls, value: SecretStr) -> SecretStr:
        url = value.get_secret_value()
        if not url.startswith("sqlite:///") or not url.removeprefix("sqlite:///"):
            raise ValueError("Esta entrega suporta somente SQLite local")
        path = url.removeprefix("sqlite:///")
        if path.startswith(("//", "\\")) or path.startswith("file:") or any(c in path for c in "?\x00\n\r"):
            raise ValueError("SQLite exige arquivo local, sem UNC/URI ou parâmetros")
        return value
