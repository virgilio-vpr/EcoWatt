"""Frames binários limitados; sem pickle, arquivos ou nomes fornecidos pelo filho."""
import struct

MAX_INPUT = 10_000_000
MAX_RESULT = 262_144
MAX_HEADER = 512


def read_exact(stream, size):
    buffer = bytearray(size)
    view = memoryview(buffer)
    offset = 0
    while offset < size:
        count = stream.readinto(view[offset:])
        if not count:
            raise EOFError("ipc_truncated")
        offset += count
    return buffer


def read_frame(stream, limit):
    size = struct.unpack("!I", read_exact(stream, 4))[0]
    if not 0 < size <= limit:
        raise ValueError("ipc_size")
    return read_exact(stream, size)


def write_frame(stream, content, limit):
    if not 0 < len(content) <= limit:
        raise ValueError("ipc_size")
    for part in (struct.pack("!I", len(content)), content):
        view = memoryview(part)
        while view:
            count = stream.write(view)
            if not count:
                raise OSError("ipc_write")
            view = view[count:]
    stream.flush()
