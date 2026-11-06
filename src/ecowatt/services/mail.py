from dataclasses import dataclass
from threading import Lock
from typing import Protocol
from email.message import EmailMessage
import smtplib
import ssl


@dataclass(frozen=True, repr=False)
class Message:
    recipient: str
    purpose: str
    link: str


class Mailer(Protocol):
    def send(self, message: Message) -> None: ...


class MailDeliveryError(Exception):
    """Falha sanitizada; nunca propagar diagnóstico SMTP, destinatário ou link."""


class SMTPMailer:
    def __init__(self, settings):
        self.settings = settings

    def send(self, message: Message) -> None:
        settings = self.settings
        email = EmailMessage()
        email["From"] = settings.smtp_sender
        email["To"] = message.recipient
        if message.purpose == "activation":
            email["Subject"] = "EcoWatt — confirme seu e-mail"
            text = "Confirme seu e-mail em até 24 horas"
        else:
            email["Subject"] = "EcoWatt — redefina sua senha"
            text = "Redefina sua senha em até 30 minutos"
        email.set_content(f"{text}:\n\n{message.link}\n\nSe não solicitou, ignore esta mensagem.")
        client = None
        try:
            if settings.smtp_security == "ssl":
                client = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port,
                    timeout=settings.smtp_timeout_seconds, context=ssl.create_default_context())
            else:
                client = smtplib.SMTP(settings.smtp_host, settings.smtp_port,
                                     timeout=settings.smtp_timeout_seconds)
                client.ehlo()
                if settings.smtp_security == "starttls":
                    client.starttls(context=ssl.create_default_context())
                    client.ehlo()
            if settings.smtp_username:
                client.login(settings.smtp_username, settings.smtp_password.get_secret_value())
            if client.send_message(email):
                raise MailDeliveryError("Entrega não confirmada")
        except (OSError, smtplib.SMTPException, MailDeliveryError):
            raise MailDeliveryError("Entrega não confirmada") from None
        finally:
            if client is not None:
                # Após DATA aceito, falha em QUIT não transforma entrega em falha.
                try:
                    client.close()
                except OSError:
                    pass


def make_mailer(settings):
    return SMTPMailer(settings) if settings.email_provider == "smtp" else DisabledMailer()


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
