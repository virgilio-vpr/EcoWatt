"""Backend experimental Win32, somente para executáveis/programas sintéticos.

Não conectado ao coordenador ou a rotas. Falhas de configuração são fatais;
nunca repetir execução sem AppContainer/Job. Não garante RAM sem swap/dumps.
"""
import ctypes as C
from ctypes import wintypes as W
from dataclasses import dataclass
import math
import os
from pathlib import Path
import subprocess
import threading


@dataclass(frozen=True)
class IsolationPolicy:
    memory_bytes: int = 1_000_000_000
    cpu_seconds: int = 30
    cpu_rate: int = 2500  # centésimos de porcento: teto de 25% do sistema
    processes: int = 4
    wall_seconds: float = 180

    def __post_init__(self):
        for value, lower, upper in (
            (self.memory_bytes, 32_000_000, 1_000_000_000),
            (self.cpu_seconds, 1, 180), (self.cpu_rate, 1, 10000),
            (self.processes, 1, 4),
        ):
            if type(value) is not int or not lower <= value <= upper:
                raise ValueError("Política de isolamento inválida")
        if (type(self.wall_seconds) not in (int, float)
                or not math.isfinite(self.wall_seconds) or not 0 < self.wall_seconds <= 180):
            raise ValueError("Prazo de isolamento inválido")


class IsolationError(OSError):
    """Erro técnico; nunca inclui comando, documento ou ambiente."""


class BasicLimits(C.Structure):
    _fields_ = [("process_time", C.c_int64), ("job_time", C.c_int64),
                ("flags", W.DWORD), ("min_ws", C.c_size_t), ("max_ws", C.c_size_t),
                ("processes", W.DWORD), ("affinity", C.c_size_t),
                ("priority", W.DWORD), ("scheduling", W.DWORD)]


class IO(C.Structure):
    _fields_ = [(name, C.c_uint64) for name in ("read_ops", "write_ops", "other_ops",
                                             "read_bytes", "write_bytes", "other_bytes")]


class ExtendedLimits(C.Structure):
    _fields_ = [("basic", BasicLimits), ("io", IO), ("process_memory", C.c_size_t),
                ("job_memory", C.c_size_t), ("peak_process", C.c_size_t),
                ("peak_job", C.c_size_t)]


class CpuRate(C.Structure):
    _fields_ = [("flags", W.DWORD), ("rate", W.DWORD)]


class SecurityCapabilities(C.Structure):
    _fields_ = [("sid", C.c_void_p), ("capabilities", C.c_void_p),
                ("count", W.DWORD), ("reserved", W.DWORD)]


class Startup(C.Structure):
    _fields_ = [("cb", W.DWORD), ("reserved", W.LPWSTR), ("desktop", W.LPWSTR),
                ("title", W.LPWSTR), ("x", W.DWORD), ("y", W.DWORD),
                ("xsize", W.DWORD), ("ysize", W.DWORD), ("xchars", W.DWORD),
                ("ychars", W.DWORD), ("fill", W.DWORD), ("flags", W.DWORD),
                ("show", W.WORD), ("reserved_size", W.WORD),
                ("reserved_ptr", C.c_void_p), ("stdin", W.HANDLE),
                ("stdout", W.HANDLE), ("stderr", W.HANDLE)]


class StartupEx(C.Structure):
    _fields_ = [("startup", Startup), ("attributes", C.c_void_p)]


class ProcessInfo(C.Structure):
    _fields_ = [("process", W.HANDLE), ("thread", W.HANDLE),
                ("pid", W.DWORD), ("tid", W.DWORD)]


class Win32:
    def __init__(self):
        if os.name != "nt":
            raise IsolationError("windows_isolation_unavailable")
        self.kernel = C.WinDLL("kernel32", use_last_error=True)
        self.advapi = C.WinDLL("advapi32", use_last_error=True)
        signatures = {
            "CreateJobObjectW": ([C.c_void_p, W.LPCWSTR], W.HANDLE),
            "CloseHandle": ([W.HANDLE], W.BOOL),
            "SetInformationJobObject": ([W.HANDLE, C.c_int, C.c_void_p, W.DWORD], W.BOOL),
            "QueryInformationJobObject": ([W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.c_void_p], W.BOOL),
            "IsProcessInJob": ([W.HANDLE, W.HANDLE, C.POINTER(W.BOOL)], W.BOOL),
            "TerminateJobObject": ([W.HANDLE, W.UINT], W.BOOL),
            "TerminateProcess": ([W.HANDLE, W.UINT], W.BOOL),
            "ResumeThread": ([W.HANDLE], W.DWORD),
            "WaitForSingleObject": ([W.HANDLE, W.DWORD], W.DWORD),
            "GetExitCodeProcess": ([W.HANDLE, C.POINTER(W.DWORD)], W.BOOL),
            "InitializeProcThreadAttributeList": ([C.c_void_p, W.DWORD, W.DWORD, C.POINTER(C.c_size_t)], W.BOOL),
            "UpdateProcThreadAttribute": ([C.c_void_p, W.DWORD, C.c_size_t, C.c_void_p,
                                           C.c_size_t, C.c_void_p, C.c_void_p], W.BOOL),
            "DeleteProcThreadAttributeList": ([C.c_void_p], None),
            "CreateProcessW": ([W.LPCWSTR, W.LPWSTR, C.c_void_p, C.c_void_p,
                                W.BOOL, W.DWORD, C.c_void_p, W.LPCWSTR,
                                C.POINTER(StartupEx), C.POINTER(ProcessInfo)], W.BOOL),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(self.kernel, name)
            fn.argtypes, fn.restype = args, result
        self.advapi.FreeSid.argtypes = [C.c_void_p]
        self.advapi.FreeSid.restype = C.c_void_p
        self.advapi.OpenProcessToken.argtypes = [W.HANDLE, W.DWORD, C.POINTER(W.HANDLE)]
        self.advapi.GetTokenInformation.argtypes = [W.HANDLE, C.c_int, C.c_void_p,
                                                    W.DWORD, C.POINTER(W.DWORD)]
        self.advapi.EqualSid.argtypes = [C.c_void_p, C.c_void_p]
        self.advapi.GetSidSubAuthorityCount.argtypes = [C.c_void_p]
        self.advapi.GetSidSubAuthorityCount.restype = C.POINTER(C.c_ubyte)
        self.advapi.GetSidSubAuthority.argtypes = [C.c_void_p, W.DWORD]
        self.advapi.GetSidSubAuthority.restype = C.POINTER(W.DWORD)

    def verify_token(self, process, expected_sid):
        """Confronta token real ANTES de executar até mesmo o loader do filho.

        Executáveis empacotados podem introduzir capacidades do manifesto;
        atributo solicitado não basta como evidência de isolamento.
        """
        token = W.HANDLE()
        self.check(self.advapi.OpenProcessToken(process, 8, C.byref(token)), "open_token")
        try:
            def info(kind):
                size = W.DWORD()
                self.advapi.GetTokenInformation(token, kind, None, 0, C.byref(size))
                if not 0 < size.value <= 65536:
                    raise IsolationError("token_info_size")
                buffer = C.create_string_buffer(size.value)
                self.check(self.advapi.GetTokenInformation(token, kind, buffer,
                    size, C.byref(size)), "token_info")
                return buffer
            if (W.DWORD.from_buffer(info(29)).value != 1
                    or W.DWORD.from_buffer(info(20)).value != 0
                    or W.DWORD.from_buffer(info(30)).value != 0):
                raise IsolationError("unexpected_appcontainer_token")
            package = info(31)
            if not self.advapi.EqualSid(C.c_void_p.from_buffer(package), expected_sid):
                raise IsolationError("unexpected_appcontainer_sid")
            integrity = info(25)
            sid = C.c_void_p.from_buffer(integrity)
            count = self.advapi.GetSidSubAuthorityCount(sid)[0]
            if not count or self.advapi.GetSidSubAuthority(sid, count - 1)[0] > 4096:
                raise IsolationError("unexpected_integrity")
            class Privilege(C.Structure):
                _fields_ = [("low", W.DWORD), ("high", W.LONG), ("attributes", W.DWORD)]
            privileges = info(3)
            count = W.DWORD.from_buffer(privileges).value
            if 4 + count * C.sizeof(Privilege) > len(privileges):
                raise IsolationError("invalid_privileges")
            for index in range(count):
                privilege = Privilege.from_buffer(privileges, 4 + index * C.sizeof(Privilege))
                if privilege.attributes & 2 and (privilege.low, privilege.high) != (23, 0):
                    raise IsolationError("unexpected_privilege")
        finally:
            self.kernel.CloseHandle(token)

    @staticmethod
    def check(result, operation):
        if not result:
            raise IsolationError(C.get_last_error(), operation)
        return result


class IsolatedProcess:
    """Handle único do Job no pai; descendentes não herdam nenhum handle.

    O watchdog é thread nativa de espera, independente do polling do
    coordenador. Morte do pai fecha o Job no kernel. Congelamento completo do
    pai/SO ainda requer supervisor externo, não implementado aqui.
    """
    def __init__(self, executable, arguments, *, appcontainer_sid, policy=IsolationPolicy()):
        self.api = Win32()
        self.policy = policy
        self.job = self.process = None
        self._lock = threading.Lock()
        self._done = threading.Event()
        self.timed_out = False
        self._watchdog = None
        executable = str(Path(executable).resolve(strict=True))
        if not appcontainer_sid or not appcontainer_sid.value:
            raise ValueError("AppContainer obrigatório")
        if not isinstance(arguments, (list, tuple)) or any(
                not isinstance(a, str) or "\0" in a for a in arguments):
            raise ValueError("Argumentos inválidos")
        k = self.api.kernel
        info = ProcessInfo()
        attributes = None
        initialized = False
        try:
            self.job = self.api.check(k.CreateJobObjectW(None, None), "create_job")
            limits = ExtendedLimits()
            # Tempo de CPU agregado, memória comprometida agregada, nº de processos,
            # morte ao fechar o último handle. Sem BREAKAWAY_OK/SILENT_BREAKAWAY_OK.
            limits.basic.flags = 0x4 | 0x8 | 0x200 | 0x2000 | 0x400
            limits.basic.job_time = policy.cpu_seconds * 10_000_000
            limits.basic.processes = policy.processes
            limits.job_memory = policy.memory_bytes
            self.api.check(k.SetInformationJobObject(self.job, 9, C.byref(limits), C.sizeof(limits)), "job_limits")
            rate = CpuRate(1 | 4, policy.cpu_rate)  # ENABLE | HARD_CAP
            self.api.check(k.SetInformationJobObject(self.job, 15, C.byref(rate), C.sizeof(rate)), "cpu_rate")
            size = C.c_size_t()
            k.InitializeProcThreadAttributeList(None, 2, 0, C.byref(size))
            if not size.value:
                raise IsolationError("attribute_list_size")
            attributes = C.create_string_buffer(size.value)
            self.api.check(k.InitializeProcThreadAttributeList(attributes, 2, 0, C.byref(size)), "initialize_attributes")
            initialized = True
            capabilities = SecurityCapabilities(appcontainer_sid, None, 0, 0)
            self.api.check(k.UpdateProcThreadAttribute(attributes, 0, 0x20009,
                C.byref(capabilities), C.sizeof(capabilities), None, None), "appcontainer_attributes")
            # Associação atômica na criação: morte do pai entre CreateProcess
            # e uma atribuição posterior não pode deixar processo órfão suspenso.
            jobs = (W.HANDLE * 1)(self.job)
            self.api.check(k.UpdateProcThreadAttribute(attributes, 0, 0x2000D,
                jobs, C.sizeof(jobs), None, None), "job_attributes")
            startup = StartupEx()
            startup.startup.cb = C.sizeof(startup)
            startup.attributes = C.cast(attributes, C.c_void_p)
            command = C.create_unicode_buffer(subprocess.list2cmdline([executable, *arguments]))
            # Allowlist: sem PATH/PYTHONPATH, proxy, credenciais ou variáveis da API.
            root = os.environ["SystemRoot"]
            # Win32 precisa de LOCALAPPDATA para resolver o perfil; o SO o
            # redireciona no filho. Isso não concede acesso ao diretório do pai.
            values = {"SystemRoot": root, "WINDIR": root,
                      "LOCALAPPDATA": os.environ["LOCALAPPDATA"]}
            environment = C.create_unicode_buffer("\0".join(
                f"{key}={values[key]}" for key in sorted(values, key=str.upper)) + "\0\0")
            self.api.check(k.CreateProcessW(executable, command, None, None, False,
                0x4 | 0x80000 | 0x400 | 0x8000000, environment, root,
                C.byref(startup), C.byref(info)), "create_suspended_appcontainer")
            self.process, self.pid = info.process, info.pid
            in_job = W.BOOL()
            self.api.check(k.IsProcessInJob(self.process, self.job, C.byref(in_job)), "query_job")
            if not in_job.value:
                raise IsolationError("process_not_in_job")
            self.api.verify_token(self.process, appcontainer_sid)
            if k.ResumeThread(info.thread) == 0xFFFFFFFF:
                raise IsolationError(C.get_last_error(), "resume_thread")
            self._watchdog = threading.Thread(target=self._watch, daemon=True,
                                              name="ecowatt-isolation-watchdog")
            self._watchdog.start()
        except BaseException:
            if info.process:
                k.TerminateProcess(info.process, 1)
                k.WaitForSingleObject(info.process, 5000)
            self.close()
            raise
        finally:
            if info.thread:
                k.CloseHandle(info.thread)
            if initialized:
                k.DeleteProcThreadAttributeList(attributes)

    def _watch(self):
        # Prazo continua valendo mesmo se o processo raiz já terminou e só
        # descendentes permanecem; close/wait também encerram esses processos.
        if not self._done.wait(self.policy.wall_seconds):
            with self._lock:
                if self.job:
                    self.timed_out = True
                    self.api.check(self.api.kernel.TerminateJobObject(self.job, 1460), "watchdog_terminate")

    def wait(self, seconds=185):
        if self.api.kernel.WaitForSingleObject(self.process, math.ceil(seconds * 1000)) != 0:
            raise IsolationError("wait_failed_or_expired")
        code = W.DWORD()
        self.api.check(self.api.kernel.GetExitCodeProcess(self.process, C.byref(code)), "exit_code")
        self.close()
        return code.value

    def process_ids(self):
        """Snapshot técnico do Job, inclusive descendentes; não é autorização."""
        class IdList(C.Structure):
            _fields_ = [("assigned", W.DWORD), ("count", W.DWORD),
                        ("ids", C.c_size_t * 4)]
        result = IdList()
        with self._lock:
            if not self.job:
                return ()
            self.api.check(self.api.kernel.QueryInformationJobObject(
                self.job, 3, C.byref(result), C.sizeof(result), None), "job_process_ids")
        return tuple(result.ids[:result.count])

    def close(self):
        self._done.set()
        with self._lock:
            if self.job:
                self.api.kernel.CloseHandle(self.job)
                self.job = None
        if self._watchdog and self._watchdog is not threading.current_thread():
            self._watchdog.join(5)
        if self.process:
            self.api.kernel.WaitForSingleObject(self.process, 5000)
            self.api.kernel.CloseHandle(self.process)
            self.process = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
