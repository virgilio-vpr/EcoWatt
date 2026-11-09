"""Revisão sintética atômica com histórico e invalidação transitiva."""
import json

from pydantic import ValidationError
from sqlalchemy import select

from ecowatt.db.invoices import (FieldDependency, FieldProvenance, InvoiceItem,
    InvoiceMeasurement)
from ecowatt.db.models import AuditEvent, User, new_id
from ecowatt.errors import DomainError
from ecowatt.invoice_result import HEADER, ITEM, MEASUREMENT, Item, Measurement, Value, normalize
from ecowatt.invoice_review import ReviewInput
from ecowatt.security.tokens import digest
from ecowatt.services.invoices import require_invoice
from ecowatt.services.simulations import require_simulation


def invalid(code="invalid_invoice_review", status=422):
    return DomainError(code, "Revisão inválida ou desatualizada.", status)


def current_fields(db, invoice_id):
    latest = {}
    for row in db.scalars(select(FieldProvenance).where(FieldProvenance.invoice_id == invoice_id)
            .order_by(FieldProvenance.version)):
        latest[row.field_path] = row
    return latest


def targets(db, invoice):
    output = {f"header.{key}": (invoice, key, spec) for key, spec in HEADER.items()}
    for model, prefix, specs in ((InvoiceItem, "items", ITEM), (InvoiceMeasurement, "measurements", MEASUREMENT)):
        for row in db.scalars(select(model).where(model.invoice_id == invoice.id)):
            output.update({f"{prefix}.{row.id}.{key}": (row, key, spec) for key, spec in specs.items()})
    return output


def review_invoice(db, actor, simulation_id, invoice_id, key, payload):
    # Também protege chamadas internas com objetos antigos ou entradas não validadas.
    try:
        payload = ReviewInput.model_validate(payload.model_dump() if isinstance(payload, ReviewInput) else payload)
    except (ValidationError, TypeError, ValueError):
        raise invalid() from None
    actor = db.get(User, actor.id, populate_existing=True)
    if actor is None or actor.status != "active":
        raise invalid("task_unavailable", 409)
    sim = require_simulation(db, actor, simulation_id)
    invoice = require_invoice(db, actor, simulation_id, invoice_id)
    if invoice.source_kind != "synthetic" or invoice.contract_version != "invoice-v0.3":
        raise invalid("invoice_review_not_supported", 409)
    fingerprint = digest(json.dumps(payload.model_dump(mode="json"), sort_keys=True, separators=(",", ":")))
    key_hash = digest(key)
    previous = db.scalar(select(AuditEvent).where(AuditEvent.actor_id == actor.id,
        AuditEvent.action == "invoice_reviewed", AuditEvent.resource_id == invoice.id,
        AuditEvent.changes["key_hash"].as_string() == key_hash))
    if previous:
        if previous.changes["request_hash"] != fingerprint:
            raise invalid("idempotency_conflict", 409)
        # Recibo histórico, nunca restaura valores ou libera conjunto posterior.
        return previous.changes["receipt"]
    require_simulation(db, actor, simulation_id, payload.expected_revision)
    if sim.dataset_revision != payload.expected_dataset_revision:
        raise invalid("dataset_revision_conflict", 409)
    if invoice.revision != payload.expected_invoice_revision:
        raise invalid("invoice_revision_conflict", 409)
    latest = current_fields(db, invoice.id)
    mapped = targets(db, invoice)
    changed = {edit.path for edit in payload.edits}
    edges = list(db.scalars(select(FieldDependency).where(FieldDependency.invoice_id == invoice.id)))
    by_id = {row.id: row for row in latest.values()}
    inputs = {}
    for edge in edges:
        inputs.setdefault(edge.field_id, []).append(edge.input_id)
    # Relações por caminho alcançam derivados de uma versão já obsoleta também.
    history = {row.id: row.field_path for row in db.scalars(select(FieldProvenance).where(FieldProvenance.invoice_id == invoice.id))}
    affected = set(changed)
    while True:
        following = {path for path, row in latest.items()
            if any(history[source] in affected for source in inputs.get(row.id, []))}
        if following <= affected:
            break
        affected |= following
    prepared = {}
    for edit in payload.edits:
        old = latest.get(edit.path)
        if edit.path not in mapped or old is None:
            raise invalid()
        if edit.expected_version != old.version:
            raise invalid("field_version_conflict", 409)
        try:
            typed, canonical = normalize(edit.field, mapped[edit.path][2])
        except (ValueError, TypeError):
            raise invalid() from None
        if len(set(edit.field.inputs)) != len(edit.field.inputs):
            raise invalid()
        for source in edit.field.inputs:
            if source not in by_id or by_id[source].field_path in affected:
                raise invalid("stale_field_dependency", 409)
        prepared[edit.path] = (typed, canonical, edit.field, edit.field.inputs)
    for path in affected - changed:
        if path not in mapped:
            raise invalid()
        old = latest[path]
        # A versão antiga conserva valor, hipótese/regra e entradas exatas.
        sources = inputs.get(old.id, [])
        prepared[path] = (mapped[path][2].fallback, None, Value(reason_code="dependency_changed",
            origin="derived", rule_version="dependency-invalidation-v1", inputs=tuple(sources)), sources)
    # Validação conjunta antes de qualquer mutação: unidades, períodos e identidade.
    prospective = {}
    for path, (target, name, spec) in mapped.items():
        old = latest[path]
        prospective[path] = prepared[path][2] if path in prepared else Value(
            value=(getattr(target, name) if spec.kind == "boolean" else
                int(old.value) if spec.kind == "integer" and old.value is not None else old.value),
            state=old.state, unit=old.unit, origin=old.origin, coverage=old.coverage,
            reason_code=old.reason_code, hypothesis_code=old.hypothesis_code,
            rule_version=old.rule_version, inputs=tuple(inputs.get(old.id, [])))
    try:
        for prefix, cls, specs in (("items", Item, ITEM), ("measurements", Measurement, MEASUREMENT)):
            ids = {path.split(".")[1] for path in mapped if path.startswith(prefix + ".")}
            for record_id in ids:
                fields = {name: prospective[f"{prefix}.{record_id}.{name}"] for name in specs}
                if prefix == "items":
                    cls(key="review", fields=fields)
                else:
                    cls(key="review", post=mapped[f"{prefix}.{record_id}.contracted_demand"][0].post, fields=fields)
        start, end = (prospective[f"header.{name}"].value for name in ("cycle_start", "cycle_end"))
        if start and end and start > end:
            raise ValueError()
        unit = prospective["header.consumer_unit_id"].value
        if unit is not None and unit != sim.unit_identifier:
            raise ValueError()
    except (ValidationError, ValueError, TypeError):
        raise invalid() from None
    # Aplicar o lote inteiro antes do flush: checks SQL de ciclo/unidade podem
    # recusar um estado intermediário que não corresponde ao comando final.
    for path, (typed, _, _, _) in prepared.items():
        target, name, _ = mapped[path]
        setattr(target, name, typed)
    db.flush()
    for path, (typed, canonical, field, sources) in prepared.items():
        target, name, _ = mapped[path]
        old = latest[path]
        row = FieldProvenance(id=new_id(), invoice_id=invoice.id, field_path=path,
            item_id=old.item_id, measurement_id=old.measurement_id, version=old.version + 1,
            value=canonical, state=field.state, unit=field.unit, origin=field.origin,
            coverage=field.coverage, actor_id=actor.id,
            reason_code=(field.reason_code or payload.reason_code) if path in changed else "dependency_changed",
            hypothesis_code=field.hypothesis_code, rule_version=field.rule_version)
        db.add(row)
        db.flush()
        db.add_all(FieldDependency(invoice_id=invoice.id, field_id=row.id, input_id=source) for source in sources)
    sim.dataset_revision += 1
    sim.updated_by = actor.id
    invoice.dataset_revision = sim.dataset_revision
    invoice.revision += 1
    invoice.status = "needs_review"
    from ecowatt.services.invoice_validation import record_validations
    record_validations(db, invoice)
    receipt = {"invoice_id": invoice.id, "invoice_revision": invoice.revision,
        "dataset_revision": sim.dataset_revision, "invalidated_paths": sorted(affected - changed)}
    db.add(AuditEvent(actor_id=actor.id, action="invoice_reviewed", resource_id=invoice.id,
        changes={"key_hash": key_hash, "request_hash": fingerprint, "receipt": receipt,
            "reason_code": payload.reason_code, "changed_paths": sorted(changed)}))
    db.flush()
    return receipt
