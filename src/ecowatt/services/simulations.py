import json

from sqlalchemy import delete, func, select

from ecowatt.db.models import AuditEvent, Distributor, IdempotencyKey, Simulation, User, now
from ecowatt.errors import DomainError
from ecowatt.security.tokens import digest
from ecowatt.services.tasks import cancel_tasks


def require_admin(actor):
    if actor.role != "admin":
        raise DomainError("forbidden", "Acesso não autorizado.", 403)


def require_simulation(db, actor, simulation_id, revision=None):
    # Revalidar tombstone/revisão mesmo se a sessão já carregou o objeto antes.
    simulation = db.get(Simulation, str(simulation_id), populate_existing=True)
    if (not simulation or simulation.status == "deleted"
            or (actor.role != "admin" and simulation.owner_id != actor.id)):
        raise DomainError("not_found", "Recurso não encontrado.", 404)
    if revision is not None and simulation.revision != revision:
        raise DomainError("simulation_revision_conflict", "Atualize os dados antes de continuar.", 409)
    return simulation


def serialize(simulation):
    fields = ("id", "owner_id", "company_id", "created_by", "updated_by", "status", "revision",
              "distributor_id", "unit_identifier", "holder_name", "address_line", "city", "state",
              "postal_code", "created_at")
    return {**{name: getattr(simulation, name) for name in fields},
            "unit_saved": simulation.unit_saved_at is not None}


def create_simulation(db, actor, owner_id, key):
    if owner_id != actor.id:
        require_admin(actor)
    owner = db.get(User, owner_id)
    if not owner or owner.status != "active":
        raise DomainError("not_found", "Titular não encontrado.", 404)
    fingerprint = digest(json.dumps({"owner_id": owner_id}, sort_keys=True))
    previous = db.scalar(select(IdempotencyKey).where(IdempotencyKey.actor_id == actor.id,
                         IdempotencyKey.key_hash == digest(key)))
    if previous:
        if previous.request_hash != fingerprint:
            raise DomainError("idempotency_conflict", "Chave já usada em outro pedido.", 409)
        return require_simulation(db, actor, previous.simulation_id)
    occupied = set(db.scalars(select(Simulation.slot).where(Simulation.owner_id == owner_id,
                              Simulation.status != "deleted")))
    available = {1, 2} - occupied
    if not available:
        raise DomainError("simulation_limit_reached", "Limite de duas simulações atingido.", 409)
    simulation = Simulation(owner_id=owner_id, company_id=owner.company_id, created_by=actor.id,
                            updated_by=actor.id, slot=min(available))
    db.add(simulation)
    db.flush()
    db.add(IdempotencyKey(actor_id=actor.id, key_hash=digest(key), request_hash=fingerprint,
                          simulation_id=simulation.id))
    db.add(AuditEvent(actor_id=actor.id, action="simulation_created", resource_id=simulation.id))
    return simulation


def save_unit(db, actor, simulation_id, payload):
    simulation = require_simulation(db, actor, simulation_id, payload.expected_revision)
    if not db.get(Distributor, str(payload.distributor_id)):
        raise DomainError("invalid_distributor", "Selecione distribuidora do catálogo.", 422, ["distributor_id"])
    if simulation.unit_saved_at is not None and (simulation.unit_identifier != payload.unit_identifier
                or simulation.distributor_id != str(payload.distributor_id)):
        raise DomainError("unit_identity_conflict", "Outra unidade exige nova simulação.", 409)
    values = payload.model_dump(exclude={"expected_revision"}, mode="json")
    before = {name: getattr(simulation, name) for name in values}
    for name, value in values.items():
        setattr(simulation, name, value)
    simulation.unit_saved_at, simulation.updated_by = now(), actor.id
    simulation.revision += 1
    cancel_tasks(db, simulation.id, "revision_changed")
    db.add(AuditEvent(actor_id=actor.id, action="unit_saved", resource_id=simulation.id,
                      changes={"before": before, "after": values}))
    return simulation


def delete_simulation(db, actor, simulation_id, payload):
    if not payload.confirm:
        raise DomainError("confirmation_required", "Confirme a exclusão.", 422, ["confirm"])
    simulation = require_simulation(db, actor, simulation_id, payload.expected_revision)
    simulation.status, simulation.slot, simulation.deleted_at = "deleted", None, now()
    simulation.revision += 1
    simulation.updated_by = actor.id
    cancel_tasks(db, simulation.id, "simulation_deleted")
    # Filhos faturáveis são removidos na mesma transação do tombstone/lease.
    # Itens primeiro: a referência à medição usa RESTRICT deliberadamente.
    from ecowatt.db.invoices import Invoice, InvoiceItem
    invoice_ids = select(Invoice.id).where(Invoice.simulation_id == simulation.id)
    db.execute(delete(InvoiceItem).where(InvoiceItem.invoice_id.in_(invoice_ids)))
    db.execute(delete(Invoice).where(Invoice.simulation_id == simulation.id))
    db.add(AuditEvent(actor_id=actor.id, action="simulation_deleted", resource_id=simulation.id))


def list_simulations(db, actor, owner_id, page, page_size):
    if owner_id != actor.id:
        require_admin(actor)
    query = select(Simulation).where(Simulation.owner_id == owner_id, Simulation.status != "deleted")
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = db.scalars(query.order_by(Simulation.created_at, Simulation.id)
                      .offset((page - 1) * page_size).limit(page_size))
    return {"items": [serialize(item) for item in items], "total": total, "page": page,
            "page_size": page_size, "limit": 2}


def company_data(company):
    return {name: getattr(company, name) for name in
            ("id", "name", "phone", "address_line", "city", "state", "postal_code")}
