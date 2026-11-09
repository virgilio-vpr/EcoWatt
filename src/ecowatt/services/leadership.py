"""Controle explícito de liderança. Nunca executado no startup da aplicação."""
from dataclasses import dataclass, field
import secrets

from sqlalchemy import select

from ecowatt.db.admissions import InvoiceAdmission
from ecowatt.db.coordinator import CoordinatorLease
from ecowatt.db.models import SimulationTask, now
from ecowatt.db.session import transaction
from ecowatt.errors import DomainError
from ecowatt.security.tokens import digest, new_token


@dataclass(frozen=True)
class Identity:
    epoch: int
    token: str = field(repr=False)


def unavailable():
    raise DomainError("coordinator_unavailable", "Coordenador indisponível. Tente novamente.", 503)


def require_leader(db, identity):
    row = db.get(CoordinatorLease, 1, populate_existing=True)
    if (row is None or row.epoch != identity.epoch or row.expires_at <= now()
            or not secrets.compare_digest(row.token_hash, digest(identity.token))):
        unavailable()
    return row


def require_epoch(db, epoch):
    row = db.get(CoordinatorLease, 1, populate_existing=True)
    if row is None or row.epoch != epoch or row.expires_at <= now():
        unavailable()


def recover(db, epoch):
    """Somente queued de gerações perdidas e running cuja lease já venceu.

    Running com lease viva não é alterada por takeover. O fencing impede
    heartbeat/finish da geração antiga, mesmo antes da recuperação.
    """
    rows = db.scalars(select(SimulationTask).join(InvoiceAdmission).where(
        InvoiceAdmission.coordinator_epoch.is_not(None),
        SimulationTask.status.in_(("queued", "running"))))
    for task in rows:
        admission = db.get(InvoiceAdmission, task.id)
        if (task.status == "queued" and admission.coordinator_epoch != epoch
                or task.status == "running" and task.lease_expires_at <= now()):
            task.status, task.ended_at = "expired", now()
            task.reason = "content_lost" if task.lease_hash is None else "lease_expired"
            task.lease_hash = task.lease_expires_at = None


def acquire(engine, ttl=60):
    if type(ttl) is not int or not 2 <= ttl <= 300:
        raise ValueError("Validade inválida")
    token = new_token()
    with transaction(engine, write=True) as db:
        row = db.get(CoordinatorLease, 1)
        if row is not None and row.expires_at > now():
            unavailable()
        epoch = row.epoch + 1 if row else 1
        if row is None:
            row = CoordinatorLease(id=1, epoch=epoch, token_hash=digest(token), expires_at=now() + ttl)
            db.add(row)
        else:
            row.epoch, row.token_hash, row.expires_at = epoch, digest(token), now() + ttl
        recover(db, epoch)
    return Identity(epoch, token)


def renew(engine, identity, ttl=60):
    if type(ttl) is not int or not 2 <= ttl <= 300:
        raise ValueError("Validade inválida")
    with transaction(engine, write=True) as db:
        require_leader(db, identity).expires_at = now() + ttl
        recover(db, identity.epoch)


def release(db, identity):
    require_leader(db, identity).expires_at = now()
