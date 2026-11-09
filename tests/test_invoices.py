"""Somente fixtures inventadas; nenhum PDF, OCR ou corpus real."""
from datetime import date
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete, func, inspect, select
from sqlalchemy.exc import IntegrityError, StatementError

from ecowatt.db.invoices import (FieldDependency, FieldProvenance, Invoice, InvoiceItem,
    InvoiceMarketEvidence, InvoiceMeasurement, InvoiceValidation)
from ecowatt.db.models import Simulation, SimulationTask, User
from ecowatt.db.session import transaction
from ecowatt.errors import DomainError
from ecowatt.schemas import DeleteInput
from ecowatt.services import tasks
from ecowatt.services.invoices import require_invoice
from ecowatt.services.simulations import delete_simulation
from test_simulations import create
from test_task_lifecycle import setup_task

TABLES = (Invoice, InvoiceMeasurement, InvoiceItem, FieldProvenance,
          InvoiceValidation, InvoiceMarketEvidence, FieldDependency)


def graph(db, sim, actor_id=None, source_hash="a" * 64):
    invoice = Invoice(simulation_id=sim.id, created_by=actor_id or sim.created_by,
        dataset_revision=sim.revision, source_hash=source_hash, source_kind="synthetic",
        competence="2026-01", cycle_start=date(2025, 12, 10), cycle_end=date(2026, 1, 9),
        cycle_days=30, modality="green", invoice_total=Decimal("19.99"),
        amount_payable=Decimal("23.99"), coverage="partial")
    db.add(invoice)
    db.flush()
    single = InvoiceMeasurement(invoice_id=invoice.id, post="single", contracted_demand=Decimal("150"))
    peak = InvoiceMeasurement(invoice_id=invoice.id, post="peak", measured_active_demand=Decimal("123.4567890123"))
    off_peak = InvoiceMeasurement(invoice_id=invoice.id, post="off_peak", measured_active_demand=Decimal("140"))
    db.add_all([single, peak, off_peak])
    db.flush()
    item = InvoiceItem(invoice_id=invoice.id, measurement_id=peak.id, position=1,
        type="active_energy_te", post="peak", quantity=Decimal("10"), quantity_unit="kWh",
        effective_price=Decimal("1.999000000000000001"), amount=Decimal("19.99"), price_basis="with_tax")
    money_only = InvoiceItem(invoice_id=invoice.id, position=2, type="idle_demand", amount=Decimal("-1.23"))
    db.add_all([item, money_only])
    db.flush()
    db.add_all([
        FieldProvenance(invoice_id=invoice.id, item_id=item.id, field_path=f"items.{item.id}.amount",
            state="confirmed", value="19.99", unit="BRL", origin="user", actor_id=invoice.created_by),
        FieldProvenance(invoice_id=invoice.id, item_id=money_only.id, field_path=f"items.{money_only.id}.quantity",
            state="missing", origin="user", actor_id=invoice.created_by),
        InvoiceValidation(invoice_id=invoice.id, field_path="header.invoice_total", code="synthetic_review",
            result="warning", policy_version="synthetic-v1", observed=Decimal("19.99")),
        InvoiceMarketEvidence(invoice_id=invoice.id, code="network_charge_present"),
    ])
    db.flush()
    return invoice.id, peak.id, item.id


def persist_graph(environment):
    _, simulation, task_id = setup_task(environment)
    engine = environment.app.state.engine
    lease = tasks.claim(engine, task_id, "synthetic-schema-worker")
    ids = []
    tasks.finish(engine, task_id, lease, lambda db, sim: ids.extend(graph(db, sim)))
    return simulation, task_id, ids


def counts(db):
    return [db.scalar(select(func.count()).select_from(cls)) for cls in TABLES]


def test_typed_graph_decimal_unknowns_and_green_posts(environment):
    simulation, task_id, (invoice_id, peak_id, _) = persist_graph(environment)
    with transaction(environment.app.state.engine) as db:
        invoice = db.get(Invoice, invoice_id)
        assert invoice.market == invoice.market_candidate == "unknown"
        assert invoice.status == "needs_review" and invoice.parser_version is None
        assert invoice.invoice_total == Decimal("19.99") and invoice.amount_payable == Decimal("23.99")
        peak = db.get(InvoiceMeasurement, peak_id)
        assert peak.measured_active_demand == Decimal("123.4567890123")
        assert peak.contracted_demand is None and peak.billed_active_demand is None
        assert peak.loss_adjustment_included is None
        single = db.scalar(select(InvoiceMeasurement).where(InvoiceMeasurement.post == "single"))
        assert single.contracted_demand == Decimal("150") and single.measured_active_demand is None
        items = db.scalars(select(InvoiceItem).order_by(InvoiceItem.position)).all()
        assert items[0].effective_price == Decimal("1.999000000000000001")
        assert items[1].quantity is items[1].effective_price is None
        assert items[1].amount == Decimal("-1.23")
        assert invoice.created_by == simulation["owner_id"]
        assert db.get(SimulationTask, task_id).status == "finished"


def test_finish_rolls_back_entire_real_graph_and_allows_retry(environment):
    engine = environment.app.state.engine
    _, _, task_id = setup_task(environment)
    lease = tasks.claim(engine, task_id, "synthetic-worker")
    def fail(db, sim):
        graph(db, sim)
        raise RuntimeError("synthetic failure after all children")
    with pytest.raises(RuntimeError):
        tasks.finish(engine, task_id, lease, fail)
    with transaction(engine) as db:
        assert counts(db) == [0] * 7
        assert db.get(SimulationTask, task_id).status == "running"
    tasks.finish(engine, task_id, lease, lambda db, sim: graph(db, sim))
    with transaction(engine) as db:
        assert counts(db) == [1, 3, 2, 2, 1, 1, 0]
    with pytest.raises(DomainError):
        tasks.finish(engine, task_id, lease, lambda db, sim: graph(db, sim))


def test_delete_removes_graph_atomically_and_late_callback_cannot_recreate(environment):
    engine = environment.app.state.engine
    simulation, _, _ = persist_graph(environment)
    with transaction(engine, write=True) as db:
        actor = db.get(User, simulation["owner_id"])
        task_id = tasks.reserve(db, actor, simulation["id"], 1)
    lease = tasks.claim(engine, task_id, "late-synthetic-worker")
    with pytest.raises(RuntimeError), transaction(engine, write=True) as db:
        delete_simulation(db, db.get(User, simulation["owner_id"]), simulation["id"],
                          DeleteInput(confirm=True, expected_revision=1))
        db.flush()
        assert counts(db) == [0] * 7
        raise RuntimeError("undo deletion")
    with transaction(engine) as db:
        assert counts(db) == [1, 3, 2, 2, 1, 1, 0]
        assert db.get(SimulationTask, task_id).status == "running"
    client = environment.client().login()
    assert client.request("DELETE", "/api/v1/simulations/" + simulation["id"],
        json={"confirm": True, "expected_revision": 1}).status_code == 204
    with pytest.raises(DomainError):
        tasks.finish(engine, task_id, lease, lambda db, sim: graph(db, sim))
    with transaction(engine) as db:
        assert counts(db) == [0] * 7
        assert db.get(Simulation, simulation["id"]).slot is None
    assert create(client, "after-graph-deletion").status_code == 201


def test_read_authorization_revision_and_explicit_admin_authorship(environment):
    engine = environment.app.state.engine
    simulation, _, (invoice_id, _, _) = persist_graph(environment)
    admin_client = environment.client().login("admin@ecowatt.test")
    other = create(admin_client).json()
    with transaction(engine, write=True) as db:
        owner = db.get(User, simulation["owner_id"])
        admin = db.scalar(select(User).where(User.role == "admin"))
        assert require_invoice(db, owner, simulation["id"], invoice_id, 1).id == invoice_id
        assert require_invoice(db, admin, simulation["id"], invoice_id).id == invoice_id
        for sim_id, rev in ((other["id"], None), (simulation["id"], 2)):
            with pytest.raises(DomainError):
                require_invoice(db, owner, sim_id, invoice_id, rev)
        with pytest.raises(DomainError):
            require_invoice(db, admin, other["id"], invoice_id)
        sim = db.get(Simulation, simulation["id"])
        new_id, _, _ = graph(db, sim, actor_id=admin.id, source_hash="b" * 64)
        assert db.get(Invoice, new_id).created_by == admin.id and sim.owner_id == owner.id


@pytest.mark.parametrize("changes", [
    {"status": "completed"}, {"coverage": "absent"}, {"modality": "yellow"},
    {"source_hash": "short"}, {"dataset_revision": 0}, {"cycle_days": 0},
    {"cycle_end": date(2025, 1, 1)}, {"market": "presumed_free"},
])
def test_invoice_constraints(environment, changes):
    engine = environment.app.state.engine
    simulation, _, (invoice_id, _, _) = persist_graph(environment)
    with pytest.raises(IntegrityError), transaction(engine, write=True) as db:
        invoice = db.get(Invoice, invoice_id)
        for key, value in changes.items():
            setattr(invoice, key, value)


def test_scoped_references_hash_uniqueness_and_physical_cascades(environment):
    engine = environment.app.state.engine
    simulation, _, (invoice_id, peak_id, item_id) = persist_graph(environment)
    with pytest.raises(IntegrityError), transaction(engine, write=True) as db:
        graph(db, db.get(Simulation, simulation["id"]))
    with transaction(engine, write=True) as db:
        other_id, _, _ = graph(db, db.get(Simulation, simulation["id"]), source_hash="b" * 64)
    with pytest.raises(IntegrityError), transaction(engine, write=True) as db:
        db.add(InvoiceItem(invoice_id=other_id, measurement_id=peak_id, position=3))
    with pytest.raises(IntegrityError), transaction(engine, write=True) as db:
        db.add(FieldProvenance(invoice_id=other_id, item_id=item_id, field_path="invalid",
            state="missing", origin="user", actor_id=simulation["owner_id"]))
    with transaction(engine, write=True) as db:
        # Mesma ordem explícita da exclusão lógica; testa também o pai físico.
        db.execute(delete(InvoiceItem))
        db.execute(delete(Simulation).where(Simulation.id == simulation["id"]))
        assert counts(db) == [0] * 7
    with engine.connect() as conn:
        assert conn.exec_driver_sql("PRAGMA foreign_key_check").all() == []


@pytest.mark.parametrize("changes", [
    {"state": "missing", "value": "0"}, {"state": "confirmed", "value": None},
    {"state": "zero_confirmed", "value": "0", "coverage": "partial"},
    {"state": "estimated", "value": "2"}, {"state": "not_applicable"},
    {"origin": "pdf_text"}, {"origin": "ocr", "page": 1},
    {"origin": "derived"}, {"version": 2}, {"region_x": "1"},
])
def test_field_state_and_evidence_constraints(environment, changes):
    simulation, _, (invoice_id, _, _) = persist_graph(environment)
    values = dict(invoice_id=invoice_id, field_path="header.synthetic", state="missing",
                  origin="user", actor_id=simulation["owner_id"])
    values.update(changes)
    with pytest.raises(IntegrityError), transaction(environment.app.state.engine, write=True) as db:
        db.add(FieldProvenance(**values))


def test_zero_estimates_correction_history_and_decimal_rejection(environment):
    engine = environment.app.state.engine
    simulation, _, (invoice_id, peak_id, item_id) = persist_graph(environment)
    with transaction(engine, write=True) as db:
        for version, value, state, extra in (
            (1, "0", "zero_confirmed", {"coverage": "complete"}),
            (2, "1", "estimated", {"hypothesis_code": "synthetic_assumption", "reason_code": "synthetic_correction"}),
        ):
            db.add(FieldProvenance(invoice_id=invoice_id, field_path="header.synthetic", version=version,
                value=value, state=state, origin="user", actor_id=simulation["owner_id"], **extra))
    with transaction(engine) as db:
        history = db.scalars(select(FieldProvenance).where(FieldProvenance.field_path == "header.synthetic")
            .order_by(FieldProvenance.version)).all()
        assert [(row.value, row.state) for row in history] == [("0", "zero_confirmed"), ("1", "estimated")]
        input_id, field_id = history[0].id, history[1].id
    with transaction(engine, write=True) as db:
        db.add(FieldDependency(invoice_id=invoice_id, field_id=field_id, input_id=input_id))
    with pytest.raises(IntegrityError), transaction(engine, write=True) as db:
        db.add(FieldDependency(invoice_id=invoice_id, field_id=input_id, input_id=input_id))
    for value in (0.1, "NaN", "1.0000000000000000001"):
        with pytest.raises(StatementError), transaction(engine, write=True) as db:
            db.get(InvoiceItem, item_id).effective_price = value
    with pytest.raises(ValueError), transaction(engine, write=True) as db:
        db.get(InvoiceMeasurement, peak_id).measured_active_demand = "-1"


def test_upgrade_from_phase_one_preserves_existing_data_and_downgrade(environment):
    engine = environment.app.state.engine
    client = environment.client().login()
    simulation = create(client).json()
    cfg = Config("alembic.ini")
    cfg.attributes["settings"] = environment.settings
    command.downgrade(cfg, "0003_simulation_tasks")
    assert "invoices" not in inspect(engine).get_table_names()
    with transaction(engine) as db:
        # Esquema histórico não contém colunas adicionadas ao modelo atual.
        assert db.scalar(select(Simulation.owner_id).where(Simulation.id == simulation["id"])) == simulation["owner_id"]
    command.upgrade(cfg, "head")
    command.check(cfg)
    with transaction(engine, write=True) as db:
        graph(db, db.get(Simulation, simulation["id"]))
    command.downgrade(cfg, "0003_simulation_tasks")
    command.upgrade(cfg, "head")
    command.check(cfg)
    with transaction(engine) as db:
        assert counts(db) == [0] * 7
        assert db.get(Simulation, simulation["id"]) is not None


@pytest.mark.parametrize("cause", ["delete", "revision"])
def test_late_thread_and_new_revision_never_write_invoice_children(environment, cause):
    engine = environment.app.state.engine
    client, simulation, task_id = setup_task(environment)
    lease = tasks.claim(engine, task_id, "synthetic-delayed-worker")
    started, release = Event(), Event()
    def worker():
        started.set()
        assert release.wait(5)
        with pytest.raises(DomainError):
            tasks.finish(engine, task_id, lease, lambda db, sim: graph(db, sim))
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(worker)
        try:
            assert started.wait(2)
            if cause == "delete":
                assert client.request("DELETE", "/api/v1/simulations/" + simulation["id"],
                    json={"confirm": True, "expected_revision": 1}).status_code == 204
            else:
                distributor = client.request("GET", "/api/v1/distributors").json()["items"][0]
                payload = {"expected_revision": 1, "distributor_id": distributor["id"],
                    "unit_identifier": "000-synthetic", "holder_name": "Synthetic",
                    "address_line": "Rua Sintética 1", "city": "Exemplo", "state": "SP", "postal_code": "00000"}
                assert client.request("PATCH", "/api/v1/simulations/" + simulation["id"] + "/unit",
                                      json=payload).status_code == 200
        finally:
            release.set()
        future.result(5)
    with transaction(engine) as db:
        assert counts(db) == [0] * 7
        assert db.get(SimulationTask, task_id).reason == ("simulation_deleted" if cause == "delete" else "revision_changed")
