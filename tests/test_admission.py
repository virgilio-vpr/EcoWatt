"""Admissão com metadados inventados; nenhum arquivo ou parser real."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from sqlalchemy import func, select

from ecowatt.db.admissions import InvoiceAdmission
from ecowatt.db.models import Distributor, Simulation, SimulationTask, User, now
from ecowatt.db.session import transaction
from ecowatt.errors import DomainError
from ecowatt.schemas import DeleteInput
from ecowatt.services import admission as service, tasks
from ecowatt.services.simulations import delete_simulation
from test_simulations import create


def setup(environment):
    client = environment.client().login()
    sim = create(client).json()
    engine = environment.app.state.engine
    with transaction(engine, write=True) as db:
        distributor = Distributor(code="SYNTHETIC", name="Fixture apenas")
        db.add(distributor)
        db.flush()
        row = db.get(Simulation, sim["id"])
        row.distributor_id, row.unit_identifier, row.unit_saved_at = distributor.id, "00001", now()
        row.holder_name, row.address_line, row.city, row.state, row.postal_code = "Fixture", "Rua 1", "Teste", "SP", "00000"
    inspection = service.Inspection("a" * 64, 100, 1, "SYNTHETIC", "synthetic-v1", "synthetic-v1", "00001")
    return engine, sim, inspection


def admit(engine, sim, inspection, key="synthetic-key", **kwargs):
    return service.admit_synthetic(engine, sim["owner_id"], sim["id"], sim["revision"],
        key, inspection, action=kwargs.pop("action", "read_invoice"), **kwargs)


def test_unit_action_and_real_document_gates(environment):
    engine, sim, inspection = setup(environment)
    for action in ("select", "upload", ""):
        with pytest.raises(DomainError, match="Ler fatura"):
            admit(engine, sim, inspection, action=action)
    with pytest.raises(DomainError) as error:
        admit(engine, sim, replace(inspection, source_kind="document"))
    assert error.value.code == "document_processing_disabled"
    with transaction(engine, write=True) as db:
        db.get(Simulation, sim["id"]).unit_saved_at = None
    with pytest.raises(DomainError) as error:
        admit(engine, sim, inspection)
    assert error.value.code == "unit_not_saved"
    with transaction(engine) as db:
        assert db.scalar(select(func.count()).select_from(InvoiceAdmission)) == 0
        assert db.scalar(select(func.count()).select_from(SimulationTask)) == 0


@pytest.mark.parametrize("field,value", [("byte_count", 0), ("byte_count", 10_000_001),
    ("byte_count", 1.0), ("page_count", 0), ("page_count", 11), ("page_count", True), ("source_hash", "bad")])
def test_invalid_metadata(environment, field, value):
    engine, sim, inspection = setup(environment)
    with pytest.raises(DomainError) as error:
        admit(engine, sim, replace(inspection, **{field: value}))
    assert error.value.code == "invalid_admission"


@pytest.mark.parametrize("field,value,code", [("distributor_code", "ENEL_SP", "invoice_identity_conflict"),
    ("unit_identifier", "1", "invoice_identity_conflict"),
    ("layout_version", "enel-v1", "layout_not_supported"),
    ("parser_version", "other", "layout_not_supported")])
def test_exact_identity_and_support(environment, field, value, code):
    engine, sim, inspection = setup(environment)
    with pytest.raises(DomainError) as error:
        admit(engine, sim, replace(inspection, **{field: value}))
    assert error.value.code == code
    for distributor in ("ENEL_SP", "ENEL_RJ", "OTHER"):
        assert service.support(distributor, "enel-v1") == {"supported": False,
            "reason": "layout_not_supported", "contact_required": True, "document_upload_enabled": False}


def test_concurrent_retry_and_duplicate_hash(environment):
    engine, sim, inspection = setup(environment)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: admit(engine, sim, inspection), range(2)))
    assert results[0] == results[1]
    with pytest.raises(DomainError) as error:
        admit(engine, sim, replace(inspection, byte_count=101))
    assert error.value.code == "idempotency_conflict"
    with pytest.raises(DomainError) as error:
        admit(engine, sim, inspection, "another-key")
    assert error.value.code == "duplicate_invoice"


@pytest.mark.parametrize("kind", ["files", "bytes", "pages"])
def test_accumulated_budget_and_concurrent_last_slot(environment, kind):
    engine, sim, inspection = setup(environment)
    count = 11 if kind == "files" else 5
    inspection = replace(inspection, byte_count=10_000_000 if kind == "bytes" else 100,
        page_count=10 if kind == "pages" else 1)
    for i in range(count):
        task = admit(engine, sim, replace(inspection, source_hash=f"{i:064x}"), f"request-{i:03}")
        lease = tasks.claim(engine, task, "synthetic")
        tasks.finish(engine, task, lease, lambda db, sim: None)
    def reserve(i):
        try:
            return admit(engine, sim, replace(inspection, source_hash=f"{i:064x}"), f"request-{i:03}")
        except DomainError as error:
            return error.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reserve, [20, 21]))
    assert results.count("invoice_limits_exceeded") == 1


def test_capacity_and_rollback_after_task_reservation(environment, monkeypatch):
    engine, sim, inspection = setup(environment)
    original = tasks.reserve
    def fail(*args):
        original(*args)
        raise RuntimeError("synthetic rollback")
    monkeypatch.setattr(tasks, "reserve", fail)
    with pytest.raises(RuntimeError):
        admit(engine, sim, inspection)
    monkeypatch.setattr(tasks, "reserve", original)
    with transaction(engine) as db:
        assert db.scalar(select(func.count()).select_from(SimulationTask)) == 0
    ids = [admit(engine, sim, replace(inspection, source_hash=f"{i:064x}"), f"request-{i:03}") for i in range(4)]
    with pytest.raises(DomainError) as error:
        admit(engine, sim, inspection)
    assert error.value.code == "admission_capacity_unavailable"
    lease = tasks.claim(engine, ids[0], "worker")
    tasks.finish(engine, ids[0], lease, lambda db, sim: None)
    assert admit(engine, sim, inspection)


def test_remove_replay_and_late_finish(environment):
    engine, sim, inspection = setup(environment)
    task = admit(engine, sim, inspection)
    lease = tasks.claim(engine, task, "worker")
    service.remove_synthetic(engine, sim["owner_id"], sim["id"], 1, task)
    called = []
    with pytest.raises(DomainError):
        tasks.finish(engine, task, lease, lambda db, sim: called.append(True))
    assert not called
    with pytest.raises(DomainError) as error:
        admit(engine, sim, inspection)
    assert error.value.code == "admission_removed"
    assert admit(engine, sim, inspection, "explicit-resend") != task


def test_atomic_finish_delete_rollback_and_authorization(environment):
    engine, sim, inspection = setup(environment)
    task = admit(engine, sim, inspection)
    lease = tasks.claim(engine, task, "worker")
    def fail(db, simulation):
        simulation.holder_name = "rollback"
        db.flush()
        raise RuntimeError("synthetic")
    with pytest.raises(RuntimeError):
        tasks.finish(engine, task, lease, fail)
    with transaction(engine) as db:
        assert db.get(SimulationTask, task).status == "running"
        assert db.get(Simulation, sim["id"]).holder_name == "Fixture"
    with pytest.raises(RuntimeError), transaction(engine, write=True) as db:
        delete_simulation(db, db.get(User, sim["owner_id"]), sim["id"], DeleteInput(confirm=True, expected_revision=1))
        raise RuntimeError("rollback deletion")
    with transaction(engine) as db:
        admin = db.scalar(select(User).where(User.role == "admin"))
        admin_id = admin.id
    # Administração preserva autoria distinta do dono e a idempotência por ator.
    admin_task = service.admit_synthetic(engine, admin_id, sim["id"], 1, "admin-read-key",
        replace(inspection, source_hash="b" * 64), action="read_invoice")
    with transaction(engine) as db:
        assert db.get(InvoiceAdmission, admin_task).actor_id == admin_id
        assert db.get(Simulation, sim["id"]).owner_id == sim["owner_id"]
    with transaction(engine, write=True) as db:
        delete_simulation(db, db.get(User, sim["owner_id"]), sim["id"], DeleteInput(confirm=True, expected_revision=1))
    with pytest.raises(DomainError):
        tasks.finish(engine, task, lease, lambda db, sim: pytest.fail("late callback"))
    with pytest.raises(DomainError):
        admit(engine, sim, inspection)

    with transaction(engine) as db:
        assert db.scalar(select(func.count()).select_from(InvoiceAdmission)) == 0


def test_expired_reservation_requires_explicit_resend(environment):
    engine, sim, inspection = setup(environment)
    task = admit(engine, sim, inspection)
    tasks.claim(engine, task, "worker")
    with transaction(engine, write=True) as db:
        db.get(SimulationTask, task).lease_expires_at = now() - 1
    tasks.expire(engine)
    assert admit(engine, sim, inspection) == task
    with transaction(engine) as db:
        assert db.get(SimulationTask, task).status == "expired"


def test_support_api_is_authorized_read_only_and_blocks_catalog_layout(environment):
    client = environment.client().login()
    sim = create(client).json()
    url = "/api/v1/simulations/" + sim["id"] + "/invoice-admission"
    assert environment.client().request("GET", url).status_code == 401
    assert client.request("GET", url).json()["reason"] == "unit_not_saved"
    distributor = client.request("GET", "/api/v1/distributors").json()["items"][0]
    payload = {"expected_revision": 1, "distributor_id": distributor["id"], "unit_identifier": "00001",
        "holder_name": "Fixture", "address_line": "Rua 1", "city": "Teste", "state": "SP", "postal_code": "00000"}
    assert client.request("PATCH", "/api/v1/simulations/" + sim["id"] + "/unit", json=payload).status_code == 200
    result = client.request("GET", url + "?layout_version=enel-v1").json()
    assert result["reason"] == "layout_not_supported" and result["contact_required"]
    assert not result["supported"] and not result["document_upload_enabled"]
    assert result["distributor_id"] == distributor["id"]
    assert client.request("POST", url).status_code == 405
    admin = environment.client().login("admin@ecowatt.test")
    other = create(admin).json()
    assert client.request("GET", "/api/v1/simulations/" + other["id"] + "/invoice-admission").status_code == 404
    with transaction(environment.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(InvoiceAdmission)) == 0


def test_new_unit_revision_cancels_admission_and_denies_stale_result(environment):
    engine, sim, inspection = setup(environment)
    task = admit(engine, sim, inspection)
    lease = tasks.claim(engine, task, "worker")
    client = environment.client().login()
    with transaction(engine) as db:
        distributor_id = db.get(Simulation, sim["id"]).distributor_id
    payload = {"expected_revision": 1, "distributor_id": distributor_id, "unit_identifier": "00001",
        "holder_name": "Fixture", "address_line": "Rua 2", "city": "Teste", "state": "SP", "postal_code": "00000"}
    assert client.request("PATCH", "/api/v1/simulations/" + sim["id"] + "/unit", json=payload).status_code == 200
    with pytest.raises(DomainError):
        tasks.finish(engine, task, lease, lambda db, sim: pytest.fail("stale callback"))
    with pytest.raises(DomainError) as error:
        admit(engine, sim, inspection)
    assert error.value.code == "simulation_revision_conflict"
    with transaction(engine) as db:
        assert db.get(SimulationTask, task).status == "cancelled"


def test_claims_serialized_globally_and_capacity_concurrent(environment):
    engine, sim, inspection = setup(environment)
    admin = environment.client().login("admin@ecowatt.test")
    other = create(admin).json()
    with transaction(engine, write=True) as db:
        original = db.get(Simulation, sim["id"])
        row = db.get(Simulation, other["id"])
        row.distributor_id, row.unit_identifier, row.unit_saved_at = original.distributor_id, "00001", now()
    one = admit(engine, sim, inspection)
    two = admit(engine, other, inspection)
    def claim(task):
        try:
            return tasks.claim(engine, task, "worker")
        except DomainError as error:
            return error.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        leases = list(pool.map(claim, [one, two]))
    assert leases.count("admission_executor_busy") == 1
    # Três reservas ativas, duas requisições disputam a última vaga global.
    admit(engine, sim, replace(inspection, source_hash="b" * 64), "request-two")
    def reserve(i):
        try:
            return admit(engine, sim, replace(inspection, source_hash=f"{i:064x}"), f"request-{i:03}")
        except DomainError as error:
            return error.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reserve, [20, 21]))
    assert results.count("admission_capacity_unavailable") == 1
    # Cliente não pode admitir nem remover tarefa de outra titularidade.
    with pytest.raises(DomainError):
        service.admit_synthetic(engine, sim["owner_id"], other["id"], 1,
            "cross-owner-key", inspection, action="read_invoice")
    with pytest.raises(DomainError):
        service.remove_synthetic(engine, sim["owner_id"], other["id"], 1, two)


def test_removal_rollback_preserves_budget_and_lease(environment, monkeypatch):
    from contextlib import contextmanager
    engine, sim, inspection = setup(environment)
    task = admit(engine, sim, inspection)
    lease = tasks.claim(engine, task, "worker")
    @contextmanager
    def rollback(engine, **kwargs):
        with transaction(engine, **kwargs) as db:
            yield db
            db.flush()
            raise RuntimeError("synthetic removal rollback")
    monkeypatch.setattr(service, "transaction", rollback)
    with pytest.raises(RuntimeError):
        service.remove_synthetic(engine, sim["owner_id"], sim["id"], 1, task)
    with transaction(engine) as db:
        assert not db.get(InvoiceAdmission, task).removed
        assert db.get(SimulationTask, task).status == "running"
    tasks.heartbeat(engine, task, lease)


def test_one_simulation_per_owner_and_blocked_actor(environment):
    engine, sim, inspection = setup(environment)
    client = environment.client().login()
    other = create(client, "another-simulation").json()
    with transaction(engine, write=True) as db:
        original = db.get(Simulation, sim["id"])
        row = db.get(Simulation, other["id"])
        row.distributor_id, row.unit_identifier, row.unit_saved_at = original.distributor_id, "00001", now()
    task = admit(engine, sim, inspection)
    with pytest.raises(DomainError) as error:
        admit(engine, other, inspection, "other-unit-read")
    assert error.value.code == "simulation_processing_limit"
    with transaction(engine, write=True) as db:
        db.get(User, sim["owner_id"]).status = "blocked"
    with pytest.raises(DomainError):
        admit(engine, sim, inspection)
    with pytest.raises(DomainError):
        tasks.claim(engine, task, "worker")
