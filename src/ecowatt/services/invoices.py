"""Consulta interna com autorização herdada da simulação; sem rotas de upload."""
from datetime import date
from decimal import Decimal
from sqlalchemy import func, select

from ecowatt.db.invoices import Invoice
from ecowatt.errors import DomainError
from ecowatt.services.simulations import require_simulation


def require_invoice(db, actor, simulation_id, invoice_id, revision=None):
    simulation = require_simulation(db, actor, simulation_id, revision)
    invoice = db.scalar(select(Invoice).where(Invoice.id == invoice_id,
        Invoice.simulation_id == simulation.id).execution_options(populate_existing=True))
    if invoice is None:
        raise DomainError("not_found", "Recurso não encontrado.", 404)
    return invoice


def scalar(value):
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, date):
        return value.isoformat()
    return value


def serialize_invoice(db, invoice):
    from ecowatt.db.invoices import FieldDependency, FieldProvenance, InvoiceItem, InvoiceMeasurement, InvoiceConfirmation
    from ecowatt.invoice_result import HEADER, ITEM, MEASUREMENT
    def values(record, specs):
        return {key: scalar(getattr(record, key)) for key in specs}
    dependencies = {}
    for entry in db.scalars(select(FieldDependency).where(FieldDependency.invoice_id == invoice.id)):
        dependencies.setdefault(entry.field_id, []).append(entry.input_id)
    names = ("id", "field_path", "version", "value", "unit", "state", "origin", "coverage",
        "actor_id", "recorded_at", "reason_code", "hypothesis_code", "rule_version")
    return {**{name: getattr(invoice, name) for name in ("id", "simulation_id", "created_by", "revision",
        "dataset_revision", "contract_version", "source_kind", "status", "coverage")},
        "header": values(invoice, HEADER),
        "confirmations": [{name: getattr(row, name) for name in ("id", "actor_id", "unit_revision",
            "invoice_revision", "dataset_revision", "policy_version", "reason_code", "field_versions",
            "accepted_limitations", "created_at")} for row in db.scalars(select(InvoiceConfirmation)
                .where(InvoiceConfirmation.invoice_id == invoice.id).order_by(InvoiceConfirmation.dataset_revision))],
        "measurements": [{"id": m.id, "post": m.post, "fields": values(m, MEASUREMENT)} for m in
            db.scalars(select(InvoiceMeasurement).where(InvoiceMeasurement.invoice_id == invoice.id).order_by(InvoiceMeasurement.post))],
        "items": [{"id": i.id, "position": i.position, "measurement_id": i.measurement_id, "fields": values(i, ITEM)} for i in
            db.scalars(select(InvoiceItem).where(InvoiceItem.invoice_id == invoice.id).order_by(InvoiceItem.position))],
        "provenance": [{**{name: getattr(p, name) for name in names}, "inputs": sorted(dependencies.get(p.id, []))}
            for p in db.scalars(select(FieldProvenance).where(FieldProvenance.invoice_id == invoice.id)
                .order_by(FieldProvenance.field_path, FieldProvenance.version))]}


def list_invoices(db, actor, simulation_id, page, page_size):
    sim = require_simulation(db, actor, simulation_id)
    query = select(Invoice).where(Invoice.simulation_id == sim.id)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(Invoice.cycle_start.asc().nulls_last(),
        Invoice.cycle_end.asc().nulls_last(), Invoice.competence.asc().nulls_last(), Invoice.id)
        .offset((page - 1) * page_size).limit(page_size))
    return {"items": [{name: scalar(getattr(row, name)) for name in
        ("id", "status", "competence", "cycle_start", "cycle_end", "revision", "dataset_revision")} for row in rows],
        "total": total, "page": page, "page_size": page_size, "dataset_revision": sim.dataset_revision}


def remove_invoice(db, actor, simulation_id, invoice_id, payload):
    from ecowatt.db.admissions import InvoiceAdmission, InvoicePublication
    from ecowatt.db.models import AuditEvent, User
    from ecowatt.services.invoice_storage import delete_graph
    actor = db.get(User, actor.id, populate_existing=True)
    if actor is None or actor.status != "active":
        raise DomainError("task_unavailable", "Operação indisponível.", 409)
    if not payload.confirm:
        raise DomainError("confirmation_required", "Confirme a remoção.", 422)
    sim = require_simulation(db, actor, simulation_id, payload.expected_revision)
    invoice = require_invoice(db, actor, simulation_id, invoice_id)
    if sim.dataset_revision != payload.expected_dataset_revision:
        raise DomainError("dataset_revision_conflict", "Atualize o conjunto antes de remover.", 409)
    publication = db.scalar(select(InvoicePublication).where(InvoicePublication.invoice_id == invoice.id))
    if publication:
        row = db.get(InvoiceAdmission, publication.task_id)
        if row.simulation_id != sim.id:
            raise DomainError("task_unavailable", "Vínculo inconsistente.", 409)
        row.removed = True
    delete_graph(db, invoice.id)
    sim.dataset_revision += 1
    sim.updated_by = actor.id
    db.add(AuditEvent(actor_id=actor.id, action="invoice_removed", resource_id=invoice.id))
