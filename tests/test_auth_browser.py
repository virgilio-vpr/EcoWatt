from contextlib import contextmanager
import os
import socket
from threading import Thread, Event
from concurrent.futures import ThreadPoolExecutor
import time
from urllib.parse import urlsplit

import httpx
import pytest
import uvicorn
from playwright.sync_api import sync_playwright, expect

from ecowatt.main import create_app
from test_mail_delivery import smtp_capture, smtp_settings
from test_auth import registration


@contextmanager
def running_app(settings, mailer=None):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        origin = f"http://127.0.0.1:{listener.getsockname()[1]}"
        app = create_app(settings.model_copy(update={"public_origin": origin}), mailer=mailer)
        server = uvicorn.Server(uvicorn.Config(app, access_log=False, log_level="error"))
        worker = Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        worker.start()
        try:
            for _ in range(100):
                if server.started:
                    break
                time.sleep(.05)
            assert server.started
            yield origin
        finally:
            server.should_exit = True
            worker.join(timeout=10)
            app.state.engine.dispose()
            assert not worker.is_alive()


@pytest.mark.skipif(os.environ.get("ECOWATT_BROWSER_TESTS") != "1", reason="Ativar explicitamente teste no Edge já instalado")
def test_browser_register_activate_login_reset_and_revoke(environment):
    with smtp_capture() as (port, messages), running_app(smtp_settings(environment.settings, port)) as origin:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="msedge", headless=True, timeout=20000)
            try:
                context = browser.new_context()
                # Nenhuma solicitação da página pode sair do loopback sintético.
                context.route("**/*", lambda route: route.continue_() if urlsplit(route.request.url).hostname == "127.0.0.1" else route.abort())
                page = context.new_page()
                page.set_default_timeout(10000)
                errors, requests = [], []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("request", lambda request: requests.append(request.url))
                page.goto(origin + "/auth/register")
                values = {"email": "browser@ecowatt.test", "email_confirmation": "browser@ecowatt.test",
                          "responsible_name": "Pessoa Sintética", "company.name": "Empresa Sintética",
                          "company.phone": "11999999999", "company.address_line": "Rua Exemplo, 1",
                          "company.city": "Exemplo", "company.state": "SP", "company.postal_code": "00000-000",
                          "password": "Browser_12", "password_confirmation": "Browser_12"}
                for name, value in values.items():
                    page.locator(f'[name="{name}"]').fill(value)
                page.get_by_role("button", name="Criar conta", exact=True).click()
                expect(page.locator("#auth-status")).to_contain_text("Solicitação recebida")
                messages.wait_for_count(1)
                assert len(messages) == 1
                link = next(line for line in messages[-1].get_content().splitlines() if "#token=" in line)
                secret = link.split("#token=")[1]
                page.goto(link)
                expect(page).to_have_url(origin + "/auth/activation")
                assert secret not in page.content()
                page.get_by_role("button", name="Confirmar e-mail", exact=True).click()
                expect(page.locator("#auth-status")).to_contain_text("E-mail confirmado")
                # Uso único também com link reaberto no navegador.
                page.goto(link)
                page.get_by_role("button", name="Confirmar e-mail", exact=True).click()
                expect(page.locator("#auth-status")).to_contain_text("inválido ou expirado")
                page.goto(origin + "/auth/login")
                page.locator('[name="email"]').fill("browser@ecowatt.test")
                page.locator('[name="password"]').fill("Browser_12")
                page.get_by_role("button", name="Entrar", exact=True).click()
                expect(page).to_have_url(origin + "/account")
                expect(page.get_by_role("heading", level=1)).to_have_text("Empresa Sintética")
                previous_session = context.cookies()
                page.goto(origin + "/auth/forgot-password")
                page.locator('[name="email"]').fill("browser@ecowatt.test")
                page.get_by_role("button", name="Recuperar acesso", exact=True).click()
                expect(page.locator("#auth-status")).to_contain_text("Solicitação recebida")
                messages.wait_for_count(2)
                reset = next(line for line in messages[-1].get_content().splitlines() if "#token=" in line)
                page.goto(reset)
                expect(page).to_have_url(origin + "/auth/reset")
                page.locator('[name="password"]').fill("NovaSenha_34")
                page.locator('[name="password_confirmation"]').fill("NovaSenha_34")
                page.get_by_role("button", name="Mostrar senha", exact=True).click()
                expect(page.locator('[name="password"]')).to_have_attribute("type", "text")
                page.get_by_role("button", name="Redefinir senha", exact=True).click()
                expect(page.locator("#auth-status")).to_contain_text("Senha redefinida")
                cookie = next(c["value"] for c in previous_session if c["name"] == "ecowatt_session")
                assert httpx.get(origin + "/api/v1/me", cookies={"ecowatt_session": cookie}).status_code == 401
                page.goto(origin + "/auth/login")
                page.locator('[name="email"]').fill("browser@ecowatt.test")
                page.locator('[name="password"]').fill("NovaSenha_34")
                page.get_by_role("button", name="Entrar", exact=True).click()
                expect(page).to_have_url(origin + "/account")
                assert all("#token=" not in url and "?token=" not in url for url in requests)
                assert errors == []
            finally:
                browser.close()


def test_http_response_does_not_wait_for_smtp_delivery(environment):
    started, release = Event(), Event()

    class SlowMailer:
        def send(self, message):
            started.set()
            assert release.wait(timeout=5)

    with running_app(environment.settings, mailer=SlowMailer()) as origin:
        try:
            with httpx.Client(base_url=origin) as client, ThreadPoolExecutor(max_workers=1) as pool:
                csrf = client.get("/api/v1/auth/csrf").json()["csrf_token"]
                future = pool.submit(client.post, "/api/v1/auth/register", json=registration(),
                                     headers={"Origin": origin, "X-CSRF-Token": csrf})
                assert started.wait(timeout=3)
                assert future.result(timeout=2).status_code == 202
        finally:
            release.set()
