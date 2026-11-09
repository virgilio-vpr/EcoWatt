"""Publicação inicial normalizada por TASKS, exclusivamente sintética."""
import json
import secrets

from pydantic import ValidationError
from sqlalchemy import delete, select

from ecowatt.db.admissions import InvoiceAdmission, InvoicePublication
from ecowatt.db.invoices import (FieldDependency, FieldProvenance, Invoice, InvoiceItem,
    InvoiceMarketEvidence, InvoiceMeasurement, InvoiceValidation)
from ecowatt.db.models import AuditEvent, Distributor, SimulationTask, User, new_id
from ecowatt.db.session import transaction
from ecowatt.errors import DomainError
from ecowatt.invoice_result import ExtractionResult, HEADER, ITEM, MEASUREMENT, Spec, Value, normalize
from ecowatt.security.tokens import digest
from ecowatt.services import tasks
from ecowatt.services.simulations import require_simulation


def prepare_result(value):
    """Valida/copia fora do SQL; erros nunca incluem valores do payload."""
    try:
        return ExtractionResult.model_validate(value.model_dump() if isinstance(value, ExtractionResult) else value)
    except (ValidationError, ValueError, TypeError):
        raise DomainError("invalid_extraction_result", "Resultado normalizado inválido.", 422) from None


def result_hash(result):
    return digest(json.dumps(result.model_dump(mode="json"), sort_keys=True, separators=(",", ":")))


def _persist(db, simulation, task_id, lease, result):
    """Somente callback interno de tasks.finish; nunca recebe bytes/texto bruto."""
    task, current = tasks.require_lease(db, task_id, lease)
    row = db.get(InvoiceAdmission, task_id, populate_existing=True)
    if row is None or row.removed or row.simulation_id != simulation.id or current.id != simulation.id:
        raise DomainError("task_unavailable", "Admissão indisponível.", 409)
    distributor = db.get(Distributor, simulation.distributor_id)
    observed_unit = result.header.get("consumer_unit_id", Value()).value
    if (distributor.code != result.distributor_code or observed_unit is not None and observed_unit != simulation.unit_identifier
            or row.source_hash != result.source_hash or row.byte_count != result.byte_count
            or row.page_count != result.page_count or row.layout_version != result.layout_version
            or row.parser_version != result.parser_version):
        raise DomainError("extraction_identity_conflict", "Resultado diverge da admissão/unidade.", 409)
    if db.scalar(select(Invoice.id).where(Invoice.simulation_id == simulation.id, Invoice.source_hash == result.source_hash)):
        raise DomainError("duplicate_invoice", "Fatura já persistida nesta simulação.", 409)
    simulation.dataset_revision += 1
    simulation.updated_by = task.actor_id
    invoice = Invoice(id=new_id(), simulation_id=simulation.id, created_by=task.actor_id,
        dataset_revision=simulation.dataset_revision, source_hash=result.source_hash, source_kind="synthetic",
        contract_version="invoice-v0.3", parser_version=result.parser_version, layout_version=result.layout_version,
        distributor_id=simulation.distributor_id, status="needs_review", coverage=result.coverage,
        market_candidate=result.market_candidate, market_assessment=result.market_assessment)
    db.add(invoice)
    fields = {}
    paths = {}
    dependencies = []

    def assign(target, prefix, values, specs, *, item_id=None, measurement_id=None):
        for key, spec in specs.items():
            field = values.get(key, Value())
            current_value, canonical = normalize(field, spec)
            setattr(target, key, current_value)
            path = f"{prefix}.{key}"
            provenance = FieldProvenance(id=new_id(), invoice_id=invoice.id, field_path=path, version=1,
                item_id=item_id, measurement_id=measurement_id, value=canonical, unit=field.unit,
                state=field.state, origin=field.origin, coverage=field.coverage,
                actor_id=task.actor_id, reason_code=field.reason_code, hypothesis_code=field.hypothesis_code,
                rule_version=field.rule_version)
            fields[path] = provenance
            db.add(provenance)
            dependencies.append((provenance, field.inputs))

    # Pais são confirmados por flush antes das FKs dos filhos; tudo ainda na mesma transação.
    header_values = {key: normalize(result.header.get(key, Value()), spec)[0] for key, spec in HEADER.items()}
    for key, value in header_values.items():
        setattr(invoice, key, value)
    db.flush()
    assign(invoice, "header", result.header, HEADER)
    paths.update({f"header.{key}": f"header.{key}" for key in HEADER})
    measurements = {}
    for record in result.measurements:
        target = InvoiceMeasurement(id=new_id(), invoice_id=invoice.id, post=record.post,
            **{key: normalize(record.fields.get(key, Value()), spec)[0] for key, spec in MEASUREMENT.items()})
        db.add(target)
        db.flush()
        measurements[record.key] = target.id
        prefix = f"measurements.{target.id}"
        assign(target, prefix, record.fields, MEASUREMENT, measurement_id=target.id)
        assign(target, prefix, {"post": Value(value=record.post, state="confirmed")}, {"post": Spec()}, measurement_id=target.id)
        paths.update({f"measurements.{record.key}.{key}": f"{prefix}.{key}" for key in MEASUREMENT})
    for position, record in enumerate(result.items, 1):
        target = InvoiceItem(id=new_id(), invoice_id=invoice.id, position=position,
            measurement_id=measurements.get(record.measurement_key),
            **{key: normalize(record.fields.get(key, Value()), spec)[0] for key, spec in ITEM.items()})
        db.add(target)
        db.flush()
        prefix = f"items.{target.id}"
        assign(target, prefix, record.fields, ITEM, item_id=target.id)
        paths.update({f"items.{record.key}.{key}": f"{prefix}.{key}" for key in ITEM})
    db.flush()
    for provenance, inputs in dependencies:
        for source in inputs:
            db.add(FieldDependency(invoice_id=invoice.id, field_id=provenance.id, input_id=fields[paths[source]].id))
    db.add_all(InvoiceMarketEvidence(invoice_id=invoice.id, code=code) for code in result.evidence)
    # Esta etapa não certifica finanças/prontidão; revisão operacional ainda é obrigatória.
    db.add(InvoiceValidation(invoice_id=invoice.id, field_path="header", code="review_required",
        result="blocking", policy_version="normalized-invoice-v1"))
    db.add(InvoicePublication(task_id=task.id, invoice_id=invoice.id, result_hash=result_hash(result), completion_hash=digest(lease)))
    db.add(AuditEvent(actor_id=task.actor_id, action="invoice_persisted", resource_id=invoice.id))
    db.flush()
    return invoice.id


def finish_normalized(engine, task_id, lease, value):
    result = prepare_result(value)
    try:
        return tasks.finish(engine, task_id, lease,
            lambda db, simulation: _persist(db, simulation, task_id, lease, result))
    except DomainError:
        # Replay concorrente/terminal exige a lease original e o mesmo resultado.
        with transaction(engine, write=True) as db:
            task = db.get(SimulationTask, task_id, populate_existing=True)
            publication = db.get(InvoicePublication, task_id)
            row = db.get(InvoiceAdmission, task_id)
            if task is None or publication is None or row is None or row.removed or task.status != "finished":
                raise
            actor = db.get(User, task.actor_id, populate_existing=True)
            if actor is None or actor.status != "active":
                raise DomainError("task_unavailable", "Operação indisponível.", 409)
            require_simulation(db, actor, task.simulation_id, task.revision)
            if not secrets.compare_digest(publication.completion_hash, digest(lease)):
                raise DomainError("task_unavailable", "Executor inválido.", 409)
            if publication.result_hash != result_hash(result):
                raise DomainError("idempotency_conflict", "Resultado já confirmado com outro conteúdo.", 409)
            return publication.invoice_id


def delete_graph(db, invoice_id):
    """Itens antes das medições; CASCADE remove proveniência, dependências e vínculo."""
    db.execute(delete(InvoiceItem).where(InvoiceItem.invoice_id == invoice_id))
    db.execute(delete(Invoice).where(Invoice.id == invoice_id))
