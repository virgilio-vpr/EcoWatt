"""Confirmação/seleção exclusivamente de dados inventados, sem arquivos."""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import event, func, select

from ecowatt.db.invoices import (FieldProvenance, Invoice, InvoiceConfirmation, InvoiceItem, InvoiceSelection)
from ecowatt.db.models import Simulation, User
from ecowatt.db.session import transaction
from ecowatt.errors import DomainError
from ecowatt.schemas import InvoiceDeleteInput
from ecowatt.services import admission, tasks
from ecowatt.services.invoice_confirmation import confirm_invoice, require_ready_dataset, select_invoices
from ecowatt.services.invoice_storage import finish_normalized
from ecowatt.services.invoices import remove_invoice
from ecowatt.services.synthetic_worker import Sample
from ecowatt.synthetic_invoice import field, synthetic_result
from test_invoice_storage import reserved


def complete(result):
    data = result.model_dump()
    data["header"].update(printed_address_line=field("Rua Sintética 1"), printed_city=field("Teste"),
        printed_state=field("SP"), invoice_total=field("18.76", "BRL"), market=field("captive"))
    return data


def published(environment, change=None):
    engine, sim, task, lease, result = reserved(environment)
    data = complete(result)
    if change:
        change(data)
    invoice_id = finish_normalized(engine, task, lease, data)
    return engine, sim, invoice_id


def another(engine, sim, serial=1, change=None):
    sample, inspection = Sample("00001", serial=serial).materialize()
    task = admission.admit_synthetic(engine, sim["owner_id"], sim["id"], 1,
        f"confirmation-admission-{serial}", inspection, action="read_invoice")
    lease = tasks.claim(engine, task, "confirmation-fixture")
    data = complete(synthetic_result(inspection.source_hash, len(sample), 1, "00001", serial))
    # Mesmo ciclo/competência sintéticos, hash distinto.
    data["header"]["competence"] = field("2026-01")
    if change:
        change(data)
    return finish_normalized(engine, task, lease, data)


def readiness(client, sim):
    response = client.request("GET", f"/api/v1/simulations/{sim['id']}/invoice-readiness")
    assert response.status_code == 200, response.text
    return response.json()


def confirm_payload(data, invoice_id):
    entry = next(i for i in data["invoices"] if i["invoice_id"] == invoice_id)
    return dict(expected_revision=data["unit_revision"], expected_dataset_revision=data["dataset_revision"],
        expected_invoice_revision=entry["revision"], reason_code="synthetic_review_complete",
        billing_coverage_confirmed=True, accepted_limitations=entry["limitations"])


def confirm(client, sim, invoice_id, key="confirm-key-001", payload=None):
    return client.request("POST", f"/api/v1/simulations/{sim['id']}/invoices/{invoice_id}/confirmations",
        json=payload or confirm_payload(readiness(client, sim), invoice_id), headers={"Idempotency-Key": key})


def selection_payload(data, included, relationship="replacement"):
    return dict(expected_revision=data["unit_revision"], expected_dataset_revision=data["dataset_revision"],
        reason_code="synthetic_choice", relationship=relationship,
        member_versions=data["duplicate_groups"][0]["member_versions"], included_ids=included)


def choose(client, sim, payload, key="selection-key-001"):
    return client.request("POST", f"/api/v1/simulations/{sim['id']}/invoice-selections",
        json=payload, headers={"Idempotency-Key": key})


def test_first_confirmed_invoice_ready_snapshot_and_guard(environment):
    engine, sim, invoice_id = published(environment)
    client = environment.client().login()
    before = readiness(client, sim)
    assert not before["ready_for_calculation"] and before["invoices"][0]["pending_fields"] == []
    payload = confirm_payload(before, invoice_id)
    response = confirm(client, sim, invoice_id, payload=payload)
    assert response.status_code == 200, response.text
    after = readiness(client, sim)
    assert after["ready_for_calculation"] and after["reasons"] == [] and after["dataset_revision"] == 3
    assert confirm(client, sim, invoice_id, payload=payload).json() == response.json()
    with transaction(engine, write=True) as db:
        receipt = db.get(InvoiceConfirmation, response.json()["confirmation_id"])
        assert receipt.actor_id == sim["owner_id"] and receipt.unit_revision == receipt.invoice_revision == 1
        assert len(receipt.field_versions) == db.scalar(select(func.count()).select_from(FieldProvenance))
        assert require_ready_dataset(db, db.get(User, sim["owner_id"]), sim["id"], 1, 3) == [invoice_id]
        assert db.get(Invoice, invoice_id).coverage == "partial"  # Atestação humana é separada.
        credit = db.scalar(select(InvoiceItem).where(InvoiceItem.position == 2))
        assert credit.quantity is None and credit.effective_price is None


@pytest.mark.parametrize("missing", ["holder_name", "consumer_unit_id", "printed_address_line", "competence", "cycle_start", "subgroup", "modality", "customer_class"])
def test_critical_unknown_never_ready(environment, missing):
    engine, sim, invoice_id = published(environment, lambda data: data["header"].pop(missing))
    client = environment.client().login()
    data = readiness(client, sim)
    assert "header." + missing in data["invoices"][0]["pending_fields"]
    response = confirm(client, sim, invoice_id)
    assert response.status_code == 409 and response.json()["code"] == "invoice_confirmation_blocked"
    with transaction(engine) as db:
        assert db.scalar(select(func.count()).select_from(InvoiceConfirmation)) == 0


@pytest.mark.parametrize("mode", ["false", "integer", "extra_owner", "missing_ack", "extra_ack", "invoice_revision", "dataset_revision"])
def test_confirmation_strict_preconditions(environment, mode):
    engine, sim, invoice_id = published(environment)
    client = environment.client().login()
    payload = confirm_payload(readiness(client, sim), invoice_id)
    if mode == "false":
        payload["billing_coverage_confirmed"] = False
    elif mode == "integer":
        payload["billing_coverage_confirmed"] = 1
    elif mode == "extra_owner":
        payload["owner_id"] = sim["owner_id"]
    elif mode == "missing_ack":
        del payload["billing_coverage_confirmed"]
    elif mode == "extra_ack":
        payload["accepted_limitations"] = ["market_unconfirmed"]
    else:
        payload["expected_" + mode] = 99
    assert confirm(client, sim, invoice_id, payload=payload).status_code in (409, 422)


def test_module_limitations_acknowledged_without_inventing_demands(environment):
    def change(data):
        data["header"].pop("market")
        for measurement in data["measurements"]:
            measurement["fields"] = {}
    engine, sim, invoice_id = published(environment, change)
    client = environment.client().login()
    data = readiness(client, sim)
    assert set(data["invoices"][0]["limitations"]) == {"market_unconfirmed", "contracted_demand_incomplete", "measured_demand_incomplete"}
    payload = confirm_payload(data, invoice_id)
    payload["accepted_limitations"] = []
    assert confirm(client, sim, invoice_id, payload=payload).json()["code"] == "invoice_limitations_ack_required"
    assert confirm(client, sim, invoice_id).status_code == 200
    assert readiness(client, sim)["ready_for_calculation"]


def test_revision_and_unit_changes_invalidate_confirmation_and_replay_cannot_restore(environment):
    engine, sim, invoice_id = published(environment)
    client = environment.client().login()
    original = confirm_payload(readiness(client, sim), invoice_id)
    receipt = confirm(client, sim, invoice_id, payload=original).json()
    from test_invoice_review import command as edit_payload
    edit = edit_payload("header.amount_payable", "25")
    edit["expected_dataset_revision"] = 3
    path = f"/api/v1/simulations/{sim['id']}/invoices/{invoice_id}"
    assert client.request("POST", path + "/reviews", json=edit, headers={"Idempotency-Key": "edit-after-confirm"}).status_code == 200
    assert not readiness(client, sim)["ready_for_calculation"]
    assert confirm(client, sim, invoice_id, payload=original).json() == receipt
    assert not readiness(client, sim)["ready_for_calculation"]
    assert confirm(client, sim, invoice_id, key="confirm-key-002").status_code == 200
    with transaction(engine) as db:
        distributor = db.get(Simulation, sim["id"]).distributor_id
    unit = dict(expected_revision=1, distributor_id=distributor, unit_identifier="00001", holder_name="Fixture",
        address_line="Rua 2", city="Teste", state="SP", postal_code="00000")
    assert client.request("PATCH", f"/api/v1/simulations/{sim['id']}/unit", json=unit).status_code == 200
    assert not readiness(client, sim)["ready_for_calculation"]
    with transaction(engine) as db:
        assert db.get(Invoice, invoice_id).status == "needs_review"
        assert db.scalar(select(func.count()).select_from(InvoiceConfirmation)) == 2


def test_duplicates_choose_one_preserve_other_and_new_member_invalidates(environment):
    engine, sim, first = published(environment)
    second = another(engine, sim)
    client = environment.client().login()
    assert confirm(client, sim, first).status_code == 200
    data = readiness(client, sim)
    assert "duplicate_resolution_required" in data["reasons"]
    payload = selection_payload(data, [first])
    receipt = choose(client, sim, payload)
    assert receipt.status_code == 200, receipt.text
    assert choose(client, sim, payload).json() == receipt.json()
    data = readiness(client, sim)
    assert data["ready_for_calculation"]
    assert {i["invoice_id"] for i in data["invoices"] if i["included"]} == {first}
    with transaction(engine) as db:
        assert db.get(Invoice, second) is not None  # Não apaga a versão descartada.
    another(engine, sim, serial=2)
    assert "duplicate_resolution_required" in readiness(client, sim)["reasons"]
    assert choose(client, sim, payload, "new-selection-key").status_code == 409


def test_removing_preferred_does_not_silently_include_old_alternative(environment):
    engine, sim, first = published(environment)
    second = another(engine, sim)
    client = environment.client().login()
    assert confirm(client, sim, second).status_code == 200
    assert choose(client, sim, selection_payload(readiness(client, sim), [first])).status_code == 200
    data = readiness(client, sim)
    assert client.request("DELETE", f"/api/v1/simulations/{sim['id']}/invoices/{first}",
        json=dict(confirm=True, expected_revision=1, expected_dataset_revision=data["dataset_revision"])).status_code == 204
    data = readiness(client, sim)
    assert not data["ready_for_calculation"] and len(data["duplicate_groups"][0]["member_versions"]) == 1
    assert choose(client, sim, selection_payload(data, [second]), "select-survivor").status_code == 200
    assert readiness(client, sim)["ready_for_calculation"]


@pytest.mark.parametrize("mode", ["overlap", "distinct", "complement", "same_number"])
def test_explicit_distinct_periods_and_complement_safety(environment, mode):
    def first_change(data):
        if mode == "same_number":
            data["header"]["invoice_number"] = field("SYNTHETIC-123")
    engine, sim, first = published(environment, first_change)
    def second_change(data):
        if mode in ("distinct", "same_number"):
            data["header"]["cycle_start"] = field("2026-02-01")
            data["header"]["cycle_end"] = field("2026-02-28")
            data["header"]["cycle_days"] = field(27)
        if mode == "same_number":
            data["header"]["invoice_number"] = field("SYNTHETIC-123")
    second = another(engine, sim, change=second_change)
    client = environment.client().login()
    assert confirm(client, sim, first).status_code == 200
    assert confirm(client, sim, second).status_code == 200
    relationship = "complement" if mode == "complement" else "distinct_periods"
    response = choose(client, sim, selection_payload(readiness(client, sim), [first, second], relationship))
    if mode in ("overlap", "same_number"):
        assert response.status_code == 409
    else:
        assert response.status_code == 200, response.text
        data = readiness(client, sim)
        assert data["ready_for_calculation"] is (mode == "distinct")
        if mode == "complement":
            assert "complement_consolidation_required" in data["reasons"]


def test_concurrent_confirmation_same_key_and_selection_revision_conflict(environment):
    engine, sim, invoice_id = published(environment)
    client = environment.client().login()
    payload = confirm_payload(readiness(client, sim), invoice_id)
    def run(key):
        try:
            with transaction(engine, write=True) as db:
                return confirm_invoice(db, db.get(User, sim["owner_id"]), sim["id"], invoice_id, key, payload)
        except DomainError as exc:
            return exc.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(pool.map(run, ["same-key", "same-key"]))
    assert receipts[0] == receipts[1] and run("other-key") == "dataset_revision_conflict"


@pytest.mark.parametrize("operation", ["confirm", "select"])
def test_rollback_includes_snapshot_status_revision_and_receipt(environment, operation):
    engine, sim, first = published(environment)
    client = environment.client().login()
    if operation == "select":
        another(engine, sim)
    data = readiness(client, sim)
    def fail(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO audit_events"):
            raise RuntimeError("synthetic rollback")
    event.listen(engine, "after_cursor_execute", fail)
    try:
        with pytest.raises(RuntimeError):
            with transaction(engine, write=True) as db:
                actor = db.get(User, sim["owner_id"])
                if operation == "confirm":
                    confirm_invoice(db, actor, sim["id"], first, "key-rollback", confirm_payload(data, first))
                else:
                    select_invoices(db, actor, sim["id"], "key-rollback", selection_payload(data, [first]))
    finally:
        event.remove(engine, "after_cursor_execute", fail)
    with transaction(engine) as db:
        assert db.get(Simulation, sim["id"]).dataset_revision == data["dataset_revision"]
        assert db.get(Invoice, first).status == "needs_review"
        assert db.scalar(select(func.count()).select_from(InvoiceConfirmation)) == 0
        assert db.scalar(select(func.count()).select_from(InvoiceSelection)) == 0


def test_authorization_csrf_admin_authorship_and_tombstone(environment):
    engine, sim, first = published(environment)
    client = environment.client().login()
    admin = environment.client().login("admin@ecowatt.test")
    from test_simulations import create
    other = create(admin).json()
    assert confirm(client, other, first, payload=confirm_payload(readiness(client, sim), first)).status_code == 404
    assert choose(client, other, dict(expected_revision=1, expected_dataset_revision=1, reason_code="test",
        relationship="duplicate", member_versions={first: 1}, included_ids=[first])).status_code == 404
    path = f"/api/v1/simulations/{sim['id']}/invoices/{first}/confirmations"
    payload = confirm_payload(readiness(client, sim), first)
    assert client.request("POST", path, json=payload, headers={"Idempotency-Key": "csrf-key", "X-CSRF-Token": ""}).status_code == 403
    response = confirm(admin, sim, first, payload=payload)
    assert response.status_code == 200
    with transaction(engine) as db:
        assert db.get(InvoiceConfirmation, response.json()["confirmation_id"]).actor_id == db.scalar(select(User.id).where(User.role == "admin"))
        assert db.get(Simulation, sim["id"]).owner_id == sim["owner_id"]
    assert client.request("DELETE", f"/api/v1/simulations/{sim['id']}", json=dict(confirm=True, expected_revision=1)).status_code == 204
    assert confirm(admin, sim, first, payload=payload).status_code == 404
    with transaction(engine) as db:
        assert db.scalar(select(func.count()).select_from(InvoiceConfirmation)) == 0


def test_migration_preserves_invoices_and_downgrade_loses_confirmations_only(environment):
    engine, sim, invoice_id = published(environment)
    client = environment.client().login()
    assert confirm(client, sim, invoice_id).status_code == 200
    cfg = Config("alembic.ini")
    cfg.attributes["settings"] = environment.settings
    command.check(cfg)
    command.downgrade(cfg, "0007_invoice_publications")
    command.upgrade(cfg, "head")
    command.check(cfg)
    assert not readiness(client, sim)["ready_for_calculation"]
    with transaction(engine) as db:
        assert db.get(Invoice, invoice_id).invoice_total == Decimal("18.76")
        assert db.scalar(select(func.count()).select_from(InvoiceConfirmation)) == 0
    with engine.connect() as conn:
        assert conn.exec_driver_sql("PRAGMA foreign_key_check").all() == []


def test_histories_authorship_and_selection_fingerprint_conflict(environment):
    engine, sim, first = published(environment)
    another(engine, sim)
    client = environment.client().login()
    assert confirm(client, sim, first).status_code == 200
    payload = selection_payload(readiness(client, sim), [first])
    response = choose(client, sim, payload)
    assert response.status_code == 200
    history = client.request("GET", f"/api/v1/simulations/{sim['id']}/invoice-selections?page_size=1").json()
    assert history["total"] == 1 and history["items"][0]["actor_id"] == sim["owner_id"]
    assert history["items"][0]["reason_code"] == "synthetic_choice"
    detail = client.request("GET", f"/api/v1/simulations/{sim['id']}/invoices/{first}").json()
    assert detail["confirmations"][0]["field_versions"] and detail["confirmations"][0]["actor_id"] == sim["owner_id"]
    payload["reason_code"] = "different_reason"
    assert choose(client, sim, payload).json()["code"] == "idempotency_conflict"


@pytest.mark.parametrize("state", ["queued", "running", "expired", "cancelled"])
def test_pending_or_lost_admission_blocks_confirmed_dataset(environment, state):
    from ecowatt.db.models import SimulationTask, now
    engine, sim, invoice_id = published(environment)
    client = environment.client().login()
    assert confirm(client, sim, invoice_id).status_code == 200
    sample, inspection = Sample("00001", serial=5).materialize()
    task = admission.admit_synthetic(engine, sim["owner_id"], sim["id"], 1,
        "unprocessed-admission", inspection, action="read_invoice")
    if state in ("running", "expired"):
        tasks.claim(engine, task, "test-pending")
    if state == "expired":
        with transaction(engine, write=True) as db:
            db.get(SimulationTask, task).lease_expires_at = now() - 1
        tasks.expire(engine)
    elif state == "cancelled":
        with transaction(engine, write=True) as db:
            tasks.cancel_tasks(db, sim["id"], "synthetic_cancel")
    data = readiness(client, sim)
    assert not data["ready_for_calculation"]
    assert ("processing_pending" if state in ("queued", "running") else "admission_unresolved") in data["reasons"]
    admission.remove_synthetic(engine, sim["owner_id"], sim["id"], 1, task)
    assert readiness(client, sim)["ready_for_calculation"]


def test_gaps_are_informative_and_no_twelve_invoice_requirement(environment):
    engine, sim, first = published(environment)
    def march(data):
        data["header"].update(competence=field("2026-03"), cycle_start=field("2026-03-01"),
            cycle_end=field("2026-03-31"))
    second = another(engine, sim, change=march)
    client = environment.client().login()
    assert confirm(client, sim, first).status_code == 200
    assert confirm(client, sim, second).status_code == 200
    data = readiness(client, sim)
    assert data["ready_for_calculation"] and data["missing_competences"] == ["2026-02"]


def test_estimated_data_preserved_and_ack_required(environment):
    def change(data):
        data["measurements"][0]["fields"]["active_energy"] = field("10", "kWh", state="estimated",
            hypothesis_code="synthetic_average", inputs=("items.line-1.quantity",))
    engine, sim, invoice_id = published(environment, change)
    client = environment.client().login()
    payload = confirm_payload(readiness(client, sim), invoice_id)
    assert "estimated_data" in payload["accepted_limitations"]
    assert confirm(client, sim, invoice_id, payload=payload).status_code == 200
    with transaction(engine) as db:
        row = db.scalar(select(FieldProvenance).where(FieldProvenance.state == "estimated"))
        assert row.value == "10" and row.version == 1 and row.hypothesis_code == "synthetic_average"


def test_guard_rejects_stale_dataset_and_empty_dataset(environment):
    from test_admission import setup
    engine, sim, _ = setup(environment)
    client = environment.client().login()
    assert "no_invoices" in readiness(client, sim)["reasons"]
    with transaction(engine, write=True) as db:
        with pytest.raises(DomainError) as error:
            require_ready_dataset(db, db.get(User, sim["owner_id"]), sim["id"], 1, 1)
        assert error.value.code == "dataset_not_ready"
        with pytest.raises(DomainError) as stale:
            require_ready_dataset(db, db.get(User, sim["owner_id"]), sim["id"], 1, 99)
        assert stale.value.code == "dataset_revision_conflict"


def test_concurrent_confirmation_and_removal_only_one_writes(environment):
    engine, sim, invoice_id = published(environment)
    client = environment.client().login()
    payload = confirm_payload(readiness(client, sim), invoice_id)
    def run(operation):
        try:
            with transaction(engine, write=True) as db:
                actor = db.get(User, sim["owner_id"])
                if operation == "confirm":
                    confirm_invoice(db, actor, sim["id"], invoice_id, "confirm-remove-key", payload)
                else:
                    remove_invoice(db, actor, sim["id"], invoice_id, InvoiceDeleteInput(
                        confirm=True, expected_revision=1, expected_dataset_revision=2))
            return "ok"
        except DomainError as exc:
            return exc.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, ["confirm", "remove"]))
    assert results.count("ok") == 1 and set(results) <= {"ok", "not_found", "dataset_revision_conflict"}


def test_optional_payable_outside_validation_memory_remains_informational(environment):
    def change(data):
        data["items"][1]["fields"]["amount"] = field("90000000000000000000", "BRL")
        data["header"]["invoice_total"] = field("90000000000000000019.99", "BRL")
        data["header"]["amount_payable"] = field("-90000000000000000000", "BRL")
    engine, sim, invoice_id = published(environment, change)
    client = environment.client().login()
    data = readiness(client, sim)
    assert any(c["code"] == "payable_numeric_range" and c["result"] == "warning" for c in data["invoices"][0]["checks"])
    assert confirm(client, sim, invoice_id).status_code == 200
    assert readiness(client, sim)["ready_for_calculation"]
