"""Confirmação mínima, seleção explícita e guards de prontidão; só sintéticos."""
import json
from itertools import combinations

from sqlalchemy import select
from pydantic import ValidationError

from ecowatt.db.invoices import (FieldDependency, Invoice, InvoiceConfirmation, InvoiceItem,
    InvoiceMeasurement, InvoiceSelection)
from ecowatt.db.models import AuditEvent, User, new_id
from ecowatt.errors import DomainError
from ecowatt.invoice_confirmation import ConfirmationInput, SelectionInput
from ecowatt.services.invoice_review import current_fields, targets
from ecowatt.services.invoices import require_invoice, scalar
from ecowatt.services.simulations import require_simulation
from ecowatt.security.tokens import digest

POLICY = "synthetic-confirmation-v1"
CRITICAL_HEADER = ("consumer_unit_id", "holder_name", "printed_address_line", "printed_city", "printed_state",
    "competence", "cycle_start", "cycle_end", "cycle_days", "subgroup", "modality", "customer_class", "invoice_total")


def reject(code, status=409):
    raise DomainError(code, "Consulte as pendências e revisões antes de confirmar.", status)


def content_hash(db, invoice):
    latest = current_fields(db, invoice.id)
    mapped = targets(db, invoice)
    measurements = list(db.scalars(select(InvoiceMeasurement).where(InvoiceMeasurement.invoice_id == invoice.id)))
    return digest(json.dumps({"fields": {p: scalar(getattr(target, key)) for p, (target, key, _) in mapped.items()},
        "versions": {p: row.id for p, row in latest.items()},
        "posts": {m.id: m.post for m in measurements}, "coverage": invoice.coverage,
        "distributor": invoice.distributor_id, "source_hash": invoice.source_hash}, sort_keys=True))


def confirmation_checks(db, sim, invoice):
    """Pendências globais e limitações de módulos são coisas distintas."""
    from ecowatt.services.invoice_validation import financial_checks
    pending, limitations = set(), set()
    latest = current_fields(db, invoice.id)
    if invoice.source_kind != "synthetic" or invoice.contract_version != "invoice-v0.3":
        pending.add("invoice_confirmation_not_supported")
    for key in CRITICAL_HEADER:
        row = latest.get("header." + key)
        if row is None or row.value is None or row.state not in ("confirmed", "zero_confirmed", "estimated"):
            pending.add("header." + key)
    if invoice.consumer_unit_id != sim.unit_identifier or invoice.distributor_id != sim.distributor_id:
        pending.add("invoice_identity_conflict")
    if invoice.modality == "unknown":
        pending.add("header.modality")
    if invoice.cycle_start and invoice.cycle_end:
        if invoice.cycle_start >= invoice.cycle_end:
            pending.add("cycle_period_invalid")
        elif invoice.cycle_days != (invoice.cycle_end - invoice.cycle_start).days:
            limitations.add("cycle_days_disagreement")
    items = list(db.scalars(select(InvoiceItem).where(InvoiceItem.invoice_id == invoice.id)))
    for item in items:
        for key in ("amount", "type"):
            row = latest.get(f"items.{item.id}.{key}")
            if row is None or row.value is None or row.state not in ("confirmed", "zero_confirmed", "estimated"):
                pending.add(f"items.{item.id}.{key}")
        if item.type == "unclassified":
            pending.add(f"items.{item.id}.type")
    if any(c["result"] == "blocking" for c in financial_checks(db, invoice)):
        pending.add("financial_review_required")
    if any(row.state == "estimated" for row in latest.values()):
        limitations.add("estimated_data")
    if invoice.market == "unknown":
        limitations.add("market_unconfirmed")
    elif invoice.market == "free":
        limitations.add("free_market_scope")
    measurements = {m.post: m for m in db.scalars(select(InvoiceMeasurement).where(InvoiceMeasurement.invoice_id == invoice.id))}
    posts = ("single",) if invoice.modality == "green" else ("peak", "off_peak")
    if any(post not in measurements or measurements[post].contracted_demand is None for post in posts):
        limitations.add("contracted_demand_incomplete")
    if any(post not in measurements or measurements[post].measured_active_demand is None for post in ("peak", "off_peak")):
        limitations.add("measured_demand_incomplete")
    # Derivados presentes nunca podem depender de uma versão antiga/inválida.
    ids = {row.id: row for row in latest.values()}
    for edge in db.scalars(select(FieldDependency).where(FieldDependency.invoice_id == invoice.id)):
        target = ids.get(edge.field_id)
        if target and target.value is not None and (edge.input_id not in ids or ids[edge.input_id].value is None):
            pending.add("stale_field_dependency")
    return sorted(pending), sorted(limitations)


def current_confirmation(db, sim, invoice):
    # Ordinal dataset_revision é único para cada comando confirmado nesta simulação.
    row = db.scalar(select(InvoiceConfirmation).where(InvoiceConfirmation.invoice_id == invoice.id,
        InvoiceConfirmation.invoice_revision == invoice.revision, InvoiceConfirmation.unit_revision == sim.revision,
        InvoiceConfirmation.policy_version == POLICY).order_by(InvoiceConfirmation.dataset_revision.desc()))
    if row and row.content_hash == content_hash(db, invoice):
        return row
    return None


def overlap(left, right):
    return bool(left.cycle_start and left.cycle_end and right.cycle_start and right.cycle_end
        and left.cycle_start < right.cycle_end and right.cycle_start < left.cycle_end)


def duplicate_groups(invoices, previous=()):
    """Componentes conexos: chegada de terceiro documento invalida a escolha antiga."""
    links = {i.id: set() for i in invoices}
    evidence = {}
    historical = set()
    for members in previous:
        surviving = set(members) & links.keys()
        historical |= surviving
        for identity in surviving:
            links[identity] |= surviving - {identity}
    for left, right in combinations(invoices, 2):
        reasons = []
        if left.invoice_number and left.invoice_number == right.invoice_number and left.distributor_id == right.distributor_id:
            reasons.append("same_document_number")
        if left.competence and left.competence == right.competence:
            reasons.append("same_competence")
        if overlap(left, right):
            reasons.append("overlapping_cycles")
        if reasons:
            links[left.id].add(right.id)
            links[right.id].add(left.id)
            evidence[f"{left.id}:{right.id}"] = reasons
    remaining, groups = set(links), []
    while remaining:
        todo, group = [min(remaining)], set()
        while todo:
            current = todo.pop()
            if current in group:
                continue
            group.add(current)
            todo.extend(links[current] - group)
        remaining -= group
        if len(group) > 1 or group & historical:
            groups.append({"member_versions": {i.id: i.revision for i in invoices if i.id in group},
                "evidence": sorted({code for pair, codes in evidence.items()
                    if pair.split(":")[0] in group for code in codes} | ({"previous_selection"} if group & historical else set()))})
    return groups


def selection_groups(db, sim, invoices):
    previous = db.scalars(select(InvoiceSelection).where(InvoiceSelection.simulation_id == sim.id))
    return duplicate_groups(invoices, (row.member_versions for row in previous))


def group_selection(db, sim, group):
    rows = db.scalars(select(InvoiceSelection).where(InvoiceSelection.simulation_id == sim.id,
        InvoiceSelection.unit_revision == sim.revision).order_by(InvoiceSelection.dataset_revision.desc()))
    return next((row for row in rows if row.member_versions == group["member_versions"]), None)


def command_context(db, actor, simulation_id, resource_id, action, key, payload):
    actor = db.get(User, actor.id, populate_existing=True)
    if actor is None or actor.status != "active":
        reject("task_unavailable")
    sim = require_simulation(db, actor, simulation_id)
    fingerprint = digest(json.dumps(payload.model_dump(mode="json"), sort_keys=True))
    previous = db.scalar(select(AuditEvent).where(AuditEvent.actor_id == actor.id, AuditEvent.action == action,
        AuditEvent.resource_id == resource_id, AuditEvent.changes["key_hash"].as_string() == digest(key)))
    if previous:
        if previous.changes["request_hash"] != fingerprint:
            reject("idempotency_conflict")
        return actor, sim, previous.changes["receipt"], fingerprint
    require_simulation(db, actor, simulation_id, payload.expected_revision)
    if sim.dataset_revision != payload.expected_dataset_revision:
        reject("dataset_revision_conflict")
    return actor, sim, None, fingerprint


def record_receipt(db, actor, resource_id, action, key, fingerprint, receipt, reason):
    db.add(AuditEvent(actor_id=actor.id, resource_id=resource_id, action=action,
        changes={"key_hash": digest(key), "request_hash": fingerprint, "receipt": receipt, "reason_code": reason}))
    db.flush()


def validated(payload, cls):
    try:
        return cls.model_validate(payload.model_dump() if isinstance(payload, cls) else payload)
    except (ValueError, TypeError, ValidationError):
        reject("invalid_invoice_confirmation", 422)


def confirm_invoice(db, actor, simulation_id, invoice_id, key, payload):
    payload = validated(payload, ConfirmationInput)
    # Recurso removido não pode ser ressuscitado por um recibo histórico.
    invoice = require_invoice(db, actor, simulation_id, invoice_id)
    actor, sim, receipt, fingerprint = command_context(db, actor, simulation_id, invoice_id,
        "invoice_confirmed", key, payload)
    if receipt:
        return receipt
    if invoice.revision != payload.expected_invoice_revision:
        reject("invoice_revision_conflict")
    pending, limitations = confirmation_checks(db, sim, invoice)
    if pending:
        reject("invoice_confirmation_blocked")
    if set(payload.accepted_limitations) != set(limitations):
        reject("invoice_limitations_ack_required")
    sim.dataset_revision += 1
    sim.updated_by = actor.id
    invoice.dataset_revision = sim.dataset_revision
    invoice.status = "ready"
    confirmation = InvoiceConfirmation(id=new_id(), invoice_id=invoice.id, actor_id=actor.id,
        unit_revision=sim.revision, invoice_revision=invoice.revision, dataset_revision=sim.dataset_revision,
        content_hash=content_hash(db, invoice), policy_version=POLICY, reason_code=payload.reason_code,
        field_versions={path: row.id for path, row in current_fields(db, invoice.id).items()},
        accepted_limitations=limitations)
    db.add(confirmation)
    receipt = {"confirmation_id": confirmation.id, "invoice_id": invoice.id,
        "invoice_revision": invoice.revision, "dataset_revision": sim.dataset_revision}
    record_receipt(db, actor, invoice_id, "invoice_confirmed", key, fingerprint, receipt, payload.reason_code)
    return receipt


def select_invoices(db, actor, simulation_id, key, payload):
    payload = validated(payload, SelectionInput)
    actor, sim, receipt, fingerprint = command_context(db, actor, simulation_id, simulation_id,
        "invoices_selected", key, payload)
    members = {str(k): v for k, v in payload.member_versions.items()}
    # Mesmo replay após remoção não retorna IDs que já deixaram o conjunto.
    invoices = list(db.scalars(select(Invoice).where(Invoice.simulation_id == sim.id).order_by(Invoice.id)))
    if not set(members) <= {i.id for i in invoices}:
        reject("not_found", 404)
    if receipt:
        return receipt
    groups = selection_groups(db, sim, invoices)
    if not any(group["member_versions"] == members for group in groups):
        reject("invoice_selection_conflict")
    selected = sorted(str(i) for i in payload.included_ids)
    if payload.relationship == "distinct_periods":
        records = [i for i in invoices if i.id in members]
        if any(not i.cycle_start or not i.cycle_end or i.cycle_start >= i.cycle_end for i in records) or any(overlap(a, b) for a, b in combinations(records, 2)):
            reject("overlapping_distinct_periods")
        if any(a.invoice_number and a.invoice_number == b.invoice_number and a.distributor_id == b.distributor_id for a, b in combinations(records, 2)):
            reject("duplicate_document_identity")
    sim.dataset_revision += 1
    sim.updated_by = actor.id
    row = InvoiceSelection(id=new_id(), simulation_id=sim.id, actor_id=actor.id, unit_revision=sim.revision,
        dataset_revision=sim.dataset_revision, member_versions=members, included_ids=selected,
        relationship=payload.relationship, reason_code=payload.reason_code)
    db.add(row)
    receipt = {"selection_id": row.id, "dataset_revision": sim.dataset_revision, "included_ids": selected}
    record_receipt(db, actor, simulation_id, "invoices_selected", key, fingerprint, receipt, payload.reason_code)
    return receipt


def require_ready_dataset(db, actor, simulation_id, revision, dataset_revision):
    """Guard interno reutilizável pelo futuro cálculo, dentro da transação de escrita."""
    from ecowatt.services.invoice_validation import dataset_readiness
    actor = db.get(User, actor.id, populate_existing=True)
    if actor is None or actor.status != "active":
        reject("task_unavailable")
    sim = require_simulation(db, actor, simulation_id, revision)
    if sim.dataset_revision != dataset_revision:
        reject("dataset_revision_conflict")
    result = dataset_readiness(db, actor, simulation_id)
    if not result["ready_for_calculation"]:
        reject("dataset_not_ready")
    return [entry["invoice_id"] for entry in result["invoices"] if entry["included"]]


def list_selections(db, actor, simulation_id, page, page_size):
    from sqlalchemy import func
    sim = require_simulation(db, actor, simulation_id)
    query = select(InvoiceSelection).where(InvoiceSelection.simulation_id == sim.id)
    rows = db.scalars(query.order_by(InvoiceSelection.dataset_revision.desc())
        .offset((page - 1) * page_size).limit(page_size))
    names = ("id", "actor_id", "unit_revision", "dataset_revision", "relationship", "reason_code",
        "member_versions", "included_ids", "created_at")
    return {"items": [{name: getattr(row, name) for name in names} for row in rows],
        "total": db.scalar(select(func.count()).select_from(query.subquery())), "page": page, "page_size": page_size}
