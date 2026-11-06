"""Configuração sem efeitos de escrita ou conexão ao importar."""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
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

    @field_validator("database_url")
    @classmethod
    def local_sqlite_only(cls, value: SecretStr) -> SecretStr:
        url = value.get_secret_value()
        if not url.startswith("sqlite:///") or not url.removeprefix("sqlite:///"):
            raise ValueError("Esta entrega suporta somente SQLite local")
        return value
