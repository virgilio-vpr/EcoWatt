"""Auditoria conservadora somente leitura; não modifica políticas do Windows.

Valores ausentes/negados não provam proteção. Nenhuma variável/configuração
do cliente pode transformar estas observações em autorização documental.
"""
from dataclasses import asdict, dataclass
import json
import os


@dataclass(frozen=True)
class EnvironmentAudit:
    crash_dump_enabled: int | None
    encrypt_paging_file: int | None
    local_dump_configured: bool | None
    ram_temporary_verified: bool = False
    proxy_no_spool_verified: bool = False

    @property
    def blockers(self):
        reasons = ["process_dumps_not_excluded", "ram_temporary_not_verified",
                   "proxy_no_spool_not_verified", "document_adapter_not_approved"]
        if self.crash_dump_enabled != 0:
            reasons.append("system_dumps_not_excluded")
        if self.encrypt_paging_file != 1:
            reasons.append("protected_swap_not_verified")
        return tuple(reasons)


def audit_windows():
    if os.name != "nt":
        return EnvironmentAudit(None, None, None)
    import winreg
    def dword(path, name):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0,
                                winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
                value, kind = winreg.QueryValueEx(key, name)
                return value if kind == winreg.REG_DWORD and type(value) is int else None
        except OSError:
            return None
    def local_dumps():
        # Presença global OU configuração por executável. Ausência não é
        # evidência de ausência de WER, debugger, EDR ou dumps manuais.
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps",
                    0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY):
                return True
        except FileNotFoundError:
            return False
        except OSError:
            return None
    return EnvironmentAudit(
        dword(r"SYSTEM\CurrentControlSet\Control\CrashControl", "CrashDumpEnabled"),
        dword(r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management", "EncryptPagingFile"),
        local_dumps())


if __name__ == "__main__":
    report = audit_windows()
    print(json.dumps({**asdict(report), "blockers": report.blockers,
                      "document_processing_enabled": False}, sort_keys=True))
