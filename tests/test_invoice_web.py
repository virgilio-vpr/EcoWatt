import os
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import expect, sync_playwright

from test_auth_browser import running_app
from test_invoice_confirmation import another, published


def test_invoice_listing_and_detail_are_protected_and_rendered(environment):
    _, sim, invoice_id = published(environment)
    client = environment.client()
    assert client.request("GET", f"/simulations/{sim['id']}/invoices", headers={"HX-Request": "true"}).status_code == 401
    client.login()
    listing = client.request("GET", f"/simulations/{sim['id']}/invoices", headers={"HX-Request": "true"})
    assert listing.status_code == 200 and "Faturas da simulação" in listing.text
    detail = client.request("GET", f"/simulations/{sim['id']}/invoices/{invoice_id}/fragment", headers={"HX-Request": "true"})
    assert detail.status_code == 200 and "Detalhe da fatura" in detail.text and "Campos pendentes" in detail.text
    assert "Corrigir campos" in detail.text and "Conferi todas as linhas" in detail.text
    assert "data-field-edit" in detail.text and "data-field-version" in detail.text
    assert "Salvar escolha do conjunto" not in detail.text


def test_invoice_detail_page_is_available_to_owner_and_admin(environment):
    _, sim, invoice_id = published(environment)
    owner = environment.client().login()
    page = owner.request("GET", f"/simulations/{sim['id']}/invoices/{invoice_id}")
    assert page.status_code == 200 and "Conferência da fatura" in page.text
    admin = environment.client().login("admin@ecowatt.test")
    admin_page = admin.request("GET", f"/simulations/{sim['id']}/invoices/{invoice_id}")
    assert admin_page.status_code == 200 and "Detalhe da fatura" in admin_page.text


def test_invoice_conflict_group_exposes_explicit_selection_and_history(environment):
    engine, sim, first = published(environment)
    another(engine, sim)
    client = environment.client().login()
    page = client.request("GET", f"/simulations/{sim['id']}/invoices/{first}")
    assert page.status_code == 200
    assert "Possíveis duplicatas ou refaturamentos" in page.text
    assert "data-included-invoice" in page.text and "data-member-versions" in page.text
    assert "Histórico de escolhas do conjunto" in page.text


@pytest.mark.skipif(os.environ.get("ECOWATT_BROWSER_TESTS") != "1", reason="Ativar explicitamente teste no Edge já instalado")
def test_invoice_review_confirmation_and_selection_flow_in_edge(environment):
    engine, sim, first = published(environment)
    another(engine, sim)

    with running_app(environment.settings) as origin, sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True, timeout=20000)
        try:
            context = browser.new_context()
            context.route("**/*", lambda route: route.continue_() if urlsplit(route.request.url).hostname == "127.0.0.1" else route.abort())
            page = context.new_page()
            page.set_default_timeout(10000)
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))

            page.goto(origin + "/auth/login")
            page.locator('[name="email"]').fill("cliente@ecowatt.test")
            page.locator('[name="password"]').fill("EcoWatt!123")
            page.get_by_role("button", name="Entrar", exact=True).click()
            expect(page).to_have_url(origin + "/account")

            detail_url = f"{origin}/simulations/{sim['id']}/invoices/{first}"
            page.goto(detail_url)
            page.get_by_text("Corrigir campos", exact=True).click()
            review = page.locator('form[data-api-kind="review"]')
            holder = page.locator('fieldset').filter(
                has=page.locator('[data-field-path][value="header.holder_name"]'))
            holder.locator("[data-field-edit]").check()
            holder.locator("[data-field-value]").fill("true")
            review.locator('[name="reason_code"]').fill("browser_correction")
            review.get_by_role("button", name="Salvar correções selecionadas").click()
            expect(review.locator("[data-status]")).to_contain_text("Operação registrada")

            stale_confirmation = page.locator('form[data-api-kind="confirmation"]')
            stale_confirmation.locator('[name="billing_coverage_confirmed"]').check()
            accepted = stale_confirmation.locator("[data-accepted-limitation]")
            for index in range(accepted.count()):
                accepted.nth(index).check()
            stale_confirmation.get_by_role("button", name="Confirmar fatura").click()
            expect(stale_confirmation.locator("[data-status]")).to_contain_text("dataset_revision_conflict")

            page.reload()
            page.get_by_text("Corrigir campos", exact=True).click()
            review = page.locator('form[data-api-kind="review"]')
            invoice_number = page.locator('fieldset').filter(
                has=page.locator('[data-field-path][value="header.invoice_number"]'))
            invoice_number.locator("[data-field-edit]").check()
            invoice_number.locator("[data-field-value]").fill("SYNTHETIC-001")
            invoice_number.locator("[data-field-state]").select_option("confirmed")
            review.locator('[name="reason_code"]').fill("browser_invoice_number")
            review.get_by_role("button", name="Salvar correções selecionadas").click()
            expect(review.locator("[data-status]")).to_contain_text("Operação registrada")

            page.reload()
            page.get_by_text("Corrigir campos", exact=True).click()
            review = page.locator('form[data-api-kind="review"]')
            invoice_number = page.locator('fieldset').filter(
                has=page.locator('[data-field-path][value="header.invoice_number"]'))
            expect(invoice_number.locator("[data-field-value]")).to_have_value("SYNTHETIC-001")
            invoice_number.locator("[data-field-edit]").check()
            invoice_number.locator("[data-field-state]").select_option("missing")
            review.locator('[name="reason_code"]').fill("browser_mark_missing")
            review.get_by_role("button", name="Salvar correções selecionadas").click()
            expect(review.locator("[data-status]")).to_contain_text("Operação registrada")
            page.reload()
            invoice_number = page.locator('fieldset').filter(
                has=page.locator('[data-field-path][value="header.invoice_number"]'))
            expect(invoice_number.locator("[data-field-value]")).to_have_value("")

            page.reload()
            confirmation = page.locator('form[data-api-kind="confirmation"]')
            confirmation.locator('[name="billing_coverage_confirmed"]').check()
            accepted = confirmation.locator("[data-accepted-limitation]")
            for index in range(accepted.count()):
                accepted.nth(index).check()
            confirmation.get_by_role("button", name="Confirmar fatura").click()
            expect(confirmation.locator("[data-status]")).to_contain_text("Operação registrada")

            page.reload()
            selection = page.locator('form[data-api-kind="selection"]')
            choices = selection.locator("[data-included-invoice]")
            selection.locator("[data-selection-relationship]").select_option("distinct_periods")
            assert choices.count() == 2
            for index in range(choices.count()):
                expect(choices.nth(index)).to_be_checked()
                expect(choices.nth(index)).to_be_disabled()
            selection.locator("[data-selection-relationship]").select_option("replacement")
            for index in range(choices.count()):
                expect(choices.nth(index)).not_to_be_checked()
                expect(choices.nth(index)).to_be_enabled()
            selection.locator(f'[data-included-invoice][value="{first}"]').check()
            selection.get_by_role("button", name="Salvar escolha do conjunto").click()
            expect(selection.locator("[data-status]")).to_contain_text("Operação registrada")

            readiness = page.evaluate("""async (simulationId) =>
              window.EcoWattHTTP.request(`/api/v1/simulations/${simulationId}/invoice-readiness`)""",
              str(sim["id"]))
            assert readiness["ready_for_calculation"] is True
            assert [item["invoice_id"] for item in readiness["invoices"] if item["included"]] == [str(first)]
            assert errors == []
        finally:
            browser.close()
