"""Resultado, grafo e API exclusivamente sintéticos; nenhum arquivo real."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from decimal import Decimal
from threading import Event

import pytest
from sqlalchemy import event, func, select

from ecowatt.db.admissions import InvoiceAdmission, InvoicePublication
from ecowatt.db.invoices import (FieldDependency, FieldProvenance, Invoice, InvoiceItem,
    InvoiceMarketEvidence, InvoiceMeasurement, InvoiceValidation)
from ecowatt.db.models import Simulation, SimulationTask, User
from ecowatt.db.session import transaction
from ecowatt.errors import DomainError
from ecowatt.invoice_result import ExtractionResult
from ecowatt.schemas import InvoiceDeleteInput
from ecowatt.services import admission, tasks
from ecowatt.services.coordinator import Coordinator
from ecowatt.services.invoice_storage import finish_normalized, prepare_result
from ecowatt.services.invoices import remove_invoice
from ecowatt.services.synthetic_worker import Sample
from ecowatt.synthetic_invoice import field, synthetic_result
from test_admission import setup

GRAPH = (Invoice, InvoiceMeasurement, InvoiceItem, FieldProvenance, FieldDependency,
    InvoiceValidation, InvoiceMarketEvidence, InvoicePublication)


def reserved(environment, *, actor_id=None, key="normalized-key", serial=0):
    engine, sim, _ = setup(environment)
    sample, inspection = Sample("00001", serial=serial).materialize()
    result = synthetic_result(inspection.source_hash, len(sample), 1, "00001", serial)
    task = admission.admit_synthetic(engine, actor_id or sim["owner_id"], sim["id"], 1,
        key, inspection, action="read_invoice")
    lease = tasks.claim(engine, task, "normalized-fixture")
    return engine, sim, task, lease, result


def graph_counts(engine):
    with transaction(engine) as db:
        return [db.scalar(select(func.count()).select_from(model)) for model in GRAPH]


def test_atomic_graph_current_values_provenance_and_green_posts(environment):
    engine, sim, task, lease, result = reserved(environment)
    invoice_id = finish_normalized(engine, task, lease, result)
    with transaction(engine) as db:
        invoice = db.get(Invoice, invoice_id)
        assert invoice.status == "needs_review" and invoice.contract_version == "invoice-v0.3"
        assert invoice.created_by == sim["owner_id"]
        assert invoice.dataset_revision == db.get(Simulation, sim["id"]).dataset_revision == 2
        assert db.get(Simulation, sim["id"]).revision == 1
        assert invoice.invoice_total == Decimal("19.99") and invoice.amount_payable == Decimal("23.99")
        assert invoice.market == invoice.market_candidate == "unknown"
        assert db.get(SimulationTask, task).status == "finished"
        assert db.get(InvoicePublication, task).invoice_id == invoice.id
        measurements = {m.post: m for m in db.scalars(select(InvoiceMeasurement))}
        assert measurements["single"].contracted_demand == Decimal("150")
        assert measurements["peak"].contracted_demand is None
        assert measurements["peak"].measured_active_demand == Decimal("123.4567890123")
        assert measurements["off_peak"].measured_active_demand == Decimal("140")
        for row in db.scalars(select(FieldProvenance)):
            assert row.version == 1 and row.actor_id == sim["owner_id"] and row.origin == "user"
            if row.field_path.startswith("header."):
                current = getattr(invoice, row.field_path.split(".")[1])
                if isinstance(current, Decimal):
                    assert Decimal(row.value) == current
                elif row.state == "missing":
                    assert row.value is None and current in (None, "unknown")
        credit = db.scalar(select(InvoiceItem).where(InvoiceItem.position == 2))
        assert credit.amount == Decimal("-1.23") and credit.quantity is None and credit.effective_price is None
        assert db.scalar(select(InvoiceValidation.result)) == "blocking"
    with engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []


def test_concurrent_completion_replay_is_lease_and_content_bound(environment):
    engine, sim, task, lease, result = reserved(environment)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: finish_normalized(engine, task, lease, result), range(2)))
    assert results[0] == results[1]
    assert graph_counts(engine)[0] == 1
    with pytest.raises(DomainError) as error:
        finish_normalized(engine, task, "forged-lease", result)
    assert error.value.code == "task_unavailable"
    changed = result.model_dump()
    changed["header"]["holder_name"] = field("Outro titular sintético")
    with pytest.raises(DomainError) as error:
        finish_normalized(engine, task, lease, changed)
    assert error.value.code == "idempotency_conflict"
    with transaction(engine) as db:
        assert db.get(Simulation, sim["id"]).dataset_revision == 2


@pytest.mark.parametrize("field_name,value", [("quantity", 1.5), ("quantity", "NaN"),
    ("quantity", "1e2"), ("quantity", "-1"), ("quantity", "0.00000000001"),
    ("quantity", "100000000000000000000"), ("amount", "19,99")])
def test_decimal_contract_rejects_float_nonfinite_scale_and_overflow(environment, field_name, value):
    engine, sim, task, lease, result = reserved(environment)
    payload = result.model_dump()
    payload["items"][0]["fields"][field_name]["value"] = value
    with pytest.raises(DomainError) as error:
        finish_normalized(engine, task, lease, payload)
    assert error.value.code == "invalid_extraction_result"
    assert graph_counts(engine) == [0] * len(GRAPH)
    with transaction(engine) as db:
        assert db.get(SimulationTask, task).status == "running"


@pytest.mark.parametrize("location", ["extra", "header", "item", "origin", "unit", "cycle", "ref", "duplicate-post"])
def test_closed_contract_and_structural_consistency(location):
    payload = synthetic_result("a" * 64, 100, 1, "00001").model_dump()
    if location == "extra":
        payload["raw_text"] = "prohibited synthetic payload"
    elif location == "header":
        payload["header"]["raw_text"] = field("prohibited")
    elif location == "item":
        payload["items"][0]["fields"]["raw_text"] = field("prohibited")
    elif location == "origin":
        payload["header"]["holder_name"]["origin"] = "pdf_text"
    elif location == "unit":
        payload["items"][0]["fields"]["quantity"]["unit"] = "kW"
    elif location == "cycle":
        payload["header"]["cycle_end"]["value"] = "2025-01-01"
    elif location == "ref":
        payload["items"][0]["measurement_key"] = "absent"
    else:
        payload["measurements"][1]["post"] = "single"
    with pytest.raises(DomainError) as error:
        prepare_result(payload)
    assert error.value.code == "invalid_extraction_result"
    assert "prohibited" not in error.value.message


@pytest.mark.parametrize("mode", ["nonzero", "partial", "missing-value", "not-applicable", "estimated", "derived"])
def test_field_state_guarantees(mode):
    payload = synthetic_result("a" * 64, 100, 1, "00001").model_dump()
    target = payload["items"][0]["fields"]["amount"]
    if mode == "nonzero":
        target.update(state="zero_confirmed", coverage="complete")
    elif mode == "partial":
        target.update(state="zero_confirmed", value="0", coverage="partial")
    elif mode == "missing-value":
        target.update(value=None)
    elif mode == "not-applicable":
        target.update(state="not_applicable", value=None)
    elif mode == "estimated":
        target.update(state="estimated")
    else:
        target.update(origin="derived")
    with pytest.raises(DomainError):
        prepare_result(payload)


def test_dependencies_reference_concrete_versions_and_cycle_rejected(environment):
    engine, sim, task, lease, result = reserved(environment)
    payload = result.model_dump()
    payload["header"]["known_components_total"] = field("18.76", "BRL", origin="derived",
        rule_version="synthetic-sum-v1", inputs=("items.line-1.amount", "items.line-2.amount"))
    result = prepare_result(payload)
    invoice_id = finish_normalized(engine, task, lease, result)
    with transaction(engine) as db:
        output = db.scalar(select(FieldProvenance).where(FieldProvenance.field_path == "header.known_components_total"))
        inputs = list(db.scalars(select(FieldDependency).where(FieldDependency.field_id == output.id)))
        assert len(inputs) == 2 and output.value == "18.76"
        for edge in inputs:
            source = db.get(FieldProvenance, edge.input_id)
            assert source.invoice_id == invoice_id and source.version == 1
    payload["items"][0]["fields"]["amount"].update(origin="derived", rule_version="cycle-v1",
        inputs=("header.known_components_total",))
    with pytest.raises(DomainError):
        prepare_result(payload)
    payload["items"][0]["fields"]["amount"]["inputs"] = ("items.not-present.amount",)
    with pytest.raises(DomainError):
        prepare_result(payload)


def test_rollback_after_all_children_and_publication_flush(environment):
    engine, sim, task, lease, result = reserved(environment)
    def fail(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO invoice_publications"):
            raise RuntimeError("synthetic graph rollback")
    event.listen(engine, "after_cursor_execute", fail)
    try:
        with pytest.raises(RuntimeError):
            finish_normalized(engine, task, lease, result)
    finally:
        event.remove(engine, "after_cursor_execute", fail)
    assert graph_counts(engine) == [0] * len(GRAPH)
    with transaction(engine) as db:
        assert db.get(Simulation, sim["id"]).dataset_revision == 1
        assert db.get(SimulationTask, task).status == "running"
    assert finish_normalized(engine, task, lease, result)


@pytest.mark.parametrize("name,value", [("source_hash", "b" * 64), ("byte_count", 999),
    ("page_count", 2), ("unit", "1")])
def test_result_must_match_reserved_identity(environment, name, value):
    engine, sim, task, lease, result = reserved(environment)
    payload = result.model_dump()
    if name == "unit":
        payload["header"]["consumer_unit_id"]["value"] = value
    else:
        payload[name] = value
    with pytest.raises(DomainError) as error:
        finish_normalized(engine, task, lease, payload)
    assert error.value.code == "extraction_identity_conflict"
    assert graph_counts(engine) == [0] * len(GRAPH)


def test_subprocess_publishes_two_incremental_invoices_without_cancelling_queue(environment):
    engine, sim, _ = setup(environment)
    with Coordinator(engine) as coordinator:
        ids = [coordinator.read_synthetic(sim["owner_id"], sim["id"], 1, f"invoice-{i:03}",
            Sample("00001", serial=i), action="read_invoice") for i in range(2)]
        one = coordinator.run_invoice_once()
        two = coordinator.run_invoice_once()
        assert one.invoice_id and two.invoice_id and one.invoice_id != two.invoice_id
        assert [one.task_id, two.task_id] == ids
        assert coordinator.pending_count == coordinator.retained_bytes == 0
    with transaction(engine) as db:
        assert db.get(Simulation, sim["id"]).revision == 1
        assert db.get(Simulation, sim["id"]).dataset_revision == 3
        assert list(db.scalars(select(Invoice.status))) == ["needs_review", "needs_review"]


def test_json_snapshot_permissions_decimal_and_removal_revision(environment):
    engine, sim, task, lease, result = reserved(environment)
    invoice_id = finish_normalized(engine, task, lease, result)
    client = environment.client().login()
    url = f"/api/v1/simulations/{sim['id']}/invoices/{invoice_id}"
    assert environment.client().request("GET", url).status_code == 401
    body = client.request("GET", url).json()
    assert body["header"]["invoice_total"] == "19.9900000000"
    assert body["items"][1]["fields"]["quantity"] is None
    assert body["items"][1]["fields"]["amount"] == "-1.2300000000"
    assert body["created_by"] == sim["owner_id"] and body["status"] == "needs_review"
    listing = client.request("GET", url.rsplit("/", 1)[0]).json()
    assert listing["total"] == 1 and listing["dataset_revision"] == 2
    assert client.request("POST", url.rsplit("/", 1)[0], json={}).status_code == 405
    assert client.request("PATCH", url, json={}).status_code == 405
    assert client.request("DELETE", url, json={"confirm": True, "expected_revision": 1,
        "expected_dataset_revision": 1}).status_code == 409
    assert client.request("DELETE", url, json={"confirm": True, "expected_revision": 1,
        "expected_dataset_revision": 2}).status_code == 204
    assert client.request("GET", url).status_code == 404
    assert graph_counts(engine) == [0] * len(GRAPH)
    with transaction(engine) as db:
        assert db.get(InvoiceAdmission, task).removed
        assert db.get(Simulation, sim["id"]).dataset_revision == 3
    with pytest.raises(DomainError):
        finish_normalized(engine, task, lease, result)


def test_removal_graph_budget_and_dataset_rollback_together(environment):
    engine, sim, task, lease, result = reserved(environment)
    invoice_id = finish_normalized(engine, task, lease, result)
    before = graph_counts(engine)
    with pytest.raises(RuntimeError), transaction(engine, write=True) as db:
        remove_invoice(db, db.get(User, sim["owner_id"]), sim["id"], invoice_id,
            InvoiceDeleteInput(confirm=True, expected_revision=1, expected_dataset_revision=2))
        db.flush()
        raise RuntimeError("synthetic remove rollback")
    assert graph_counts(engine) == before
    with transaction(engine) as db:
        assert not db.get(InvoiceAdmission, task).removed
        assert db.get(Simulation, sim["id"]).dataset_revision == 2
    with pytest.raises(DomainError):
        admission.remove_synthetic(engine, sim["owner_id"], sim["id"], 1, task)
    admission.remove_synthetic(engine, sim["owner_id"], sim["id"], 1, task, expected_dataset_revision=2)
    assert graph_counts(engine) == [0] * len(GRAPH)
    admission.remove_synthetic(engine, sim["owner_id"], sim["id"], 1, task, expected_dataset_revision=2)
    with transaction(engine) as db:
        assert db.get(Simulation, sim["id"]).dataset_revision == 3


def test_late_result_after_removal_never_recreates_graph(environment):
    engine, sim, task, lease, result = reserved(environment)
    started, release = Event(), Event()
    def worker():
        started.set()
        assert release.wait(5)
        with pytest.raises(DomainError):
            finish_normalized(engine, task, lease, result)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(worker)
        try:
            assert started.wait(2)
            admission.remove_synthetic(engine, sim["owner_id"], sim["id"], 1, task)
        finally:
            release.set()
        future.result(timeout=5)
    assert graph_counts(engine) == [0] * len(GRAPH)


def test_zero_estimate_and_nullable_unknown_are_not_conflated(environment):
    engine, sim, task, lease, result = reserved(environment)
    payload = result.model_dump()
    payload["measurements"][1]["fields"]["reactive_energy"] = field("0", "kvarh", state="zero_confirmed", coverage="complete")
    payload["measurements"][2]["fields"]["active_energy"] = field("10", "kWh", state="estimated",
        hypothesis_code="synthetic-average", inputs=("items.line-1.quantity",))
    invoice_id = finish_normalized(engine, task, lease, payload)
    with transaction(engine) as db:
        values = list(db.scalars(select(FieldProvenance).where(FieldProvenance.invoice_id == invoice_id)))
        zero = next(p for p in values if p.state == "zero_confirmed")
        estimated = next(p for p in values if p.state == "estimated")
        assert zero.value == "0" and zero.coverage == "complete"
        assert estimated.hypothesis_code == "synthetic-average"
        assert db.scalar(select(FieldDependency.input_id).where(FieldDependency.field_id == estimated.id))
        assert any(p.state == "missing" and p.value is None for p in values)


def test_acl_suggestion_requires_coverage_or_explicit_evidence():
    payload = synthetic_result("a" * 64, 100, 1, "00001").model_dump()
    payload["market_candidate"] = "free"
    with pytest.raises(DomainError):
        prepare_result(payload)
    payload["coverage"] = "complete"
    payload["evidence"] = ("active_te_charge_absent_with_complete_coverage", "network_charge_present")
    assert prepare_result(payload).market_candidate == "free"
    payload["evidence"] += ("active_te_charge_present",)
    with pytest.raises(DomainError):
        prepare_result(payload)
    payload["market_assessment"] = "conflicting"
    assert prepare_result(payload).market_assessment == "conflicting"
    payload.update(coverage="partial", evidence=("explicit_market_label",), market_assessment="suggested")
    assert prepare_result(payload).market_candidate == "free"


def test_admin_authorship_and_client_cross_access_are_enforced(environment):
    engine = environment.app.state.engine
    with transaction(engine) as db:
        admin_id = db.scalar(select(User.id).where(User.role == "admin"))
    engine, sim, task, lease, result = reserved(environment, actor_id=admin_id)
    invoice_id = finish_normalized(engine, task, lease, result)
    with transaction(engine) as db:
        assert db.get(Invoice, invoice_id).created_by == admin_id
        assert db.get(Simulation, sim["id"]).owner_id == sim["owner_id"]
        assert set(db.scalars(select(FieldProvenance.actor_id))) == {admin_id}
    admin = environment.client().login("admin@ecowatt.test")
    client = environment.client().login()
    own_url = f"/api/v1/simulations/{sim['id']}/invoices/{invoice_id}"
    assert admin.request("GET", own_url).status_code == client.request("GET", own_url).status_code == 200
    from test_simulations import create
    private = create(admin).json()
    wrong_url = f"/api/v1/simulations/{private['id']}/invoices/{invoice_id}"
    assert client.request("GET", wrong_url).status_code == admin.request("GET", wrong_url).status_code == 404
    assert client.request("GET", f"/api/v1/simulations/{private['id']}/invoices").status_code == 404
    assert client.request("DELETE", wrong_url, json={"confirm": True, "expected_revision": 1,
        "expected_dataset_revision": 1}).status_code == 404


def test_simulation_delete_removes_publication_graph_and_budget_atomically(environment):
    engine, sim, task, lease, result = reserved(environment)
    finish_normalized(engine, task, lease, result)
    client = environment.client().login()
    assert client.request("DELETE", f"/api/v1/simulations/{sim['id']}",
        json={"confirm": True, "expected_revision": 1}).status_code == 204
    assert graph_counts(engine) == [0] * len(GRAPH)
    with transaction(engine) as db:
        assert db.get(InvoiceAdmission, task) is None
    with pytest.raises(DomainError):
        finish_normalized(engine, task, lease, result)


def test_concurrent_removal_of_same_dataset_only_one_confirms(environment):
    engine, sim, task, lease, result = reserved(environment)
    invoice_id = finish_normalized(engine, task, lease, result)
    def remove(_):
        try:
            with transaction(engine, write=True) as db:
                remove_invoice(db, db.get(User, sim["owner_id"]), sim["id"], invoice_id,
                    InvoiceDeleteInput(confirm=True, expected_revision=1, expected_dataset_revision=2))
            return "removed"
        except DomainError as error:
            return error.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(remove, range(2))) == ["not_found", "removed"]
    with transaction(engine) as db:
        assert db.get(Simulation, sim["id"]).dataset_revision == 3


@pytest.mark.parametrize("operation", ["revision", "delete", "block", "expire"])
def test_stale_normalized_result_rejected_before_any_child_is_written(environment, operation):
    engine, sim, task, lease, result = reserved(environment)
    client = environment.client().login()
    if operation == "revision":
        with transaction(engine) as db:
            distributor_id = db.get(Simulation, sim["id"]).distributor_id
        payload = {"expected_revision": 1, "distributor_id": distributor_id, "unit_identifier": "00001",
            "holder_name": "Fixture", "address_line": "Rua 2", "city": "Teste", "state": "SP", "postal_code": "00000"}
        assert client.request("PATCH", f"/api/v1/simulations/{sim['id']}/unit", json=payload).status_code == 200
    elif operation == "delete":
        assert client.request("DELETE", f"/api/v1/simulations/{sim['id']}",
            json={"confirm": True, "expected_revision": 1}).status_code == 204
    else:
        with transaction(engine, write=True) as db:
            if operation == "block":
                db.get(User, sim["owner_id"]).status = "blocked"
            else:
                from ecowatt.db.models import now
                db.get(SimulationTask, task).lease_expires_at = now() - 1
    with pytest.raises(DomainError):
        finish_normalized(engine, task, lease, result)
    assert graph_counts(engine) == [0] * len(GRAPH)


def test_migration_roundtrip_preserves_invoice_and_task_but_not_publication(environment):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect
    engine, sim, task, lease, result = reserved(environment)
    invoice_id = finish_normalized(engine, task, lease, result)
    cfg = Config("alembic.ini")
    cfg.attributes["settings"] = environment.settings
    command.downgrade(cfg, "0006_coordinator_lease")
    assert "invoice_publications" not in inspect(engine).get_table_names()
    command.upgrade(cfg, "head")
    command.check(cfg)
    with transaction(engine) as db:
        assert db.get(Invoice, invoice_id).source_hash == result.source_hash
        assert db.get(SimulationTask, task).status == "finished"
        assert db.get(Simulation, sim["id"]).dataset_revision == 1
        assert db.get(InvoicePublication, task) is None
    with engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
