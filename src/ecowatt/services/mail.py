from dataclasses import dataclass
from threading import Lock
from typing import Protocol


@dataclass(frozen=True, repr=False)
class Message:
    recipient: str
    purpose: str
    link: str


class Mailer(Protocol):
    def send(self, message: Message) -> None: ...


class DisabledMailer:
    def send(self, message: Message) -> None:
        raise RuntimeError("Provedor de e-mail não configurado")


class MemoryMailer:
    """Somente testes injetam este adaptador. Nunca há rota pública de inbox."""
    def __init__(self):
        self.messages: list[Message] = []
        self._lock = Lock()

    def send(self, message: Message) -> None:
        with self._lock:
            self.messages.append(message)
