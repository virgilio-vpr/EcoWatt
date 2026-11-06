import asyncio
from dataclasses import dataclass

import httpx
import pytest
from alembic import command
from alembic.config import Config

from ecowatt.config import Settings
from ecowatt.main import create_app
from ecowatt.seed import seed
from ecowatt.services.mail import MemoryMailer

PASSWORD = "EcoWatt!123"


class Client:
    def __init__(self, app):
        self.app = app
        self.cookies = httpx.Cookies()
        self.csrf = ""

    def request(self, method, path, **kwargs):
        headers = {"Origin": "http://127.0.0.1:8000", "X-CSRF-Token": self.csrf}
        headers.update(kwargs.pop("headers", {}))

        async def send():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app),
                                        base_url="http://127.0.0.1:8000", cookies=self.cookies) as client:
                response = await client.request(method, path, headers=headers, **kwargs)
                self.cookies = client.cookies
                return response
        return asyncio.run(send())

    def prepare(self):
        response = self.request("GET", "/api/v1/auth/csrf")
        assert response.status_code == 200, response.text
        self.csrf = response.json()["csrf_token"]
        return self

    def login(self, email="cliente@ecowatt.test", password=PASSWORD):
        self.prepare()
        response = self.request("POST", "/api/v1/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        self.csrf = response.json()["csrf_token"]
        return self


@dataclass
class Environment:
    app: object
    settings: Settings
    mailer: MemoryMailer

    def client(self):
        return Client(self.app)


@pytest.fixture
def environment(tmp_path):
    settings = Settings(_env_file=None, environment="test", cookie_secure=False,
                        database_url="sqlite:///" + str(tmp_path / "test.sqlite3"),
                        seed_admin_password=PASSWORD, seed_client_password=PASSWORD)
    cfg = Config("alembic.ini")
    cfg.attributes["settings"] = settings
    command.upgrade(cfg, "head")
    mailer = MemoryMailer()
    app = create_app(settings, mailer=mailer)
    seed(app.state.engine, settings)
    yield Environment(app, settings, mailer)
    app.state.engine.dispose()
