"""Consulta de suporte sem arquivos ou processamento; somente fixtures sintéticas."""
import os
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import expect, sync_playwright
from sqlalchemy import func, select

from ecowatt.db.admissions import InvoiceAdmission
from ecowatt.db.models import Distributor, Simulation, SimulationTask
from ecowatt.db.session import transaction
from test_admission import setup
from test_auth_browser import running_app
from test_simulations import create


@pytest.mark.parametrize("saved,code,layout,message", [
    (False, None, "unknown", "Salve os dados da unidade"),
    (True, "SYNTHETIC", "synthetic-v1", "Suporte interno exclusivamente sintético"),
    (True, "SYNTHETIC", "unknown", "Layout não suportado"),
    (True, "ENEL_SP", "enel-v1", "Layout não suportado"),
])
def test_support_html_matches_json_without_creating_work(environment, saved, code, layout, message):
    engine, sim, _ = setup(environment)
    with transaction(engine, write=True) as db:
        row = db.get(Simulation, sim["id"])
        if not saved:
            row.unit_saved_at = None
            row.distributor_id = None
        elif code != "SYNTHETIC":
            distributor = db.scalar(select(Distributor).where(Distributor.code == code))
            if distributor is None:
                distributor = Distributor(code=code, name="Distribuidora de teste")
                db.add(distributor)
                db.flush()
            row.distributor_id = distributor.id
    client = environment.client().login()
    query = {"layout_version": layout}
    api = client.request("GET", f"/api/v1/simulations/{sim['id']}/invoice-admission", params=query).json()
    for suffix in ("invoices", "invoice-admission"):
        result = client.request("GET", f"/simulations/{sim['id']}/{suffix}", params=query)
        assert result.status_code == 200 and message in result.text
        assert (api["distributor_code"] or "Não informada") in result.text
        assert 'value="' + api["layout_version"] + '"' in result.text
        assert "Upload e leitura de documentos reais estão desabilitados" in result.text
        assert ("canal de solicitação de contato" in result.text) == api["contact_required"]
        assert 'type="file"' not in result.text and "multipart/form-data" not in result.text
    assert api["document_upload_enabled"] is False
    with transaction(engine) as db:
        assert db.scalar(select(func.count()).select_from(InvoiceAdmission)) == 0
        assert db.scalar(select(func.count()).select_from(SimulationTask)) == 0
        assert db.get(Simulation, sim["id"]).dataset_revision == 1


def test_support_fragment_authorization_validation_and_escaping(environment):
    engine, sim, _ = setup(environment)
    path = f"/simulations/{sim['id']}/invoice-admission"
    assert environment.client().request("GET", path, headers={"HX-Request": "true"}).status_code == 401
    owner = environment.client().login()
    admin = environment.client().login("admin@ecowatt.test")
    assert admin.request("GET", path).status_code == 200
    for suffix in ("invoices", "invoice-admission"):
        url = f"/simulations/{sim['id']}/{suffix}"
        for layout in ("", "a" * 81):
            assert owner.request("GET", url, params={"layout_version": layout}).status_code == 422
        escaped = owner.request("GET", url, params={"layout_version": '\"><script>alert(1)</script>'})
        assert "<script>alert(1)</script>" not in escaped.text
        assert "&lt;script&gt;" in escaped.text
    other = create(admin).json()
    assert owner.request("GET", f"/simulations/{other['id']}/invoice-admission").status_code == 404
    deleted = owner.request("DELETE", f"/api/v1/simulations/{sim['id']}", json={"confirm": True, "expected_revision": 1})
    assert deleted.status_code == 204
    assert admin.request("GET", path).status_code == 404


@pytest.mark.skipif(os.environ.get("ECOWATT_BROWSER_TESTS") != "1", reason="Ativar teste no Edge instalado")
def test_support_consultation_in_edge_and_without_javascript(environment):
    engine, sim, _ = setup(environment)
    with running_app(environment.settings) as origin, sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True, timeout=20000)
        try:
            context = browser.new_context()
            context.route("**/*", lambda route: route.continue_() if urlsplit(route.request.url).hostname == "127.0.0.1" else route.abort())
            page = context.new_page()
            errors, writes = [], []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(origin + "/auth/login")
            page.locator('[name="email"]').fill("cliente@ecowatt.test")
            page.locator('[name="password"]').fill("EcoWatt!123")
            page.get_by_role("button", name="Entrar", exact=True).click()
            expect(page).to_have_url(origin + "/account")
            page.on("request", lambda request: writes.append(request.url) if request.method != "GET" else None)
            listing = f"{origin}/simulations/{sim['id']}/invoices"
            page.goto(listing)
            page.get_by_label("Versão do layout a consultar").fill("synthetic-v1")
            page.get_by_role("button", name="Consultar suporte").click()
            expect(page.locator("#invoice-admission")).to_contain_text("Suporte interno exclusivamente sintético")
            expect(page).to_have_url(listing)
            page.get_by_label("Versão do layout a consultar").fill("other-v1")
            page.get_by_role("button", name="Consultar suporte").click()
            expect(page.locator("#invoice-admission")).to_contain_text("Layout não suportado")
            assert page.locator('input[type="file"]').count() == 0
            assert writes == [] and errors == []
            fallback = browser.new_context(java_script_enabled=False, storage_state=context.storage_state())
            fallback.route("**/*", lambda route: route.continue_() if urlsplit(route.request.url).hostname == "127.0.0.1" else route.abort())
            plain = fallback.new_page()
            plain.goto(listing)
            plain.get_by_label("Versão do layout a consultar").fill("synthetic-v1")
            plain.get_by_role("button", name="Consultar suporte").click()
            expect(plain).to_have_url(listing + "?layout_version=synthetic-v1")
            expect(plain.locator("#invoice-admission")).to_contain_text("Suporte interno exclusivamente sintético")
            with transaction(engine) as db:
                assert db.scalar(select(func.count()).select_from(InvoiceAdmission)) == 0
                assert db.scalar(select(func.count()).select_from(SimulationTask)) == 0
        finally:
            browser.close()
