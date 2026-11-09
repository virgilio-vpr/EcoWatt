"""Exercício de IPC com bytes inventados. Não é sandbox nem parser de PDF."""
from dataclasses import asdict, dataclass
import hashlib
import json
import re
import time

from ecowatt.services.admission import Inspection

PREFIX = b"ECOWATT-SYNTHETIC-v1\n"


@dataclass(frozen=True)
class Sample:
    unit_identifier: str
    serial: int = 0
    page_count: int = 1
    padding_bytes: int = 0

    def materialize(self):
        if (not isinstance(self.unit_identifier, str) or not 1 <= len(self.unit_identifier) <= 100
                or type(self.serial) is not int or not 0 <= self.serial <= 1_000_000
                or type(self.page_count) is not int or not 1 <= self.page_count <= 10
                or type(self.padding_bytes) is not int or not 0 <= self.padding_bytes <= 9_999_000):
            raise ValueError("Fixture sintética inválida")
        header = json.dumps({"unit_identifier": self.unit_identifier, "serial": self.serial,
            "page_count": self.page_count}, sort_keys=True).encode("utf-8")
        content = bytearray(PREFIX + header + b"\n")
        content.extend(b"0" * self.padding_bytes)
        inspection = Inspection(hashlib.sha256(content).hexdigest(), len(content), self.page_count,
            "SYNTHETIC", "synthetic-v1", "synthetic-v1", self.unit_identifier)
        return content, inspection


@dataclass(frozen=True)
class Receipt:
    """Retorno técnico fechado; não representa dados faturáveis ou prontidão."""
    source_hash: str
    byte_count: int
    page_count: int
    version: str = "synthetic-receipt-v1"


def decode_receipt(packet):
    """JSON limitado; nunca desserializar pickle vindo do subprocesso."""
    value = json.loads(packet)
    if value == {"status": "error", "code": "synthetic_worker_failed"}:
        return None
    fields = {"status", "source_hash", "byte_count", "page_count", "version"}
    if (not isinstance(value, dict) or set(value) != fields or value["status"] != "ok"
            or value["version"] != "synthetic-receipt-v1"
            or not isinstance(value["source_hash"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", value["source_hash"])
            or type(value["byte_count"]) is not int or not 1 <= value["byte_count"] <= 10_000_000
            or type(value["page_count"]) is not int or not 1 <= value["page_count"] <= 10):
        raise ValueError("Resultado técnico inválido")
    return Receipt(**{key: value[key] for key in fields - {"status"}})


def work(connection, content, pages, delay=0, fail=False, normalized=False):
    """Sem banco ou logs de conteúdo. Delay/fail são injeções internas de teste."""
    try:
        if delay:
            time.sleep(delay)
        if fail or not content.startswith(PREFIX):
            connection.send_bytes(b'{"status":"error","code":"synthetic_worker_failed"}')
            return
        source_hash = hashlib.sha256(content).hexdigest()
        if normalized:
            from ecowatt.synthetic_invoice import synthetic_result
            header = json.loads(content[len(PREFIX):].split(b"\n", 1)[0])
            result = synthetic_result(source_hash, len(content), pages, header["unit_identifier"], header["serial"])
            connection.send_bytes(result.model_dump_json().encode("utf-8"))
        else:
            result = Receipt(source_hash, len(content), pages)
            connection.send_bytes(json.dumps({"status": "ok", **asdict(result)}).encode("ascii"))
    except Exception:
        # Não envia exceção/traceback, documento ou diagnóstico da biblioteca.
        try:
            connection.send_bytes(b'{"status":"error","code":"synthetic_worker_failed"}')
        except (OSError, EOFError):
            pass
    finally:
        content[:] = b"\0" * len(content)
        connection.close()
