"""Revisão e reconciliação usam exclusivamente fixtures inventadas."""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest
from sqlalchemy import event, select

from ecowatt.db.invoices import FieldDependency, FieldProvenance, Invoice, InvoiceItem, InvoiceValidation
from ecowatt.db.models import Simulation, User
from ecowatt.db.session import transaction
from ecowatt.errors import DomainError
from ecowatt.services.invoice_review import current_fields, review_invoice
from ecowatt.services.invoice_storage import finish_normalized
from ecowatt.services.invoice_validation import financial_checks
from ecowatt.synthetic_invoice import field
from test_invoice_storage import reserved


def published(environment, derived=False):
    engine, sim, task, lease, result = reserved(environment)
    payload = result.model_dump()
    if derived:
        payload["header"]["known_components_total"] = field("18.76", "BRL", origin="derived",
            rule_version="synthetic-sum-v1", inputs=("items.line-1.amount", "items.line-2.amount"))
        payload["header"]["residual"] = field("1.23", "BRL", origin="derived",
            rule_version="synthetic-residual-v1", inputs=("header.known_components_total", "header.invoice_total"))
    invoice_id = finish_normalized(engine, task, lease, payload)
    return engine, sim, invoice_id


def command(path="header.invoice_total", value="18.76", unit="BRL", **kwargs):
    return dict(expected_revision=1, expected_dataset_revision=2, expected_invoice_revision=1,
        reason_code="synthetic_correction", edits=[dict(path=path, expected_version=1,
        field=field(value, unit, **kwargs))])


def url(sim, invoice_id):
    return f"/api/v1/simulations/{sim['id']}/invoices/{invoice_id}/reviews"


def post(client, path, payload, key="review-key-001"):
    return client.request("POST", path, json=payload, headers={"Idempotency-Key": key})


def test_atomic_versions_transitive_invalidation_and_historical_edges(environment):
    engine, sim, invoice_id = published(environment, derived=True)
    client = environment.client().login()
    with transaction(engine) as db:
        old = current_fields(db, invoice_id)
        path = next(path for path in old if path.startswith("items.") and path.endswith(".amount") and old[path].value == "19.99")
    payload = command(path, "20", "BRL")
    response = post(client, url(sim, invoice_id), payload)
    assert response.status_code == 200, response.text
    assert response.json()["invalidated_paths"] == ["header.known_components_total", "header.residual"]
    with transaction(engine) as db:
        current = current_fields(db, invoice_id)
        invoice = db.get(Invoice, invoice_id)
        assert invoice.revision == 2 and invoice.dataset_revision == 3 and invoice.status == "needs_review"
        assert invoice.known_components_total is None and invoice.residual is None
        assert db.get(Simulation, sim["id"]).revision == 1
        for dependent in ("header.known_components_total", "header.residual"):
            assert current[dependent].state == "missing" and current[dependent].version == 2
            assert current[dependent].reason_code == "dependency_changed"
            assert db.get(FieldProvenance, old[dependent].id).value == old[dependent].value
            assert list(db.scalars(select(FieldDependency).where(FieldDependency.field_id == old[dependent].id)))
        assert current[path].value == "20" and current[path].actor_id == sim["owner_id"]
        assert db.get(FieldProvenance, old[path].id).value == "19.99"
    # Um segundo comando pode substituir a invalidação, com referências atuais concretas.
    with transaction(engine) as db:
        current = current_fields(db, invoice_id)
        sources = [row.id for path, row in current.items() if path.startswith("items.") and path.endswith(".amount")]
    replacement = command("header.known_components_total", "18.77", origin="derived", rule_version="sum-v2", inputs=sources)
    replacement.update(expected_dataset_revision=3, expected_invoice_revision=2)
    replacement["edits"][0]["expected_version"] = 2
    assert post(client, url(sim, invoice_id), replacement, "review-key-002").status_code == 200


def test_retry_is_historical_receipt_and_conflicting_content_rejected(environment):
    engine, sim, invoice_id = published(environment)
    client = environment.client().login()
    path = url(sim, invoice_id)
    payload = command()
    first = post(client, path, payload)
    assert first.status_code == 200, first.text
    second = command("header.amount_payable", "25")
    second.update(expected_dataset_revision=3, expected_invoice_revision=2)
    assert post(client, path, second, "review-key-002").status_code == 200
    assert post(client, path, payload).json() == first.json()
    payload["edits"][0]["field"]["value"] = "18.77"
    assert post(client, path, payload).json()["code"] == "idempotency_conflict"
    with transaction(engine) as db:
        assert db.get(Simulation, sim["id"]).dataset_revision == 4
        assert db.get(Invoice, invoice_id).invoice_total == Decimal("18.76")


@pytest.mark.parametrize("mode", ["float", "nan", "scale", "unknown", "identity", "cycle", "version", "dataset", "invoice", "unit_revision", "duplicate", "owner", "reason"])
def test_invalid_review_never_changes_values(environment, mode):
    engine, sim, invoice_id = published(environment)
    client = environment.client().login()
    payload = command()
    edit = payload["edits"][0]
    if mode in ("float", "nan", "scale"):
        edit["field"]["value"] = {"float": 1.2, "nan": "NaN", "scale": "1.00000000001"}[mode]
    elif mode == "unknown":
        edit["path"] = "header.not_a_field"
    elif mode == "identity":
        edit.update(path="header.consumer_unit_id", field=field("1"))
    elif mode == "cycle":
        edit.update(path="header.cycle_start", field=field("2026-02-02"))
    elif mode == "version":
        edit["expected_version"] = 2
    elif mode in ("dataset", "invoice", "unit_revision"):
        payload[{"dataset": "expected_dataset_revision", "invoice": "expected_invoice_revision", "unit_revision": "expected_revision"}[mode]] = 99
    elif mode == "duplicate":
        payload["edits"].append(edit.copy())
    elif mode == "owner":
        payload["owner_id"] = sim["owner_id"]
    else:
        payload["reason_code"] = ""
    assert post(client, url(sim, invoice_id), payload).status_code in (409, 422)
    with transaction(engine) as db:
        assert db.get(Invoice, invoice_id).revision == 1
        assert db.get(Simulation, sim["id"]).dataset_revision == 2
        assert current_fields(db, invoice_id)["header.invoice_total"].version == 1


def test_rollback_after_versions_validation_and_counters(environment):
    engine, sim, invoice_id = published(environment, derived=True)
    def fail(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO audit_events"):
            raise RuntimeError("synthetic rollback")
    event.listen(engine, "after_cursor_execute", fail)
    try:
        with pytest.raises(RuntimeError):
            with transaction(engine, write=True) as db:
                review_invoice(db, db.get(User, sim["owner_id"]), sim["id"], invoice_id, "review-key", command())
    finally:
        event.remove(engine, "after_cursor_execute", fail)
    with transaction(engine) as db:
        assert db.get(Invoice, invoice_id).revision == 1
        assert db.get(Simulation, sim["id"]).dataset_revision == 2
        assert set(row.version for row in db.scalars(select(FieldProvenance))) == {1}
        assert len(list(db.scalars(select(InvoiceValidation)))) == 1


def test_concurrent_same_key_once_and_different_keys_conflict(environment):
    engine, sim, invoice_id = published(environment)
    def run(key):
        try:
            with transaction(engine, write=True) as db:
                return review_invoice(db, db.get(User, sim["owner_id"]), sim["id"], invoice_id, key, command())
        except DomainError as exc:
            return exc.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, ["same-key", "same-key"]))
    assert results[0] == results[1] and results[0]["dataset_revision"] == 3
    assert run("different-key") == "dataset_revision_conflict"


@pytest.mark.parametrize("difference,result", [("0.99", "pass"), ("-0.99", "pass"), ("0.9900000001", "blocking"), ("0", "pass")])
def test_financial_item_tolerance_exact_boundary(environment, difference, result):
    engine, sim, invoice_id = published(environment)
    with transaction(engine, write=True) as db:
        item = db.scalar(select(InvoiceItem).where(InvoiceItem.position == 1))
        item.amount = Decimal("19.99") + Decimal(difference)
        db.flush()
        check = next(c for c in financial_checks(db, db.get(Invoice, invoice_id)) if c["code"] == "item_product")
        assert check["result"] == result and check["difference"] == Decimal(difference)
        assert check["expected"] == Decimal("19.99")


def test_readiness_separates_residual_from_payable_and_monetary_only(environment):
    engine, sim, invoice_id = published(environment)
    client = environment.client().login()
    response = post(client, url(sim, invoice_id), command())
    assert response.status_code == 200, response.text
    output = client.request("GET", f"/api/v1/simulations/{sim['id']}/invoice-readiness")
    assert output.status_code == 200, output.text
    data = output.json()
    assert data["ready_for_calculation"] is False and data["dataset_revision"] == 3
    checks = {c["code"]: c for c in data["invoices"][0]["checks"]}
    assert checks["billing_residual"]["result"] == "pass"
    assert Decimal(checks["billing_residual"]["difference"]) == 0
    assert checks["payable_information"]["result"] == checks["product_unavailable"]["result"] == "warning"
    assert "financial_review_required" not in data["reasons"]
    assert "confirmation_workflow_pending" in data["reasons"]


def test_auth_csrf_admin_authorship_and_removed_replay(environment):
    engine, sim, invoice_id = published(environment)
    path = url(sim, invoice_id)
    admin = environment.client().login("admin@ecowatt.test")
    client = environment.client().login()
    assert client.request("POST", path, json=command(), headers={"Idempotency-Key": "review-key", "Origin": "https://invalid.test"}).status_code == 403
    assert client.request("POST", path, json=command(), headers={"Idempotency-Key": "review-key", "X-CSRF-Token": ""}).status_code == 403
    assert environment.client().request("POST", path, json=command(), headers={"Idempotency-Key": "review-key"}).status_code == 401
    from test_simulations import create
    private = create(admin).json()
    assert post(client, url(private, invoice_id), command()).status_code == 404
    assert client.request("GET", f"/api/v1/simulations/{private['id']}/invoice-readiness").status_code == 404
    assert post(admin, path, command()).status_code == 200
    with transaction(engine) as db:
        assert current_fields(db, invoice_id)["header.invoice_total"].actor_id == db.scalar(select(User.id).where(User.role == "admin"))
        assert db.get(Simulation, sim["id"]).owner_id == sim["owner_id"]
    assert client.request("DELETE", path.removesuffix("/reviews"), json=dict(confirm=True, expected_revision=1, expected_dataset_revision=3)).status_code == 204
    assert post(admin, path, command()).status_code == 404


@pytest.mark.parametrize("mode", ["old", "foreign", "self", "cycle", "changed_input", "duplicate"])
def test_dependencies_reject_stale_foreign_self_cycles_and_same_batch(environment, mode):
    engine, sim, invoice_id = published(environment, derived=True)
    client = environment.client().login()
    with transaction(engine) as db:
        latest = current_fields(db, invoice_id)
        source = latest["header.invoice_total"].id
        target = "header.known_components_total"
        if mode == "foreign":
            source = "not-a-provenance-id"
        elif mode == "self":
            source = latest[target].id
        elif mode == "cycle":
            source = latest["header.residual"].id
    payload = command(target, "18.76", origin="derived", rule_version="sum-v2", inputs=[source])
    if mode == "duplicate":
        payload["edits"][0]["field"]["inputs"].append(source)
    if mode == "changed_input":
        payload["edits"].append(command()["edits"][0])
    elif mode == "old":
        assert post(client, url(sim, invoice_id), command(), "first-review-key").status_code == 200
        payload.update(expected_dataset_revision=3, expected_invoice_revision=2)
    response = post(client, url(sim, invoice_id), payload)
    assert response.status_code == (422 if mode == "duplicate" else 409), response.text
    assert response.json()["code"] == ("invalid_invoice_review" if mode == "duplicate" else "stale_field_dependency")


def test_two_distinct_edits_and_edit_remove_race(environment):
    engine, sim, invoice_id = published(environment)
    client = environment.client().login()
    payload = command()
    payload["edits"].append(command("header.amount_payable", "22")["edits"][0])
    assert post(client, url(sim, invoice_id), payload).status_code == 200
    with transaction(engine) as db:
        invoice = db.get(Invoice, invoice_id)
        assert invoice.revision == 2 and invoice.amount_payable == Decimal("22")
    from ecowatt.schemas import InvoiceDeleteInput
    from ecowatt.services.invoices import remove_invoice
    def run(operation):
        try:
            with transaction(engine, write=True) as db:
                actor = db.get(User, sim["owner_id"])
                if operation == "remove":
                    remove_invoice(db, actor, sim["id"], invoice_id,
                        InvoiceDeleteInput(confirm=True, expected_revision=1, expected_dataset_revision=3))
                else:
                    next_payload = command()
                    next_payload.update(expected_dataset_revision=3, expected_invoice_revision=2)
                    next_payload["edits"][0]["expected_version"] = 2
                    review_invoice(db, actor, sim["id"], invoice_id, "racing-key", next_payload)
            return "ok"
        except DomainError as exc:
            return exc.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, ["remove", "edit"]))
    assert results.count("ok") == 1
    assert set(results) <= {"ok", "not_found", "dataset_revision_conflict"}


def test_readiness_detects_active_and_expired_admissions(environment):
    from ecowatt.services import admission, tasks
    from ecowatt.services.synthetic_worker import Sample
    engine, sim, invoice_id = published(environment)
    sample, inspection = Sample("00001", serial=1).materialize()
    task = admission.admit_synthetic(engine, sim["owner_id"], sim["id"], 1,
        "another-admission", inspection, action="read_invoice")
    client = environment.client().login()
    path = f"/api/v1/simulations/{sim['id']}/invoice-readiness"
    assert "processing_pending" in client.request("GET", path).json()["reasons"]
    lease = tasks.claim(engine, task, "synthetic-review-test")
    from ecowatt.db.models import SimulationTask, now
    with transaction(engine, write=True) as db:
        db.get(SimulationTask, task).lease_expires_at = now() - 1
    tasks.expire(engine)
    assert "admission_unresolved" in client.request("GET", path).json()["reasons"]


def test_financial_precision_range_and_residual_not_tolerated(environment):
    engine, sim, invoice_id = published(environment)
    with transaction(engine, write=True) as db:
        invoice = db.get(Invoice, invoice_id)
        invoice.invoice_total = Decimal("18.77")
        item = db.scalar(select(InvoiceItem).where(InvoiceItem.position == 1))
        db.flush()
        residual = next(c for c in financial_checks(db, invoice) if c["code"] == "billing_residual")
        assert residual["difference"] == Decimal("0.01") and residual["result"] == "blocking"
        item.quantity = Decimal("99999999999999999999")
        item.effective_price = Decimal("99999999999999999999")
        db.flush()
        check = next(c for c in financial_checks(db, invoice) if c["code"] == "validation_numeric_range")
        assert check["result"] == "blocking" and check["expected"] is None


def test_review_preserves_pending_publication_and_original_replay(environment):
    from ecowatt.services import admission, tasks
    from ecowatt.services.synthetic_worker import Sample
    from ecowatt.synthetic_invoice import synthetic_result
    engine, sim, task, lease, result = reserved(environment)
    invoice_id = finish_normalized(engine, task, lease, result)
    sample, inspection = Sample("00001", serial=1).materialize()
    second = admission.admit_synthetic(engine, sim["owner_id"], sim["id"], 1,
        "second-publication", inspection, action="read_invoice")
    client = environment.client().login()
    assert post(client, url(sim, invoice_id), command()).status_code == 200
    assert finish_normalized(engine, task, lease, result) == invoice_id
    next_lease = tasks.claim(engine, second, "review-regression")
    next_result = synthetic_result(inspection.source_hash, len(sample), 1, "00001", 1)
    assert finish_normalized(engine, second, next_lease, next_result) != invoice_id
    with transaction(engine) as db:
        assert db.get(Invoice, invoice_id).invoice_total == Decimal("18.76")
        assert db.get(Invoice, invoice_id).revision == 2
        assert db.get(Simulation, sim["id"]).revision == 1
        assert db.get(Simulation, sim["id"]).dataset_revision == 4


def test_item_unit_changes_require_coherent_batch(environment):
    engine, sim, invoice_id = published(environment)
    client = environment.client().login()
    with transaction(engine) as db:
        item_id = db.scalar(select(InvoiceItem.id).where(InvoiceItem.position == 1))
    payload = command(f"items.{item_id}.quantity_unit", "MWh", None)
    assert post(client, url(sim, invoice_id), payload).status_code == 422
    payload["edits"].extend([
        command(f"items.{item_id}.quantity", "0.01", "MWh")["edits"][0],
        command(f"items.{item_id}.effective_price", "1999", "BRL/MWh")["edits"][0]])
    response = post(client, url(sim, invoice_id), payload)
    assert response.status_code == 200, response.text
    with transaction(engine) as db:
        check = next(c for c in financial_checks(db, db.get(Invoice, invoice_id)) if c["code"] == "item_product")
        assert check["difference"] == 0 and check["result"] == "pass"


def test_cycle_batch_flushes_final_state_without_invalid_intermediate(environment):
    engine, sim, invoice_id = published(environment)
    client = environment.client().login()
    payload = command("header.cycle_start", "2026-02-01", None)
    payload["edits"].append(command("header.cycle_end", "2026-02-28", None)["edits"][0])
    response = post(client, url(sim, invoice_id), payload)
    assert response.status_code == 200, response.text
    with transaction(engine) as db:
        invoice = db.get(Invoice, invoice_id)
        assert str(invoice.cycle_start) == "2026-02-01" and str(invoice.cycle_end) == "2026-02-28"
        assert invoice.revision == 2
