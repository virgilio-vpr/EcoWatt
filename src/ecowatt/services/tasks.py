"""Ciclo de vida transacional; não inicia workers nem guarda payloads de arquivos."""
import secrets

from sqlalchemy import select, update

from ecowatt.db.models import AuditEvent, Simulation, SimulationTask, User, now
from ecowatt.db.session import transaction
from ecowatt.errors import DomainError
from ecowatt.security.tokens import digest, new_token

ACTIVE = ("queued", "running")


def cancel_tasks(db, simulation_id, reason):
    db.execute(update(SimulationTask).where(SimulationTask.simulation_id == simulation_id,
        SimulationTask.status.in_(ACTIVE)).values(status="cancelled", lease_hash=None,
        lease_expires_at=None, ended_at=now(), reason=reason))


def reserve(db, actor, simulation_id, revision):
    from ecowatt.services.simulations import require_simulation
    actor = db.get(User, actor.id, populate_existing=True)
    if not actor or actor.status != "active":
        raise DomainError("task_unavailable", "Operação indisponível.", 409)
    simulation = require_simulation(db, actor, simulation_id, revision)
    other = db.scalar(select(SimulationTask.id).join(Simulation).where(
        Simulation.owner_id == simulation.owner_id, SimulationTask.status.in_(ACTIVE),
        SimulationTask.simulation_id != simulation.id).limit(1))
    if other:
        raise DomainError("simulation_processing_limit", "Já há outra simulação em processamento.", 409)
    task = SimulationTask(simulation_id=simulation.id, actor_id=actor.id, revision=revision)
    db.add(task)
    db.flush()
    return task.id


def require_task(db, task_id):
    from ecowatt.services.simulations import require_simulation
    task = db.get(SimulationTask, task_id, populate_existing=True)
    if task is None or task.status not in ACTIVE:
        raise DomainError("task_unavailable", "Operação cancelada, encerrada ou indisponível.", 409)
    actor = db.get(User, task.actor_id, populate_existing=True)
    if not actor or actor.status != "active":
        raise DomainError("task_unavailable", "Operação indisponível.", 409)
    simulation = require_simulation(db, actor, task.simulation_id, task.revision)
    from ecowatt.db.admissions import InvoiceAdmission
    admission = db.get(InvoiceAdmission, task.id)
    if admission is not None and admission.coordinator_epoch is not None:
        from ecowatt.services.leadership import require_epoch
        require_epoch(db, admission.coordinator_epoch)
    return task, simulation


def claim(engine, task_id, executor_id, ttl=60):
    if not executor_id or len(executor_id) > 64 or not 1 <= ttl <= 300:
        raise ValueError("Executor/validade inválidos")
    lease = new_token()
    with transaction(engine, write=True) as db:
        task, _ = require_task(db, task_id)
        from ecowatt.db.admissions import InvoiceAdmission
        if db.get(InvoiceAdmission, task_id) is not None and db.scalar(
                select(InvoiceAdmission.task_id).join(SimulationTask).where(
                    SimulationTask.status == "running").limit(1)):
            raise DomainError("admission_executor_busy", "Executor de leitura ocupado.", 409)
        if task.status != "queued" or db.scalar(select(SimulationTask.id).where(
                SimulationTask.simulation_id == task.simulation_id, SimulationTask.status == "running").limit(1)):
            raise DomainError("task_unavailable", "Operação já assumida ou unidade ocupada.", 409)
        task.status, task.executor_id = "running", executor_id
        task.lease_hash, task.lease_expires_at = digest(lease), now() + ttl
    return lease


def require_lease(db, task_id, lease):
    task, simulation = require_task(db, task_id)
    if (task.status != "running" or task.lease_expires_at <= now()
            or not secrets.compare_digest(task.lease_hash, digest(lease))):
        raise DomainError("task_unavailable", "Executor inválido ou operação vencida.", 409)
    return task, simulation


def heartbeat(engine, task_id, lease, ttl=60):
    if not 1 <= ttl <= 300:
        raise ValueError("Validade inválida")
    with transaction(engine, write=True) as db:
        task, _ = require_lease(db, task_id, lease)
        task.lease_expires_at = now() + ttl


def finish(engine, task_id, lease, persist):
    """Callback interno grava somente dados estruturados, após revalidação atômica.

    Trabalho pesado deve terminar antes desta chamada. Callback não faz rede/OCR,
    não chama commit e não recebe documentos por esta infraestrutura.
    """
    with transaction(engine, write=True) as db:
        task, simulation = require_lease(db, task_id, lease)
        result = persist(db, simulation)
        task.status, task.lease_hash, task.lease_expires_at = "finished", None, None
        task.ended_at = now()
        db.add(AuditEvent(actor_id=task.actor_id, action="task_finished", resource_id=task.id))
        return result


def expire(engine):
    """Recuperação explícita apenas de leases vencidas; nunca no startup."""
    with transaction(engine, write=True) as db:
        db.execute(update(SimulationTask).where(SimulationTask.status == "running",
            SimulationTask.lease_expires_at <= now()).values(status="expired", lease_hash=None,
            lease_expires_at=None, ended_at=now(), reason="lease_expired"))
