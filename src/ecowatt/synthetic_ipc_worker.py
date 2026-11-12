"""Entrada exclusiva de fixtures em pipes herdados. Nenhum parser documental."""
import hashlib
import json
import sys
import time

from ecowatt.document_ipc import MAX_HEADER, MAX_INPUT, MAX_RESULT, read_frame, write_frame

PREFIX = b"ECOWATT-SYNTHETIC-v1\n"


def main():
    content = bytearray()
    try:
        header = json.loads(read_frame(sys.stdin.buffer, MAX_HEADER))
        if (type(header) is not dict or set(header) != {"pages", "delay", "fail", "normalized"}
                or type(header["pages"]) is not int or not 1 <= header["pages"] <= 10
                or type(header["delay"]) not in (int, float) or not 0 <= header["delay"] <= 10
                or type(header["fail"]) is not bool or type(header["normalized"]) is not bool):
            raise ValueError("invalid_synthetic_request")
        content = read_frame(sys.stdin.buffer, MAX_INPUT)
        if sys.stdin.buffer.read(1) or not content.startswith(PREFIX) or header["fail"]:
            raise ValueError("invalid_synthetic_content")
        time.sleep(header["delay"])
        source_hash = hashlib.sha256(content).hexdigest()
        if header["normalized"]:
            from ecowatt.synthetic_invoice import synthetic_result
            data = json.loads(content[len(PREFIX):].split(b"\n", 1)[0])
            result = synthetic_result(source_hash, len(content), header["pages"],
                                      data["unit_identifier"], data["serial"])
            packet = result.model_dump_json().encode("utf-8")
        else:
            packet = json.dumps({"status": "ok", "source_hash": source_hash,
                "byte_count": len(content), "page_count": header["pages"],
                "version": "synthetic-receipt-v1"}).encode("ascii")
        write_frame(sys.stdout.buffer, packet, MAX_RESULT)
        return 0
    except Exception:
        try:
            write_frame(sys.stdout.buffer,
                b'{"status":"error","code":"synthetic_worker_failed"}', MAX_RESULT)
        except (OSError, ValueError):
            pass
        return 1
    finally:
        content[:] = b"\0" * len(content)
        content.clear()


if __name__ == "__main__":
    raise SystemExit(main())
