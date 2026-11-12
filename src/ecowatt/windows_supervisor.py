"""Supervisor confiável sem conteúdo documental, executado fora do host/GIL.

Somente handles explicitamente herdados: Job (terminate), pai (synchronize),
evento de encerramento e evento de prontidão. Sem IPC de documentos ou nomes.
"""
import ctypes as C
from ctypes import wintypes as W
import sys


def supervise(job, parent, stop, ready, milliseconds):
    k = C.WinDLL("kernel32", use_last_error=True)
    k.SetEvent.argtypes = [W.HANDLE]
    k.SetEvent.restype = W.BOOL
    k.WaitForMultipleObjects.argtypes = [W.DWORD, C.POINTER(W.HANDLE), W.BOOL, W.DWORD]
    k.WaitForMultipleObjects.restype = W.DWORD
    k.TerminateJobObject.argtypes = [W.HANDLE, W.UINT]
    k.TerminateJobObject.restype = W.BOOL
    k.CloseHandle.argtypes = [W.HANDLE]
    try:
        if not k.SetEvent(ready):
            return 1
        # Pai primeiro: morte do host prevalece sobre encerramento normal.
        result = k.WaitForMultipleObjects(2, (W.HANDLE * 2)(parent, stop), False, milliseconds)
        if result == 1:
            return 0
        if not k.TerminateJobObject(job, 1460):
            return 1
        return 1460 if result == 258 else 1
    finally:
        for handle in (job, parent, stop, ready):
            k.CloseHandle(handle)


if __name__ == "__main__":
    raise SystemExit(supervise(*(int(value) for value in sys.argv[1:])))
