"""Scratch em páginas travadas de RAM, sem arquivo/diretório temporário.

Não protege cópias do Python, pipes, bibliotecas ou dumps. Não substitui
política de swap/dumps do ambiente nem um filesystem RAM para bibliotecas.
"""
import ctypes as C
from ctypes import wintypes as W
import mmap
from threading import RLock

from ecowatt.windows_isolation import IsolationError

MAX_SCRATCH_BYTES = 4_000_000


class RamScratch:
    def __init__(self, quota=MAX_SCRATCH_BYTES):
        if type(quota) is not int or not 0 < quota <= MAX_SCRATCH_BYTES:
            raise ValueError("invalid_scratch_quota")
        self.quota = quota
        self._buffers = set()
        self._used = 0
        self._closed = False
        self._lock = RLock()

    @property
    def used_bytes(self):
        return self._used

    def allocate(self, size):
        with self._lock:
            if (self._closed or type(size) is not int or size <= 0
                    or size > self.quota):
                raise ValueError("scratch_quota_or_closed")
            charged = ((size + mmap.PAGESIZE - 1) // mmap.PAGESIZE) * mmap.PAGESIZE
            if charged > self.quota - self._used:
                raise ValueError("scratch_quota_or_closed")
            buffer = LockedBuffer(size, self)
            self._buffers.add(buffer)
            self._used += charged
            return buffer

    def close(self):
        with self._lock:
            self._closed = True
            for buffer in tuple(self._buffers):
                buffer.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class LockedBuffer:
    def __init__(self, size, owner):
        self._owner, self.size = owner, size
        self.charged_bytes = ((size + mmap.PAGESIZE - 1) // mmap.PAGESIZE) * mmap.PAGESIZE
        self._address = None
        k = self._kernel = C.WinDLL("kernel32", use_last_error=True)
        k.VirtualAlloc.argtypes = [C.c_void_p, C.c_size_t, W.DWORD, W.DWORD]
        k.VirtualAlloc.restype = C.c_void_p
        k.VirtualLock.argtypes = [C.c_void_p, C.c_size_t]
        k.VirtualLock.restype = W.BOOL
        k.VirtualUnlock.argtypes = [C.c_void_p, C.c_size_t]
        k.VirtualUnlock.restype = W.BOOL
        k.VirtualFree.argtypes = [C.c_void_p, C.c_size_t, W.DWORD]
        k.VirtualFree.restype = W.BOOL
        address = k.VirtualAlloc(None, size, 0x3000, 4)
        if not address:
            raise IsolationError("scratch_allocation_failed")
        if not k.VirtualLock(address, size):
            C.memset(address, 0, size)
            k.VirtualFree(address, 0, 0x8000)
            raise IsolationError("scratch_lock_failed")
        self._address = address

    def write(self, content, offset=0):
        with self._owner._lock:
            if (not self._address or type(offset) is not int or offset < 0
                    or type(content) is not bytes or offset + len(content) > self.size):
                raise ValueError("scratch_write_invalid")
            C.memmove(self._address + offset, content, len(content))

    def read(self, size, offset=0):
        with self._owner._lock:
            if (not self._address or type(size) is not int or type(offset) is not int
                    or size < 0 or offset < 0 or offset + size > self.size):
                raise ValueError("scratch_read_invalid")
            # Cópia retornada ao chamador NÃO está travada; usar só fixtures.
            return C.string_at(self._address + offset, size)

    def close(self):
        with self._owner._lock:
            if self._address:
                C.memset(self._address, 0, self.size)
                # VirtualFree também desfaz o lock. Falha de liberação permanece
                # contabilizada e é erro fechado; nunca liberar quota fictícia.
                if not self._kernel.VirtualFree(self._address, 0, 0x8000):
                    raise IsolationError("scratch_free_failed")
                self._address = None
                if self in self._owner._buffers:
                    self._owner._buffers.remove(self)
                    self._owner._used -= self.charged_bytes
