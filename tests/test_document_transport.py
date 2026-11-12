"""Somente bytes inventados; não lê corpus, documentos ou configurações reais."""
import asyncio
from io import BytesIO
import struct

import pytest

from ecowatt.document_environment import EnvironmentAudit
from ecowatt.document_ipc import read_frame, write_frame
from ecowatt.memory_ingress import IngressError, memory_body


def test_frame_roundtrip_and_short_reads_writes():
    class ShortIO(BytesIO):
        def readinto(self, target):
            return super().readinto(target[:2])
        def write(self, source):
            return super().write(source[:2])
    stream = ShortIO()
    write_frame(stream, b"SYNTHETIC", 9)
    stream.seek(0)
    assert read_frame(stream, 9) == b"SYNTHETIC"


@pytest.mark.parametrize("size", [0, 11, 0xffffffff])
def test_frame_rejects_length_before_reading_or_allocating_payload(size):
    stream = BytesIO(struct.pack("!I", size) + b"SYNTHETIC")
    with pytest.raises(ValueError, match="ipc_size"):
        read_frame(stream, 10)
    assert stream.tell() == 4


@pytest.mark.parametrize("packet", [b"", b"\0\0", struct.pack("!I", 8) + b"abc"])
def test_frame_truncation(packet):
    with pytest.raises(EOFError):
        read_frame(BytesIO(packet), 10)


def exercise(messages, headers=(), limit=16, fail=False):
    retained = []
    async def run():
        iterator = iter(messages)
        async def receive():
            return next(iterator)
        async with memory_body({"type": "http", "headers": headers}, receive, limit=limit) as body:
            retained.append(body)
            if fail:
                raise RuntimeError("synthetic_consumer_failed")
            return bytes(body)
    try:
        return asyncio.run(run())
    finally:
        assert all(body == bytearray() for body in retained)


def test_ingress_stream_without_spool_and_cleanup(monkeypatch):
    import tempfile
    def denied(*args, **kwargs):
        pytest.fail("Ingress tentou spool")
    monkeypatch.setattr(tempfile, "SpooledTemporaryFile", denied)
    monkeypatch.setattr(tempfile, "TemporaryFile", denied)
    messages = [{"type": "http.request", "body": b"SYN", "more_body": True},
                {"type": "http.request", "body": b"THETIC"}]
    assert exercise(messages, [(b"content-length", b"9")]) == b"SYNTHETIC"
    assert exercise(messages) == b"SYNTHETIC"
    with pytest.raises(RuntimeError):
        exercise(messages, fail=True)


@pytest.mark.parametrize("messages,headers,code", [
    ([{"type": "http.request", "body": b"12345678901234567"}], (), "ingress_size"),
    ([{"type": "http.request", "body": b"abc", "more_body": True},
      {"type": "http.disconnect"}], (), "ingress_disconnected"),
    ([{"type": "http.request", "body": b"abc"}], [(b"content-length", b"4")], "ingress_length_mismatch"),
    ([], [(b"content-length", b"17")], "ingress_size"),
    ([], [(b"content-length", b"-1")], "invalid_content_length"),
    ([], [(b"content-length", b"1"), (b"content-length", b"1")], "invalid_ingress_headers"),
    ([], [(b"content-encoding", b"gzip")], "invalid_ingress_headers"),
    ([{"type": "http.request", "body": b""}], (), "ingress_length_mismatch"),
])
def test_ingress_rejects_oversize_disconnect_and_ambiguous_headers(messages, headers, code):
    with pytest.raises(IngressError, match=code):
        exercise(messages, headers)


@pytest.mark.parametrize("crash,swap", [(None, None), (3, None), (0, 1)])
def test_environment_report_never_authorizes_documents(crash, swap):
    report = EnvironmentAudit(crash, swap, False)
    assert "process_dumps_not_excluded" in report.blockers
    assert "ram_temporary_not_verified" in report.blockers
    assert ("system_dumps_not_excluded" in report.blockers) == (crash != 0)
    assert ("protected_swap_not_verified" in report.blockers) == (swap != 1)
