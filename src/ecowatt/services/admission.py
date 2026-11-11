"""Contrato interno sintético. Nenhuma rota recebe PDFs nesta entrega.

O futuro coordenador inspeciona/hash/paginação fora da transação, em isolamento
verificado. Metadados enviados pelo cliente não são prova de tamanho/páginas.
"""
from dataclasses import asdict, dataclass
import json
import re
from typing import Protocol

from sqlalchemy import func, select

from ecowatt.db.admissions import InvoiceAdmission
from ecowatt.db.models import Distributor, SimulationTask, User
from ecowatt.db.session import transaction
from ecowatt.errors import DomainError
from ecowatt.security.tokens import digest
from ecowatt.services import tasks
from ecowatt.services.simulations import require_simulation

# MB decimal; política única do piloto. Fila total inclui queued e running.
MAX_FILES, MAX_BYTES, MAX_PAGES, CAPACITY = 12, 60_000_000, 60, 4


@dataclass(frozen=True)
class Inspection:
    source_hash: str
    byte_count: int
    page_count: int
    distributor_code: str
    layout_version: str
    parser_version: str
    unit_identifier: str
    source_kind: str = "synthetic"


class Adapter(Protocol):
    """Futuro processo isolado: inspeção sem SQL e sem conteúdo no retorno.

    Recebe bytes efêmeros somente após garantias §5. Não implementado aqui.
    Extração normalizada/proveniência será outro contrato versionado.
    """
    def inspect(self, content: bytes) -> Inspection: ...


def support(distributor_code, layout_version):
    # Registro fechado: nenhum layout documental homologado, inclusive ENEL.
    enabled = (distributor_code, layout_version) == ("SYNTHETIC", "synthetic-v1")
    return {"supported": enabled, "reason": None if enabled else "layout_not_supported",
            "contact_required": not enabled, "document_upload_enabled": False}


def admission_context(db, actor, simulation_id, layout_version="unknown"):
    """Consulta compartilhada por JSON e HTML, sem admissão ou leitura."""
    simulation = require_simulation(db, actor, simulation_id)
    distributor = db.get(Distributor, simulation.distributor_id) if simulation.distributor_id else None
    capability = support(distributor.code if distributor else None, layout_version)
    if simulation.unit_saved_at is None:
        capability.update(supported=False, reason="unit_not_saved")
    return {"unit_saved": simulation.unit_saved_at is not None,
            "distributor_id": simulation.distributor_id,
            "distributor_code": distributor.code if distributor else None,
            "layout_version": layout_version, **capability}


def reject(code, message, status=409):
    raise DomainError(code, message, status)


def admit_synthetic(engine, actor_id, simulation_id, revision, key, inspection, *, action,
        _coordinator=None, _on_reserved=None):
    """Reserva somente pela ação Ler fatura. Não aceita nem persiste bytes.

    Idempotência é por ator/chave; retry terminal devolve o mesmo ID, sem
    criar trabalho novo. Cancelamento/expiração exigem remover e reenviar com
    outra chave. Reservas terminais retêm orçamento até remoção explícita.
    """
    if action != "read_invoice":
        reject("read_action_required", "Use a ação Ler fatura.", 422)
    if inspection.source_kind != "synthetic":
        reject("document_processing_disabled", "Recebimento de documentos desabilitado.", 503)
    if (not isinstance(key, str) or not 8 <= len(key) <= 128
            or not isinstance(inspection.source_hash, str)
            or not re.fullmatch(r"[0-9a-f]{64}", inspection.source_hash)
            or type(inspection.byte_count) is not int or not 1 <= inspection.byte_count <= 10_000_000
            or type(inspection.page_count) is not int or not 1 <= inspection.page_count <= 10):
        reject("invalid_admission", "Metadados de admissão inválidos.", 422)
    fingerprint = digest(json.dumps({"simulation_id": simulation_id, "revision": revision,
        **asdict(inspection)}, sort_keys=True))
    with transaction(engine, write=True) as db:
        if _coordinator is not None:
            from ecowatt.services.leadership import require_leader
            require_leader(db, _coordinator)
        actor = db.get(User, actor_id, populate_existing=True)
        if not actor or actor.status != "active":
            reject("task_unavailable", "Operação indisponível.")
        sim = require_simulation(db, actor, simulation_id, revision)
        if sim.unit_saved_at is None:
            reject("unit_not_saved", "Salve os dados da unidade antes de ler faturas.")
        previous = db.scalar(select(InvoiceAdmission).where(
            InvoiceAdmission.actor_id == actor.id, InvoiceAdmission.key_hash == digest(key)))
        if previous:
            if previous.request_hash != fingerprint:
                reject("idempotency_conflict", "Chave já usada em outro pedido.")
            if previous.removed:
                reject("admission_removed", "Admissão removida. Use um novo pedido.")
            return previous.task_id
        distributor = db.get(Distributor, sim.distributor_id)
        if (distributor.code != inspection.distributor_code
                or sim.unit_identifier != inspection.unit_identifier):
            reject("invoice_identity_conflict", "Confira distribuidora e unidade do documento.")
        if not support(distributor.code, inspection.layout_version)["supported"]:
            reject("layout_not_supported", "Layout não suportado. Solicite contato para atendimento.")
        if inspection.parser_version != "synthetic-v1":
            reject("layout_not_supported", "Versão do adaptador não habilitada. Solicite contato.")
        if db.scalar(select(InvoiceAdmission.task_id).where(
                InvoiceAdmission.simulation_id == sim.id,
                InvoiceAdmission.source_hash == inspection.source_hash,
                InvoiceAdmission.removed.is_(False))):
            reject("duplicate_invoice", "Arquivo já admitido nesta simulação.")
        count, size, pages = db.execute(select(func.count(),
            func.coalesce(func.sum(InvoiceAdmission.byte_count), 0),
            func.coalesce(func.sum(InvoiceAdmission.page_count), 0)).where(
                InvoiceAdmission.simulation_id == sim.id, InvoiceAdmission.removed.is_(False))).one()
        if count + 1 > MAX_FILES or size + inspection.byte_count > MAX_BYTES or pages + inspection.page_count > MAX_PAGES:
            reject("invoice_limits_exceeded", "Limites acumulados da simulação atingidos.")
        active = db.scalar(select(func.count()).select_from(InvoiceAdmission).join(SimulationTask).where(
            SimulationTask.status.in_(tasks.ACTIVE), InvoiceAdmission.removed.is_(False)))
        if active >= CAPACITY:
            reject("admission_capacity_unavailable", "Capacidade temporariamente indisponível. Tente novamente.", 503)
        task_id = tasks.reserve(db, actor, sim.id, revision)
        db.add(InvoiceAdmission(task_id=task_id, simulation_id=sim.id, actor_id=actor.id,
            key_hash=digest(key), request_hash=fingerprint, source_hash=inspection.source_hash,
            byte_count=inspection.byte_count, page_count=inspection.page_count,
            layout_version=inspection.layout_version, parser_version=inspection.parser_version,
            coordinator_epoch=_coordinator.epoch if _coordinator else None))
        if _on_reserved is not None:
            # Inserção efêmera curta; falha desfaz também a reserva SQL.
            _on_reserved(task_id)
        return task_id


def remove_synthetic(engine, actor_id, simulation_id, revision, task_id, *, expected_dataset_revision=None):
    """Libera orçamento e cancela autorização de escrita na mesma transação."""
    with transaction(engine, write=True) as db:
        actor = db.get(User, actor_id, populate_existing=True)
        if not actor or actor.status != "active":
            reject("task_unavailable", "Operação indisponível.")
        simulation = require_simulation(db, actor, simulation_id, revision)
        row = db.get(InvoiceAdmission, task_id)
        if row is None or row.simulation_id != simulation_id:
            reject("not_found", "Recurso não encontrado.", 404)
        if row.removed:
            return
        from ecowatt.db.admissions import InvoicePublication
        publication = db.get(InvoicePublication, task_id)
        if publication is not None:
            if expected_dataset_revision != simulation.dataset_revision:
                reject("dataset_revision_conflict", "Atualize a revisão do conjunto antes de remover.")
            from ecowatt.services.invoice_storage import delete_graph
            delete_graph(db, publication.invoice_id)
            simulation.dataset_revision += 1
            simulation.updated_by = actor.id
        task = db.get(SimulationTask, task_id)
        if task.status in tasks.ACTIVE:
            from ecowatt.db.models import now
            task.status, task.reason, task.ended_at = "cancelled", "invoice_removed", now()
            task.lease_hash = task.lease_expires_at = None
        # Mantém chave/hash como tombstone: retry não recria reserva removida.
        row.removed = True
