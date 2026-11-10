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
