import asyncio
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from ecowatt.config import Settings
from ecowatt.main import create_app


def test_api_without_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    async def check():
        transport = ASGITransport(app=create_app(Settings(_env_file=None)))
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            assert (await client.get("/api/v1/health")).json() == {"status": "ok"}
            schema = (await client.get("/api/v1/openapi.json")).json()
            assert "/api/v1/health" in schema["paths"]
            assert (await client.get("/api/v1/docs")).status_code == 200
    asyncio.run(check())
    assert list(tmp_path.iterdir()) == []


def test_settings_env_file_and_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    env = tmp_path / ".env"
    env.write_text("ENVIRONMENT=test\nDATA_DIR=synthetic\n", encoding="utf-8")
    monkeypatch.setenv("DATA_DIR", "override")
    settings = Settings(_env_file=env)
    assert settings.environment == "test"
    assert settings.data_dir == Path("override")


@pytest.mark.parametrize("values", [
    {"environment": "production"},
    {"database_url": "postgresql://localhost/ecowatt"},
    {"database_url": "sqlite:///"},
    {"email_provider": "smtp"},
])
def test_unsupported_settings_rejected(values):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **values)
