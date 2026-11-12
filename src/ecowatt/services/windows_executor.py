"""Adaptador interno Windows do coordenador, somente fixtures sintéticas.

Dois pipes anônimos, stderr NUL e lista explícita de três handles. Threads
de I/O não bloqueiam heartbeat/cancelamento; nenhum byte passa por argv/env.
O runtime/script e SID são provisionados pelo chamador confiável, sem fallback.
"""
from dataclasses import dataclass, replace
import json
import os
from pathlib import Path
from threading import Event, Thread

from ecowatt.document_ipc import MAX_HEADER, MAX_INPUT, read_frame, write_frame
from ecowatt.windows_isolation import IsolatedProcess, IsolationPolicy, IsolationError


@dataclass(frozen=True)
class WindowsExecutor:
    executable: str
    worker_script: str
    appcontainer_sid: object
    policy: IsolationPolicy = IsolationPolicy()

    def start(self, content, pages, delay, fail, normalized, timeout):
        return Exchange(self, content, pages, delay, fail, normalized, timeout)


class Exchange:
    def __init__(self, config, content, pages, delay, fail, normalized, timeout):
        import msvcrt
        self.process = None
        self.packet = None
        self.error = False
        self.done = Event()
        self.threads = []
        self.streams = []
        descriptors = []
        try:
            input_read, input_write = os.pipe()
            descriptors.extend((input_read, input_write))
            output_read, output_write = os.pipe()
            descriptors.extend((output_read, output_write))
            null = os.open(os.devnull, os.O_WRONLY)
            descriptors.append(null)
            for fd in (input_read, output_write, null):
                os.set_inheritable(fd, True)
            handles = tuple(msvcrt.get_osfhandle(fd) for fd in (input_read, output_write, null))
            self.process = IsolatedProcess(config.executable,
                ["-I", "-B", str(Path(config.worker_script).resolve(strict=True))],
                appcontainer_sid=config.appcontainer_sid, stdio=handles,
                policy=replace(config.policy, wall_seconds=min(config.policy.wall_seconds, timeout)))
            for fd in (input_read, output_write, null):
                os.close(fd)
                descriptors.remove(fd)
            writer = os.fdopen(input_write, "wb", buffering=0)
            descriptors.remove(input_write)
            self.streams.append(writer)
            reader = os.fdopen(output_read, "rb", buffering=0)
            descriptors.remove(output_read)
            self.streams.append(reader)
            def send():
                try:
                    write_frame(writer, json.dumps({"pages": pages, "delay": delay,
                        "fail": fail, "normalized": normalized}).encode("ascii"), MAX_HEADER)
                    write_frame(writer, content, MAX_INPUT)
                except (OSError, ValueError):
                    self.error = True
                    self.done.set()
                finally:
                    writer.close()
            def receive():
                try:
                    packet = read_frame(reader, 262144 if normalized else 1024)
                    # Só um frame; aguardar EOF antes de aceitar/publicar.
                    if reader.read(1):
                        raise ValueError("ipc_trailing_data")
                    self.packet = packet
                except (OSError, EOFError, ValueError):
                    self.error = True
                finally:
                    reader.close()
                    self.done.set()
            self.threads = [Thread(target=send, daemon=True), Thread(target=receive, daemon=True)]
            for thread in self.threads:
                thread.start()
        except BaseException:
            self.close()
            raise
        finally:
            for fd in descriptors:
                os.close(fd)

    def poll(self, seconds):
        return self.done.wait(seconds)

    def recv_bytes(self, maxlength):
        if self.error or self.packet is None:
            raise OSError("synthetic_ipc_failed")
        if len(self.packet) > maxlength:
            raise ValueError("ipc_size")
        return self.packet

    @property
    def pid(self):
        return self.process.pid if self.process else None

    def is_alive(self):
        return bool(self.process and self.process.api.kernel.WaitForSingleObject(self.process.process, 0) == 258)

    def close(self):
        if self.process:
            self.process.close()  # Fecha árvore antes de recolher threads/buffers.
            self.process = None
        for thread in self.threads:
            if thread.ident is not None:
                thread.join(5)
                if thread.is_alive():
                    raise IsolationError("ipc_thread_not_stopped")
        for stream in self.streams:
            stream.close()
        if self.packet is not None:
            self.packet[:] = b"\0" * len(self.packet)
            self.packet = None
