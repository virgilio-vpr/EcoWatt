"""Configuração sem efeitos de escrita ou conexão ao importar."""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from email_validator import validate_email
from urllib.parse import urlsplit
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    environment: Literal["development", "test"] = "development"
    data_dir: Path = Path("data")
    database_url: SecretStr = Field(default=SecretStr("sqlite:///data/ecowatt.sqlite3"))
    email_provider: Literal["disabled", "smtp"] = "disabled"
    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_security: Literal["starttls", "ssl", "local"] = "starttls"
    smtp_username: str = ""
    smtp_password: SecretStr = SecretStr("")
    smtp_sender: str = "noreply@ecowatt.test"
    smtp_timeout_seconds: int = Field(default=5, ge=1, le=10)
    local_secret: SecretStr = SecretStr("")
    seed_admin_password: SecretStr = SecretStr("")
    seed_client_password: SecretStr = SecretStr("")
    public_origin: str = "http://127.0.0.1:8000"
    cookie_secure: bool = True
    session_idle_seconds: int = Field(default=1800, ge=60, le=86400)
    session_absolute_seconds: int = Field(default=43200, ge=60, le=604800)

    @model_validator(mode="after")
    def smtp_configuration(self):
        if self.email_provider == "smtp":
            if not self.smtp_host or any(c.isspace() for c in self.smtp_host):
                raise ValueError("SMTP_HOST obrigatório, sem espaços")
            self.smtp_sender = validate_email(self.smtp_sender, check_deliverability=False,
                                              test_environment=True).normalized
            if bool(self.smtp_username) != bool(self.smtp_password.get_secret_value()):
                raise ValueError("Informe usuário e senha SMTP juntos")
            if self.smtp_security == "local":
                if self.smtp_host not in {"127.0.0.1", "::1"} or self.smtp_username:
                    raise ValueError("SMTP sem TLS somente em loopback numérico, sem credenciais")
        return self

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
