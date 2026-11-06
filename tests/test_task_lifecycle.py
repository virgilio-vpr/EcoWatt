from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from sqlalchemy import select

from ecowatt.db.models import Simulation, SimulationTask, User, now
from ecowatt.db.session import transaction
from ecowatt.errors import DomainError
from ecowatt.services import tasks
from ecowatt.security.tokens import digest
from test_simulations import create


def setup_task(environment):
    client = environment.client().login()
    simulation = create(client).json()
    with transaction(environment.app.state.engine, write=True) as db:
        actor = db.get(User, simulation["owner_id"])
        task_id = tasks.reserve(db, actor, simulation["id"], simulation["revision"])
    return client, simulation, task_id


def test_delete_cancels_queued_and_running_and_rejects_late_worker(environment):
    engine = environment.app.state.engine
    client, simulation, task_id = setup_task(environment)
    lease = tasks.claim(engine, task_id, "synthetic-worker")
    with transaction(engine, write=True) as db:
        actor = db.get(User, simulation["owner_id"])
        queued = tasks.reserve(db, actor, simulation["id"], 1)
    started, release = Event(), Event()
    persisted = []

    def worker():
        started.set()
        assert release.wait(5)
        try:
            tasks.finish(engine, task_id, lease, lambda db, sim: persisted.append(sim.id))
        except DomainError as error:
            return error.code
        return "unexpected_success"

    with ThreadPoolExecutor(max_workers=1) as pool:
        result = pool.submit(worker)
        try:
            assert started.wait(2)
            response = client.request("DELETE", "/api/v1/simulations/" + simulation["id"],
                json={"confirm": True, "expected_revision": 1})
            assert response.status_code == 204
        finally:
            release.set()
        assert result.result(5) == "task_unavailable"
    assert persisted == []
    with transaction(engine) as db:
        for key in (task_id, queued):
            task = db.get(SimulationTask, key)
            assert task.status == "cancelled" and task.lease_hash is None and task.lease_expires_at is None
        assert db.get(Simulation, simulation["id"]).slot is None
    assert create(client, "new-after-deletion").status_code == 201
    with pytest.raises(DomainError):
        tasks.claim(engine, queued, "late-worker")
    with pytest.raises(DomainError):
        tasks.heartbeat(engine, task_id, lease)


def test_finish_is_atomic_single_use_and_executor_bound(environment):
    engine = environment.app.state.engine
    _, simulation, task_id = setup_task(environment)
    lease = tasks.claim(engine, task_id, "worker-1")
    with transaction(engine) as db:
        assert db.get(SimulationTask, task_id).lease_hash == digest(lease)
    with pytest.raises(DomainError):
        tasks.claim(engine, task_id, "worker-2")
    with pytest.raises(DomainError):
        tasks.finish(engine, task_id, "forged-lease", lambda db, sim: setattr(sim, "holder_name", "wrong"))

    def fail(db, sim):
        sim.holder_name = "must rollback"
        db.flush()
        raise ValueError("synthetic failure")

    with pytest.raises(ValueError):
        tasks.finish(engine, task_id, lease, fail)
    with transaction(engine) as db:
        assert db.get(Simulation, simulation["id"]).holder_name is None
        assert db.get(SimulationTask, task_id).status == "running"
    tasks.heartbeat(engine, task_id, lease)
    tasks.finish(engine, task_id, lease, lambda db, sim: setattr(sim, "holder_name", "Synthetic result"))
    with transaction(engine) as db:
        assert db.get(Simulation, simulation["id"]).holder_name == "Synthetic result"
        task = db.get(SimulationTask, task_id)
        assert task.status == "finished" and task.lease_hash is None
    with pytest.raises(DomainError):
        tasks.finish(engine, task_id, lease, lambda db, sim: None)


def test_changed_revision_cancels_tasks_and_other_owner_is_denied(environment):
    engine = environment.app.state.engine
    client, simulation, task_id = setup_task(environment)
    lease = tasks.claim(engine, task_id, "worker")
    distributor = client.request("GET", "/api/v1/distributors").json()["items"][0]
    payload = {"expected_revision": 1, "distributor_id": distributor["id"], "unit_identifier": "synthetic-UC",
               "holder_name": "Synthetic", "address_line": "Example 1", "city": "Example", "state": "SP", "postal_code": "00000"}
    assert client.request("PATCH", "/api/v1/simulations/" + simulation["id"] + "/unit", json=payload).status_code == 200
    with pytest.raises(DomainError):
        tasks.finish(engine, task_id, lease, lambda db, sim: None)
    admin = environment.client().login("admin@ecowatt.test")
    private = create(admin).json()
    with pytest.raises(DomainError), transaction(engine, write=True) as db:
        actor = db.get(User, simulation["owner_id"])
        tasks.reserve(db, actor, private["id"], private["revision"])
    with transaction(engine) as db:
        assert db.get(SimulationTask, task_id).reason == "revision_changed"


def test_expiration_only_affects_expired_lease_not_startup(environment):
    engine = environment.app.state.engine
    _, _, task_id = setup_task(environment)
    lease = tasks.claim(engine, task_id, "worker")
    tasks.expire(engine)
    with transaction(engine, write=True) as db:
        task = db.get(SimulationTask, task_id)
        assert task.status == "running"
        task.lease_expires_at = now() - 1
    with pytest.raises(DomainError):
        tasks.finish(engine, task_id, lease, lambda db, sim: None)
    tasks.expire(engine)
    with transaction(engine) as db:
        assert db.get(SimulationTask, task_id).status == "expired"


def test_delete_rollback_restores_task_and_slot_together(environment):
    from ecowatt.schemas import DeleteInput
    from ecowatt.services.simulations import delete_simulation
    engine = environment.app.state.engine
    _, simulation, task_id = setup_task(environment)
    tasks.claim(engine, task_id, "worker")
    with pytest.raises(RuntimeError), transaction(engine, write=True) as db:
        actor = db.get(User, simulation["owner_id"])
        delete_simulation(db, actor, simulation["id"], DeleteInput(confirm=True, expected_revision=1))
        db.flush()
        raise RuntimeError("rollback both")
    with transaction(engine) as db:
        assert db.get(Simulation, simulation["id"]).slot == 1
        assert db.get(SimulationTask, task_id).status == "running"


def test_only_one_executor_can_claim_and_one_simulation_per_owner(environment):
    engine = environment.app.state.engine
    client, simulation, task_id = setup_task(environment)
    other = create(client, "second-task-simulation").json()
    with pytest.raises(DomainError), transaction(engine, write=True) as db:
        actor = db.get(User, simulation["owner_id"])
        tasks.reserve(db, actor, other["id"], other["revision"])

    def claim(executor):
        try:
            tasks.claim(engine, task_id, executor)
            return "claimed"
        except DomainError:
            return "rejected"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(claim, ["worker-one", "worker-two"])) == ["claimed", "rejected"]
