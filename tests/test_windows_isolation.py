"""Probes Win32 reais, exclusivamente com programas e canários inventados.

Integração requer ECOWATT_WINDOWS_ISOLATION_TESTS=1: cria/remove perfil
AppContainer por usuário. Falha de SO nunca vira skip quando habilitada.
"""
import ctypes as C
from ctypes import wintypes as W
from dataclasses import replace
import json
import os
from pathlib import Path
import select
import shutil
import socket
import subprocess
import sys
import time

import pytest

from ecowatt.windows_isolation import (
    ExtendedLimits, CpuRate, IsolationError, IsolationPolicy, IsolatedProcess,
    Win32,
)


@pytest.mark.parametrize("changes", [
    {"memory_bytes": True}, {"memory_bytes": 31_999_999},
    {"memory_bytes": 1_000_000_001}, {"cpu_seconds": 0},
    {"cpu_seconds": 181}, {"cpu_rate": 0}, {"cpu_rate": 10001},
    {"processes": 0}, {"processes": 5}, {"processes": 1.0},
    {"wall_seconds": True}, {"wall_seconds": float("nan")},
    {"wall_seconds": float("inf")}, {"wall_seconds": 0}, {"wall_seconds": 181},
])
def test_policy_rejects_invalid_or_expanded_limits(changes):
    with pytest.raises(ValueError):
        replace(IsolationPolicy(), **changes)


native = pytest.mark.skipif(
    os.name != "nt" or os.environ.get("ECOWATT_WINDOWS_ISOLATION_TESTS") != "1",
    reason="Probes Win32 explícitos: ECOWATT_WINDOWS_ISOLATION_TESTS=1",
)


@pytest.fixture
def profile(tmp_path, monkeypatch):
    # Provisionado pelo runner PowerShell fora da identidade MSIX do Python.
    sid_string = os.environ['ECOWATT_SYNTHETIC_PROFILE_SID']
    api = Win32()
    api.advapi.ConvertStringSidToSidW.argtypes = [W.LPCWSTR, C.POINTER(C.c_void_p)]
    sid = C.c_void_p()
    try:
        api.check(api.advapi.ConvertStringSidToSidW(sid_string, C.byref(sid)), 'parse_sid')
        # Cópia local do runtime JÁ instalado, sem download/instalação. Evita
        # capacidades injetadas pelo manifesto do executável MSIX da Store.
        # ACL exclusiva para este SID no diretório sintético, nunca no original.
        runtime = tmp_path / "synthetic-runtime"
        runtime.mkdir()
        base = Path(os.environ.get('ECOWATT_TEST_SOURCE_PYTHON', sys.base_prefix))
        for filename in ("python.exe", "python313.dll", "python3.dll",
                     "vcruntime140.dll", "vcruntime140_1.dll"):
            if (base / filename).is_file():
                shutil.copyfile(base / filename, runtime / filename)
        (runtime / "python313._pth").write_text(
            f"{base / 'Lib'}\n{base / 'DLLs'}\n{base}\n.\n", encoding="utf-8")
        api = Win32()
        api.advapi.ConvertSidToStringSidW.argtypes = [C.c_void_p, C.POINTER(W.LPWSTR)]
        text = W.LPWSTR()
        api.check(api.advapi.ConvertSidToStringSidW(sid, C.byref(text)), "sid_text")
        sid_string = text.value
        api.kernel.LocalFree.argtypes = [C.c_void_p]
        api.kernel.LocalFree(C.cast(text, C.c_void_p))
        subprocess.run(["icacls.exe", str(runtime), "/grant",
                        f"*{sid_string}:(OI)(CI)(RX)", "/T", "/Q"],
                       check=True, capture_output=True)
        # Bibliotecas copiadas pelo runner: acesso RX apenas ao perfil sintético.
        for directory in (base / 'Lib', base / 'DLLs'):
            subprocess.run(["icacls.exe", str(directory), "/grant",
                            f"*{sid_string}:(OI)(CI)(RX)", "/T", "/Q"],
                           check=True, capture_output=True)
        monkeypatch.setenv("ECOWATT_SYNTHETIC_RUNTIME", str(runtime / "python.exe"))
        yield sid
    finally:
        if sid.value:
            api.advapi.FreeSid(sid)


def python_executable():
    # Executável base, não o launcher da venv (não precisa de site-packages).
    return os.environ.get("ECOWATT_SYNTHETIC_RUNTIME", str(Path(sys.base_prefix) / "python.exe"))


def launch(sid, code, **limits):
    return IsolatedProcess(python_executable(), ["-I", "-B", "-S", "-c", code],
                           appcontainer_sid=sid, policy=IsolationPolicy(**limits))


@native
def test_runtime_and_os_limits_are_effective(profile):
    with launch(profile, "import time; time.sleep(30)", wall_seconds=10) as process:
        api = process.api
        for kind, result in [(9, ExtendedLimits()), (15, CpuRate())]:
            api.check(api.kernel.QueryInformationJobObject(process.job, kind,
                C.byref(result), C.sizeof(result), None), "readback_limits")
            if kind == 9:
                assert 1_000_000_000 - 65536 < result.job_memory <= 1_000_000_000
                assert result.basic.job_time == 30 * 10_000_000
                assert result.basic.processes == 4
                assert result.basic.flags & 0x2000  # KILL_ON_JOB_CLOSE
                assert not result.basic.flags & (0x800 | 0x1000)  # no breakaway
            else:
                assert result.flags == 5 and result.rate == 2500
        assert process.process_ids() == (process.pid,)
    with launch(profile, "raise SystemExit(42)") as process:
        assert process.wait() == 42


@native
def test_real_token_privileges_and_parent_memory_denied(profile):
    code = r'''
import ctypes as C
from ctypes import wintypes as W
import os
k=C.WinDLL('kernel32',use_last_error=True)
a=C.WinDLL('advapi32',use_last_error=True)
k.GetCurrentProcess.restype=W.HANDLE
a.OpenProcessToken.argtypes=[W.HANDLE,W.DWORD,C.POINTER(W.HANDLE)]
a.GetTokenInformation.argtypes=[W.HANDLE,C.c_int,C.c_void_p,W.DWORD,C.POINTER(W.DWORD)]
t=W.HANDLE()
assert a.OpenProcessToken(k.GetCurrentProcess(),8,C.byref(t))
def info(kind):
    size=W.DWORD()
    a.GetTokenInformation(t,kind,None,0,C.byref(size))
    value=C.create_string_buffer(size.value)
    assert a.GetTokenInformation(t,kind,value,size,C.byref(size))
    return value
assert W.DWORD.from_buffer(info(29)).value == 1  # TokenIsAppContainer
assert W.DWORD.from_buffer(info(20)).value == 0  # TokenElevation
assert W.DWORD.from_buffer(info(30)).value == 0  # TokenCapabilities count
integrity=info(25)
sid=C.c_void_p.from_buffer(integrity)
a.GetSidSubAuthorityCount.argtypes=[C.c_void_p]
a.GetSidSubAuthorityCount.restype=C.POINTER(C.c_ubyte)
a.GetSidSubAuthority.argtypes=[C.c_void_p,W.DWORD]
a.GetSidSubAuthority.restype=C.POINTER(W.DWORD)
count=a.GetSidSubAuthorityCount(sid)[0]
assert a.GetSidSubAuthority(sid,count-1)[0] <= 4096
class Priv(C.Structure):
    _fields_=[('low',W.DWORD),('high',W.LONG),('attributes',W.DWORD)]
privileges=info(3)
for i in range(W.DWORD.from_buffer(privileges).value):
    p=Priv.from_buffer(privileges,4+i*C.sizeof(Priv))
    # Só SeChangeNotifyPrivilege (traversal), nunca debug/impersonation/backup.
    assert not p.attributes & 2 or (p.low,p.high)==(23,0)
k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD]
k.OpenProcess.restype=W.HANDLE
assert not k.OpenProcess(0x410,False,PARENT_PID)
assert C.get_last_error()==5
assert 'ECOWATT_SYNTHETIC_SECRET' not in os.environ
'''.replace("PARENT_PID", str(os.getpid()))
    with launch(profile, code) as process:
        assert process.wait() == 0


@native
def test_network_denied_by_os_not_by_python_monkeypatch(profile):
    from contextlib import ExitStack
    with ExitStack() as stack:
        endpoints = []
        listeners = []
        for family, host in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
            for kind in (socket.SOCK_STREAM, socket.SOCK_DGRAM):
                listener = stack.enter_context(socket.socket(family, kind))
                listener.bind((host, 0))
                listener.settimeout(2)
                port = listener.getsockname()[1]
                if kind == socket.SOCK_STREAM:
                    listener.listen()
                endpoints.append((int(family), int(kind), host, port))
                listeners.append(listener)

        def positive_controls():
            for (family, kind, host, port), listener in zip(endpoints, listeners):
                with socket.socket(family, kind) as control:
                    control.settimeout(2)
                    if kind == socket.SOCK_STREAM:
                        control.connect((host, port))
                        connection, _ = listener.accept()
                        connection.close()
                    else:
                        control.sendto(b"SYNTHETIC", (host, port))
                        assert listener.recv(32) == b"SYNTHETIC"

        positive_controls()
        code = f'''
import socket
for family,kind,host,port in {endpoints!r}:
    with socket.socket(family,kind) as s:
        s.settimeout(1)
        try:
            if kind==socket.SOCK_STREAM:
                s.connect((host,port))
            else:
                s.sendto(b"SYNTHETIC",(host,port))
        except TimeoutError:
            pass  # O SO pode descartar silenciosamente; o pai verifica entrega.
        except OSError as e:
            if e.winerror!=10013:
                raise SystemExit(e.winerror or 1)
        else:
            if kind==socket.SOCK_STREAM:
                raise SystemExit(99)
'''
        with launch(profile, code) as process:
            assert process.wait() == 0
        assert select.select(listeners, [], [], .25)[0] == []
        positive_controls()  # Serviços permaneceram alcançáveis fora do isolamento.


@native
def test_canary_files_read_write_denied_and_environment_clean(profile, tmp_path, monkeypatch):
    canary = tmp_path / "invented-credentials.txt"
    canary.write_text("SYNTHETIC-CANARY", encoding="ascii")
    monkeypatch.setenv("ECOWATT_SYNTHETIC_SECRET", "invented-not-a-secret")
    code = f'''
import os
assert 'ECOWATT_SYNTHETIC_SECRET' not in os.environ
for mode in ('rb','wb'):
    try:
        open({str(canary)!r},mode)
    except PermissionError:
        pass
    else:
        raise AssertionError('canary_access_allowed')
'''
    with launch(profile, code) as process:
        assert process.wait() == 0
    assert canary.read_text(encoding="ascii") == "SYNTHETIC-CANARY"


@native
def test_memory_exhaustion_is_bounded(profile):
    code = '''
chunks=[]
try:
    for i in range(128):
        chunks.append(bytearray(4_000_000))
except MemoryError:
    raise SystemExit(43)
raise SystemExit(99)
'''
    with launch(profile, code, memory_bytes=96_000_000) as process:
        assert process.wait() == 43


@native
def test_cpu_time_exhaustion_kills_busy_process(profile):
    with launch(profile, "while True: pass", cpu_seconds=1, cpu_rate=10000,
                wall_seconds=15) as process:
        assert process.wait(20) != 0
        assert not process.timed_out  # orçamento CPU, não apenas timeout


@native
def test_watchdog_without_coordinator_polling(profile):
    started = time.monotonic()
    with launch(profile, "import time; time.sleep(30)", wall_seconds=0.5) as process:
        assert process.wait(10) == 1460
        assert process.timed_out
    assert time.monotonic() - started < 10


@native
def test_breakaway_denied_and_process_count_limited(profile):
    code = r'''
import subprocess,sys,time
args=[sys.executable,'-I','-B','-S','-c','import time; time.sleep(30)']
try:
    subprocess.Popen(args,creationflags=0x01000000)
except OSError:
    pass
else:
    raise AssertionError('breakaway_allowed')
children=[]
for i in range(3):
    children.append(subprocess.Popen(args))
try:
    subprocess.Popen(args)
except OSError:
    pass
else:
    raise AssertionError('process_limit_ignored')
'''
    with launch(profile, code) as process:
        assert process.wait() == 0


@native
@pytest.mark.parametrize("failure", ["job_attributes", "token"])
def test_setup_failure_never_runs_unconfined(profile, monkeypatch, failure):
    import ecowatt.windows_isolation as backend
    api = Win32()
    original_check = api.check
    resumed = []
    original_resume = api.kernel.ResumeThread
    def resume(handle):
        resumed.append(True)
        return original_resume(handle)
    def check(result, operation):
        if failure == operation:
            raise IsolationError("synthetic_setup_failure")
        return original_check(result, operation)
    def verify(*args):
        if failure == "token":
            raise IsolationError("synthetic_setup_failure")
    monkeypatch.setattr(api.kernel, "ResumeThread", resume)
    monkeypatch.setattr(api, "check", check)
    monkeypatch.setattr(api, "verify_token", verify)
    monkeypatch.setattr(backend, "Win32", lambda: api)
    with pytest.raises(IsolationError, match="synthetic_setup_failure"):
        launch(profile, "raise SystemExit(99)")
    assert resumed == []


@native
def test_abrupt_parent_death_kills_root_and_grandchildren(profile):
    api = Win32()
    a = api.advapi
    a.ConvertSidToStringSidW.argtypes = [C.c_void_p, C.POINTER(W.LPWSTR)]
    a.ConvertSidToStringSidW.restype = W.BOOL
    sid_text = W.LPWSTR()
    api.check(a.ConvertSidToStringSidW(profile, C.byref(sid_text)), "sid_to_string")
    value = sid_text.value
    api.kernel.LocalFree.argtypes = [C.c_void_p]
    api.kernel.LocalFree(C.cast(sid_text, C.c_void_p))
    worker = '''
import subprocess,sys,time
args=[sys.executable,'-I','-B','-S','-c','import time; time.sleep(60)']
children=[subprocess.Popen(args),subprocess.Popen(args)]
time.sleep(60)
'''
    helper = f'''
import ctypes as C,json,time
from ecowatt.windows_isolation import Win32,IsolatedProcess,IsolationPolicy
a=Win32().advapi
a.ConvertStringSidToSidW.argtypes=[C.c_wchar_p,C.POINTER(C.c_void_p)]
sid=C.c_void_p()
assert a.ConvertStringSidToSidW({value!r},C.byref(sid))
p=IsolatedProcess({python_executable()!r},['-I','-B','-S','-c',{worker!r}],
                  appcontainer_sid=sid,policy=IsolationPolicy(wall_seconds=60))
deadline=time.monotonic()+20
previous=()
while True:
    current=p.process_ids()
    if len(current)>=3 and current==previous:
        break
    previous=current
    if time.monotonic()>=deadline:
        raise RuntimeError(('tree_snapshot',p.process_ids()))
    time.sleep(.25)
print(json.dumps(p.process_ids()),flush=True)
time.sleep(60)
'''
    parent = subprocess.Popen([sys.executable, "-c", helper], stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True)
    handles = []
    k = api.kernel
    k.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
    k.OpenProcess.restype = W.HANDLE
    # Limite independente para o helper se sua inicialização falhar/travar.
    import threading
    timer = threading.Timer(30, parent.kill)
    timer.start()
    try:
        line = parent.stdout.readline()
        assert line, parent.communicate(timeout=5)[1]
        pids = json.loads(line)
        assert 3 <= len(pids) <= 4  # inclui launchers nativos quando presentes
        for pid in pids:
            handles.append(api.check(k.OpenProcess(0x100000, False, pid), "open_probe_process"))
        parent.kill()  # TerminateProcess: sem finally, close ou cancelamento cooperativo
        parent.wait(timeout=5)
        for handle in handles:
            assert k.WaitForSingleObject(handle, 5000) == 0
    finally:
        timer.cancel()
        if parent.poll() is None:
            parent.kill()
        parent.communicate(timeout=5)
        for handle in handles:
            k.CloseHandle(handle)
