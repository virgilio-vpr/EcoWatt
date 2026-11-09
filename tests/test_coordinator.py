"""Fixtures inventadas e subprocessos locais; nenhum PDF ou OCR."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import multiprocessing
import json
import time

import pytest
from sqlalchemy import event, func, select

from ecowatt.db.admissions import InvoiceAdmission
from ecowatt.db.coordinator import CoordinatorLease
from ecowatt.db.models import Simulation, SimulationTask, User, now
from ecowatt.db.session import transaction
from ecowatt.errors import DomainError
from ecowatt.schemas import DeleteInput
from ecowatt.services import admission, leadership, tasks
from ecowatt.services.coordinator import Coordinator
from ecowatt.services.simulations import delete_simulation
from ecowatt.services.synthetic_worker import Receipt, Sample, decode_receipt
from test_admission import setup


def read(coordinator, sim, sample=None, key="coordinator-key", action="read_invoice"):
    return coordinator.read_synthetic(sim["owner_id"], sim["id"], sim["revision"], key,
        sample or Sample("00001"), action=action)


def state(engine, task_id):
    with transaction(engine) as db:
        task = db.get(SimulationTask, task_id)
        return task.status, task.reason


def expire_leader(engine):
    with transaction(engine, write=True) as db:
        db.get(CoordinatorLease, 1).expires_at = now() - 1


def wait_running(engine, task_id):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        if state(engine, task_id)[0] == "running":
            return
        time.sleep(.02)
    pytest.fail("Fixture não iniciou")


def test_election_concurrent_no_invalidation_of_live_leader(environment):
    engine, sim, _ = setup(environment)
    def start(_):
        try:
            return Coordinator(engine)
        except DomainError as error:
            return error.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(start, range(2)))
    assert results.count("coordinator_unavailable") == 1
    leader = next(r for r in results if isinstance(r, Coordinator))
    try:
        task = read(leader, sim)
        with pytest.raises(DomainError):
            Coordinator(engine)
        assert state(engine, task)[0] == "queued"
        assert leader.run_once().state == "finished"
    finally:
        leader.close()


def test_queue_retry_memory_success_and_no_payload_in_database(environment):
    engine, sim, _ = setup(environment)
    statements = []
    def observe(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO invoice_admissions"):
            statements.append((statement, parameters))
    event.listen(engine, "before_cursor_execute", observe)
    children = {p.pid for p in multiprocessing.active_children()}
    with Coordinator(engine) as coordinator:
        task = read(coordinator, sim, Sample("00001", padding_bytes=4096))
        entry = coordinator._queue[task]
        assert coordinator.retained_bytes == entry.inspection.byte_count
        assert read(coordinator, sim, Sample("00001", padding_bytes=4096)) == task
        assert coordinator.pending_count == 1
        observed = []
        def persist(db, simulation, result):
            assert result.version == "synthetic-receipt-v1"
            assert result.source_hash == entry.inspection.source_hash
            observed.append(simulation.id)
        assert coordinator.run_once(persist).state == "finished"
        assert observed == [sim["id"]]
        assert coordinator.pending_count == coordinator.retained_bytes == 0
        assert entry.content == bytearray()
        assert state(engine, task)[0] == "finished"
        # Retry concluído não recria bytes nem executa outro processo.
        assert read(coordinator, sim, Sample("00001", padding_bytes=4096)) == task
        assert coordinator.run_once() is None
    event.remove(engine, "before_cursor_execute", observe)
    assert statements and "ECOWATT-SYNTHETIC" not in repr(statements)
    assert {p.pid for p in multiprocessing.active_children()} == children


@pytest.mark.parametrize("action", ["select", "upload", ""])
def test_selection_does_not_materialize_or_reserve(environment, action, monkeypatch):
    engine, sim, _ = setup(environment)
    with Coordinator(engine) as coordinator:
        monkeypatch.setattr(Sample, "materialize", lambda _: pytest.fail("seleção processou conteúdo"))
        with pytest.raises(DomainError) as error:
            read(coordinator, sim, action=action)
        assert error.value.code == "read_action_required"
        assert coordinator.pending_count == 0
    with transaction(engine) as db:
        assert db.scalar(select(func.count()).select_from(InvoiceAdmission)) == 0


def test_refuses_arbitrary_bytes_and_keeps_document_gate_closed(environment):
    engine, sim, _ = setup(environment)
    with Coordinator(engine) as coordinator:
        with pytest.raises(DomainError) as error:
            coordinator.read_synthetic(sim["owner_id"], sim["id"], 1, "raw-byte-key",
                b"%PDF-synthetic-not-a-document", action="read_invoice")
        assert error.value.code == "document_processing_disabled"
        assert not admission.support("ENEL_SP", "any")["document_upload_enabled"]


def test_capacity_and_enqueue_failure_rollback_sql_and_memory(environment, monkeypatch):
    engine, sim, _ = setup(environment)
    import ecowatt.services.coordinator as module
    with Coordinator(engine) as coordinator:
        monkeypatch.setattr(module, "MAX_RETAINED_BYTES", 1)
        with pytest.raises(DomainError) as error:
            read(coordinator, sim)
        assert error.value.code == "admission_capacity_unavailable"
        assert coordinator.pending_count == coordinator.retained_bytes == 0
        with transaction(engine) as db:
            assert db.scalar(select(func.count()).select_from(SimulationTask)) == 0
            assert db.scalar(select(func.count()).select_from(InvoiceAdmission)) == 0
        monkeypatch.setattr(module, "MAX_RETAINED_BYTES", 40_000_000)
        for serial in range(4):
            read(coordinator, sim, Sample("00001", serial=serial), key=f"serial-{serial:03}")
        with pytest.raises(DomainError):
            read(coordinator, sim, Sample("00001", serial=5), key="serial-extra")
        assert coordinator.pending_count == 4


def test_commit_failure_rolls_back_ephemeral_enqueue(environment, monkeypatch):
    from contextlib import contextmanager
    engine, sim, _ = setup(environment)
    @contextmanager
    def rollback(engine, **kwargs):
        with transaction(engine, **kwargs) as db:
            yield db
            db.flush()
            raise RuntimeError("synthetic commit failure")
    with Coordinator(engine) as coordinator:
        monkeypatch.setattr(admission, "transaction", rollback)
        with pytest.raises(RuntimeError):
            read(coordinator, sim)
        assert coordinator.pending_count == coordinator.retained_bytes == 0
        with transaction(engine) as db:
            assert db.scalar(select(func.count()).select_from(SimulationTask)) == 0


@pytest.mark.parametrize("failure", ["timeout", "worker", "persist"])
def test_failure_timeout_and_callback_rollback_discard_and_reap(environment, failure):
    engine, sim, _ = setup(environment)
    options = {"worker_delay": 3, "file_timeout": .05} if failure == "timeout" else {"worker_fail": failure == "worker"}
    children = {p.pid for p in multiprocessing.active_children()}
    with Coordinator(engine, **options) as coordinator:
        task = read(coordinator, sim)
        entry = coordinator._queue[task]
        def persist(db, simulation, result):
            simulation.holder_name = "must rollback"
            db.flush()
            raise RuntimeError("synthetic persist failure")
        if failure == "persist":
            with pytest.raises(RuntimeError):
                coordinator.run_once(persist)
        else:
            result = coordinator.run_once()
            assert result.state == "interrupted"
        assert coordinator.pending_count == coordinator.retained_bytes == 0
        assert not entry.content
        expected = {"timeout": "file_timeout", "worker": "synthetic_worker_failed", "persist": "persistence_failed"}[failure]
        assert state(engine, task) == ("expired", expected)
        with transaction(engine) as db:
            assert db.get(Simulation, sim["id"]).holder_name == "Fixture"
    assert {p.pid for p in multiprocessing.active_children()} == children


@pytest.mark.parametrize("operation", ["remove", "delete", "block", "revision", "close", "takeover"])
def test_interrupt_running_process_and_reject_late_result(environment, operation):
    engine, sim, _ = setup(environment)
    coordinator = Coordinator(engine, worker_delay=3)
    successor = None
    try:
        task = read(coordinator, sim)
        entry = coordinator._queue[task]
        persisted = []
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(coordinator.run_once, lambda db, sim, result: persisted.append(True))
            wait_running(engine, task)
            if operation == "remove":
                admission.remove_synthetic(engine, sim["owner_id"], sim["id"], 1, task)
            elif operation == "delete":
                with transaction(engine, write=True) as db:
                    delete_simulation(db, db.get(User, sim["owner_id"]), sim["id"], DeleteInput(confirm=True, expected_revision=1))
            elif operation == "block":
                with transaction(engine, write=True) as db:
                    db.get(User, sim["owner_id"]).status = "blocked"
            elif operation == "revision":
                client = environment.client().login()
                with transaction(engine) as db:
                    distributor = db.get(Simulation, sim["id"]).distributor_id
                payload = {"expected_revision": 1, "distributor_id": distributor, "unit_identifier": "00001",
                    "holder_name": "Fixture", "address_line": "Rua 2", "city": "Teste", "state": "SP", "postal_code": "00000"}
                assert client.request("PATCH", "/api/v1/simulations/" + sim["id"] + "/unit", json=payload).status_code == 200
            elif operation == "close":
                coordinator.close()
            else:
                expire_leader(engine)
                successor = Coordinator(engine)
            result = future.result(timeout=10)
            assert result.state == "interrupted"
        assert not persisted and not entry.content
        assert coordinator.pending_count == coordinator.retained_bytes == 0
        assert state(engine, task)[0] != "finished"
    finally:
        coordinator.close()
        if successor:
            successor.close()


def test_takeover_recovers_only_lost_queue_and_expired_running(environment):
    engine, sim, inspection = setup(environment)
    previous = Coordinator(engine)
    successor = None
    try:
        running = read(previous, sim, key="running-fixture")
        queued = read(previous, sim, Sample("00001", serial=2), key="queued-fixture")
        lease = tasks.claim(engine, running, "synthetic-legacy-executor")
        legacy = admission.admit_synthetic(engine, sim["owner_id"], sim["id"], 1,
            "uncoordinated-fixture", replace(inspection, source_hash="f" * 64), action="read_invoice")
        expire_leader(engine)
        successor = Coordinator(engine)
        assert state(engine, queued) == ("expired", "content_lost")
        assert state(engine, running)[0] == "running"  # lease ainda viva
        assert state(engine, legacy)[0] == "queued"  # contrato anterior preservado
        with pytest.raises(DomainError):
            tasks.finish(engine, running, lease, lambda db, sim: pytest.fail("fenced"))
        with pytest.raises(DomainError):
            previous.sweep()
        assert previous.retained_bytes == 0
        with transaction(engine, write=True) as db:
            db.get(SimulationTask, running).lease_expires_at = now() - 1
        successor.sweep()
        assert state(engine, running) == ("expired", "lease_expired")
        # Retry após perda informa a mesma tarefa expirada sem refazer a fila.
        assert read(successor, sim, Sample("00001", serial=2), key="queued-fixture") == queued
        assert successor.pending_count == 0
        admission.remove_synthetic(engine, sim["owner_id"], sim["id"], 1, queued)
        assert read(successor, sim, Sample("00001", serial=2), key="explicit-retry") != queued
    finally:
        previous.close()
        if successor:
            successor.close()


def test_batch_deadline_includes_waiting_queue_and_shutdown_is_idempotent(environment):
    engine, sim, _ = setup(environment)
    coordinator = Coordinator(engine, batch_timeout=.01)
    task = read(coordinator, sim)
    time.sleep(.03)
    coordinator.sweep()
    assert state(engine, task) == ("expired", "batch_timeout")
    assert coordinator.pending_count == coordinator.retained_bytes == 0
    coordinator.close()
    coordinator.close()
    with pytest.raises(DomainError):
        read(coordinator, sim, Sample("00001", serial=2), key="after-shutdown")
    with Coordinator(engine) as successor:
        assert successor.identity.epoch > coordinator.identity.epoch


def test_process_wait_holds_no_sql_transaction(environment):
    engine, sim, _ = setup(environment)
    with Coordinator(engine, worker_delay=1) as coordinator:
        task = read(coordinator, sim)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(coordinator.run_once)
            wait_running(engine, task)
            # Escrita independente confirma enquanto filho ainda está trabalhando.
            with transaction(engine, write=True) as db:
                db.get(Simulation, sim["id"]).holder_name = "Parallel write"
            assert future.result(timeout=10).state == "finished"
        with transaction(engine) as db:
            assert db.get(Simulation, sim["id"]).holder_name == "Parallel write"


@pytest.mark.parametrize("patch", [{"page_count": True}, {"byte_count": 1.0}, {"source_hash": "bad"},
    {"version": "unexpected-v2"}, {"raw_text": "must not be accepted"}])
def test_ipc_closed_schema_rejects_unknown_fields_and_types(patch):
    packet = {"status": "ok", "source_hash": "a" * 64, "byte_count": 100,
        "page_count": 1, "version": "synthetic-receipt-v1", **patch}
    with pytest.raises(ValueError):
        decode_receipt(json.dumps(packet).encode())


def test_ipc_json_receipt_and_error_contract():
    packet = {"status": "ok", "source_hash": "a" * 64, "byte_count": 100,
        "page_count": 1, "version": "synthetic-receipt-v1"}
    assert decode_receipt(json.dumps(packet).encode()) == Receipt("a" * 64, 100, 1)
    assert decode_receipt(b'{"status":"error","code":"synthetic_worker_failed"}') is None
    with pytest.raises(ValueError):
        decode_receipt(b"not json")


def test_failure_to_start_process_releases_content_and_reservation(environment, monkeypatch):
    engine, sim, _ = setup(environment)
    from multiprocessing.process import BaseProcess
    def fail_start(self):
        raise OSError("synthetic start failure")
    with Coordinator(engine) as coordinator:
        task = read(coordinator, sim)
        entry = coordinator._queue[task]
        monkeypatch.setattr(BaseProcess, "start", fail_start)
        assert coordinator.run_once().reason == "synthetic_worker_failed"
        assert state(engine, task) == ("expired", "synthetic_worker_failed")
        assert not entry.content and coordinator.retained_bytes == 0


def test_only_one_runner_and_renewal_during_work(environment):
    engine, sim, _ = setup(environment)
    with Coordinator(engine, ttl=2, worker_delay=3) as coordinator:
        task = read(coordinator, sim)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(coordinator.run_once)
            wait_running(engine, task)
            with pytest.raises(DomainError) as error:
                coordinator.run_once()
            assert error.value.code == "admission_executor_busy"
            assert future.result(timeout=10).state == "finished"
        with transaction(engine) as db:
            assert db.get(CoordinatorLease, 1).expires_at > now()


def test_leader_token_and_epoch_checked_for_atomic_admission(environment):
    engine, sim, inspection = setup(environment)
    with Coordinator(engine) as coordinator:
        forged = leadership.Identity(coordinator.identity.epoch, "wrong-token")
        with pytest.raises(DomainError):
            admission.admit_synthetic(engine, sim["owner_id"], sim["id"], 1,
                "forged-coordinator", inspection, action="read_invoice", _coordinator=forged)
        with transaction(engine) as db:
            assert db.scalar(select(func.count()).select_from(InvoiceAdmission)) == 0
            assert db.get(CoordinatorLease, 1).token_hash != coordinator.identity.token


def test_missing_content_same_epoch_expires_without_recreating_payload(environment):
    engine, sim, _ = setup(environment)
    with Coordinator(engine) as coordinator:
        task = read(coordinator, sim)
        # Simula perda efêmera após falha de confirmação/rollback da fila.
        with coordinator._lock:
            coordinator._drop(task)
        coordinator.sweep()
        assert state(engine, task) == ("expired", "content_lost")
        assert read(coordinator, sim) == task
        assert coordinator.pending_count == coordinator.retained_bytes == 0


def test_takeover_rollback_restores_epoch_and_recovery_states(environment, monkeypatch):
    from contextlib import contextmanager
    engine, sim, _ = setup(environment)
    previous = Coordinator(engine)
    try:
        task = read(previous, sim)
        expire_leader(engine)
        @contextmanager
        def rollback(engine, **kwargs):
            with transaction(engine, **kwargs) as db:
                yield db
                db.flush()
                raise RuntimeError("synthetic election rollback")
        monkeypatch.setattr(leadership, "transaction", rollback)
        with pytest.raises(RuntimeError):
            Coordinator(engine)
        with transaction(engine) as db:
            assert db.get(CoordinatorLease, 1).epoch == previous.identity.epoch
            assert db.get(SimulationTask, task).status == "queued"
    finally:
        previous.close()


def test_migration_preserves_admissions_and_reversible_metadata(environment):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect
    engine, sim, _ = setup(environment)
    with Coordinator(engine) as coordinator:
        task = read(coordinator, sim)
    cfg = Config("alembic.ini")
    cfg.attributes["settings"] = environment.settings
    command.downgrade(cfg, "0005_invoice_admissions")
    assert "coordinator_lease" not in inspect(engine).get_table_names()
    assert "coordinator_epoch" not in {c["name"] for c in inspect(engine).get_columns("invoice_admissions")}
    command.upgrade(cfg, "head")
    command.check(cfg)
    with transaction(engine) as db:
        assert db.get(InvoiceAdmission, task).coordinator_epoch is None
        assert db.get(SimulationTask, task).status == "expired"
    with engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
