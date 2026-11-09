"""Coordenador explícito de fixtures: fila RAM, fencing e subprocesso spawn.

Não é iniciado pela aplicação nem recebe bytes arbitrários/PDFs. O processo
sintético não demonstra isolamento de rede/CPU/RAM ou proteção de swap/dumps.
"""
from collections import OrderedDict
from dataclasses import dataclass
import multiprocessing
import secrets
from threading import Event, Lock, RLock
import time

from sqlalchemy import select

from ecowatt.db.admissions import InvoiceAdmission
from ecowatt.db.models import SimulationTask, now
from ecowatt.db.session import transaction
from ecowatt.errors import DomainError
from ecowatt.security.tokens import digest
from ecowatt.services import admission, leadership, tasks
from ecowatt.services.synthetic_worker import Sample, decode_receipt, work

MAX_RETAINED_BYTES = 40_000_000


@dataclass
class Entry:
    simulation_id: str
    content: bytearray
    inspection: admission.Inspection
    deadline: float
    running: bool = False

    def discard(self):
        self.content[:] = b"\0" * len(self.content)
        self.content.clear()


@dataclass(frozen=True)
class Outcome:
    task_id: str
    state: str
    reason: str | None = None
    invoice_id: str | None = None


class Coordinator:
    def __init__(self, engine, *, ttl=60, file_timeout=180, batch_timeout=600,
            poll_interval=0.1, worker_delay=0, worker_fail=False):
        if (not 0 < file_timeout <= 180 or not 0 < batch_timeout <= 600
                or not 0 < poll_interval <= 0.5 or poll_interval >= ttl / 2
                or not 0 <= worker_delay <= 10):
            raise ValueError("Limites de execução inválidos")
        self.engine = engine
        self.ttl, self.file_timeout, self.batch_timeout = ttl, file_timeout, batch_timeout
        self.poll_interval, self.worker_delay, self.worker_fail = poll_interval, worker_delay, worker_fail
        self._lock, self._runner, self._stop = RLock(), Lock(), Event()
        self._queue, self._batch_deadlines = OrderedDict(), {}
        self._closed = False
        self.identity = leadership.acquire(engine, ttl)

    @property
    def retained_bytes(self):
        with self._lock:
            return sum(len(entry.content) for entry in self._queue.values())

    @property
    def pending_count(self):
        with self._lock:
            return len(self._queue)

    def _check(self):
        if self._closed or self._stop.is_set():
            leadership.unavailable()

    def _drop(self, task_id):
        entry = self._queue.pop(task_id, None)
        if entry:
            entry.discard()
            if not any(e.simulation_id == entry.simulation_id for e in self._queue.values()):
                self._batch_deadlines.pop(entry.simulation_id, None)

    def sweep(self):
        """Descarta conteúdo revogado/vencido; não assume tarefas automaticamente."""
        with self._lock:
            self._check()
            try:
                leadership.renew(self.engine, self.identity, self.ttl)
            except DomainError:
                for key in list(self._queue):
                    self._drop(key)
                raise
            with transaction(self.engine, write=True) as db:
                leadership.require_leader(db, self.identity)
                queued = db.scalars(select(SimulationTask.id).join(InvoiceAdmission).where(
                    InvoiceAdmission.coordinator_epoch == self.identity.epoch,
                    SimulationTask.status == "queued"))
                for key in queued:
                    if key not in self._queue:
                        self._expire(db, key, "content_lost")
                for key, entry in list(self._queue.items()):
                    try:
                        task, _ = tasks.require_task(db, key)
                    except DomainError:
                        if not entry.running:
                            self._expire(db, key, "operation_revoked")
                            self._drop(key)
                        continue
                    if time.monotonic() >= entry.deadline and task.status == "queued":
                        self._expire(db, key, "batch_timeout")
                        self._drop(key)

    def read_synthetic(self, actor_id, simulation_id, revision, key, sample, *, action):
        if action != "read_invoice":
            admission.reject("read_action_required", "Use a ação Ler fatura.", 422)
        if type(sample) is not Sample:
            admission.reject("document_processing_disabled", "Somente fixtures sintéticas são permitidas.", 503)
        with self._lock:
            self._check()
            self.sweep()
            content, inspection = sample.materialize()  # sem SQL aberto
            registered = []
            def enqueue(task_id):
                if len(self._queue) >= admission.CAPACITY or self.retained_bytes + len(content) > MAX_RETAINED_BYTES:
                    admission.reject("admission_capacity_unavailable", "Fila temporariamente ocupada.", 503)
                deadline = self._batch_deadlines.setdefault(simulation_id, time.monotonic() + self.batch_timeout)
                self._queue[task_id] = Entry(simulation_id, content, inspection, deadline)
                registered.append(task_id)
            try:
                task_id = admission.admit_synthetic(self.engine, actor_id, simulation_id, revision,
                    key, inspection, action=action, _coordinator=self.identity, _on_reserved=enqueue)
                # Retry terminal não repõe bytes; retry queued sem conteúdo exige reenvio.
                if not registered:
                    with transaction(self.engine, write=True) as db:
                        leadership.require_leader(db, self.identity)
                        row = db.get(InvoiceAdmission, task_id)
                        task = db.get(SimulationTask, task_id)
                        if (row is not None and task is not None and row.coordinator_epoch == self.identity.epoch
                                and task.status == "queued" and task_id not in self._queue):
                            self._expire(db, task_id, "content_lost")
                return task_id
            except Exception:
                for task_id in registered:
                    self._drop(task_id)
                raise
            finally:
                if not registered or not any(e.content is content for e in self._queue.values()):
                    content[:] = b"\0" * len(content)
                    content.clear()

    def _expire(self, db, task_id, reason, lease=None):
        """Somente nossas reservas; nunca altera terminal ou outra geração."""
        row = db.get(InvoiceAdmission, task_id)
        task = db.get(SimulationTask, task_id)
        if (row is None or row.coordinator_epoch != self.identity.epoch or task is None
                or task.status not in tasks.ACTIVE):
            return
        if lease is not None and (task.lease_hash is None
                or not secrets.compare_digest(task.lease_hash, digest(lease))):
            return
        task.status, task.reason, task.ended_at = "expired", reason, now()
        task.lease_hash = task.lease_expires_at = None

    def _abort(self, task_id, reason, lease):
        try:
            with transaction(self.engine, write=True) as db:
                leadership.require_leader(db, self.identity)
                self._expire(db, task_id, reason, lease)
        except DomainError:
            pass  # nova geração recupera apenas conteúdo perdido/leases vencidas

    def run_invoice_once(self):
        """Publica somente o gabarito inventado normalizado; sempre needs_review."""
        return self.run_once(_invoice=True)

    def run_once(self, persist=None, *, _invoice=False):
        """Executa uma fixture; callback interno curto recebe apenas Receipt.

        Não publicar fatura: Receipt não é extração normalizada. Não há loop
        de worker no startup, e esta função nunca roda em uma rota HTTP.
        """
        if not self._runner.acquire(blocking=False):
            admission.reject("admission_executor_busy", "Executor de leitura ocupado.")
        try:
            with self._lock:
                self._check()
                self.sweep()
                if not self._queue:
                    return None
                task_id, entry = next(iter(self._queue.items()))
                lease = tasks.claim(self.engine, task_id, "synthetic-coordinator", self.ttl)
                entry.running = True
            reader = writer = process = None
            reason = None
            deadline = min(time.monotonic() + self.file_timeout, entry.deadline)
            try:
                context = multiprocessing.get_context("spawn")
                reader, writer = context.Pipe(duplex=False)
                process = context.Process(target=work,
                    args=(writer, entry.content, entry.inspection.page_count, self.worker_delay, self.worker_fail, _invoice),
                    daemon=True)
                process.start()
                writer.close()
                while True:
                    if self._stop.is_set():
                        reason = "coordinator_shutdown"
                        break
                    if time.monotonic() >= deadline:
                        reason = "batch_timeout" if entry.deadline <= deadline else "file_timeout"
                        break
                    leadership.renew(self.engine, self.identity, self.ttl)
                    tasks.heartbeat(self.engine, task_id, lease, self.ttl)
                    if reader.poll(self.poll_interval):
                        try:
                            packet = reader.recv_bytes(maxlength=262144 if _invoice else 1024)
                            if _invoice:
                                from ecowatt.invoice_result import ExtractionResult
                                result = ExtractionResult.model_validate_json(packet)
                            else:
                                result = decode_receipt(packet)
                        except (ValueError, UnicodeError):
                            reason = "invalid_worker_result"
                            break
                        if result is None:
                            reason = "synthetic_worker_failed"
                            break
                        expected = entry.inspection
                        if (result.version != ("normalized-invoice-v1" if _invoice else "synthetic-receipt-v1") or result.source_hash != expected.source_hash
                                or result.byte_count != expected.byte_count or result.page_count != expected.page_count):
                            reason = "invalid_worker_result"
                            break
                        # O callback roda em nova transação, após revalidação TASKS/epoch.
                        def commit_receipt(db, simulation):
                            leadership.require_leader(db, self.identity)
                            if self._stop.is_set() or time.monotonic() >= deadline:
                                admission.reject("task_unavailable", "Operação encerrada ou vencida.")
                            if persist:
                                return persist(db, simulation, result)
                            if _invoice:
                                from ecowatt.services.invoice_storage import _persist
                                return _persist(db, simulation, task_id, lease, result)
                        invoice_id = tasks.finish(self.engine, task_id, lease, commit_receipt)
                        return Outcome(task_id, "finished", invoice_id=invoice_id if _invoice else None)
                    if not process.is_alive():
                        reason = "synthetic_worker_failed"
                        break
            except DomainError:
                reason = "operation_revoked"
            except (EOFError, OSError):
                reason = "synthetic_worker_failed"
            except Exception:
                reason = "persistence_failed"
                raise
            finally:
                # Encerrar/recolher o filho antes de liberar capacidade ou bytes.
                try:
                    if process is not None and process.pid is not None:
                        if process.is_alive():
                            process.terminate()
                        process.join(timeout=2)
                        if process.is_alive():
                            process.kill()
                            process.join(timeout=2)
                        if process.is_alive():
                            self._stop.set()
                            raise RuntimeError("Não foi possível encerrar o executor sintético")
                        process.close()
                    if reason:
                        self._abort(task_id, reason, lease)
                finally:
                    if reader is not None:
                        reader.close()
                    if writer is not None:
                        writer.close()
                    with self._lock:
                        self._drop(task_id)
            return Outcome(task_id, "interrupted", reason)
        finally:
            self._runner.release()

    def close(self):
        """Espera o run_once encerrar o filho e descarta toda fila desta geração."""
        self._stop.set()
        with self._runner, self._lock:
            if self._closed:
                return
            try:
                with transaction(self.engine, write=True) as db:
                    leadership.require_leader(db, self.identity)
                    for key in self._queue:
                        self._expire(db, key, "coordinator_shutdown")
                    leadership.release(db, self.identity)
            except DomainError:
                pass
            finally:
                for key in list(self._queue):
                    self._drop(key)
                self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
