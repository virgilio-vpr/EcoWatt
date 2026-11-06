from contextlib import contextmanager
from email import policy
from email.parser import BytesParser
import smtplib
import socketserver
from threading import Thread, Condition
from urllib.parse import parse_qs, urlsplit

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from ecowatt.config import Settings
from ecowatt.db.models import AuditEvent, EmailToken, RateBucket, User, now
from ecowatt.db.session import transaction
from ecowatt.main import create_app
from ecowatt.services.mail import MailDeliveryError, Message, SMTPMailer
from conftest import Client
from test_auth import registration


@contextmanager
def smtp_capture():
    """Servidor sintético efêmero, só loopback e memória; não encaminha mensagens."""
    class Mailbox(list):
        def __init__(self):
            super().__init__()
            self.ready = Condition()

        def append(self, item):
            with self.ready:
                super().append(item)
                self.ready.notify_all()

        def wait_for_count(self, count):
            with self.ready:
                assert self.ready.wait_for(lambda: len(self) >= count, timeout=5)

    messages = Mailbox()

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.wfile.write(b"220 local-test\r\n")
            while line := self.rfile.readline():
                command = line.split(b" ", 1)[0].strip().upper()
                if command in {b"EHLO", b"HELO"}:
                    self.wfile.write(b"250-local-test\r\n250 SIZE 100000\r\n")
                elif command == b"DATA":
                    self.wfile.write(b"354 End with dot\r\n")
                    data = []
                    while (line := self.rfile.readline()) not in {b".\r\n", b""}:
                        data.append(line[1:] if line.startswith(b"..") else line)
                    messages.append(BytesParser(policy=policy.default).parsebytes(b"".join(data)))
                    self.wfile.write(b"250 Accepted locally\r\n")
                elif command == b"QUIT":
                    self.wfile.write(b"221 Bye\r\n")
                    break
                else:
                    self.wfile.write(b"250 OK\r\n")

    with socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler) as server:
        server.daemon_threads = True
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield server.server_address[1], messages
        finally:
            server.shutdown()
            thread.join(timeout=5)


def smtp_settings(base, port):
    values = base.model_dump()
    values.update(email_provider="smtp", smtp_host="127.0.0.1", smtp_port=port, smtp_security="local")
    return Settings(_env_file=None, **values)


def test_real_local_smtp_registration_and_link_consumption(environment):
    with smtp_capture() as (port, messages):
        app = create_app(smtp_settings(environment.settings, port))
        try:
            client = Client(app).prepare()
            response = client.request("POST", "/api/v1/auth/register", json=registration())
            assert response.status_code == 202
            assert len(messages) == 1
            message = messages[0]
            assert message["To"] == "new@ecowatt.test"
            assert "24 horas" in message.get_content()
            link = next(line for line in message.get_content().splitlines() if "#token=" in line)
            token = parse_qs(urlsplit(link).fragment)["token"][0]
            # GET não consome link; HTML e access URL não contêm token.
            page = client.request("GET", urlsplit(link).path)
            assert page.status_code == 200 and token not in page.text
            with transaction(app.state.engine) as db:
                record = db.scalar(select(EmailToken))
                assert record.consumed_at is None and record.token_hash != token
            assert client.request("POST", "/api/v1/auth/activate", json={"token": token}).status_code == 200
            client.login("new@ecowatt.test")
            assert client.request("POST", "/api/v1/auth/forgot-password", json={"email": "new@ecowatt.test"}).status_code == 202
            assert len(messages) == 2 and "30 minutos" in messages[-1].get_content()
        finally:
            app.state.engine.dispose()


def test_network_delivery_occurs_after_commit_without_sqlite_write_lock(environment):
    class Probe:
        def send(self, message):
            with transaction(environment.app.state.engine, write=True) as db:
                assert db.scalar(select(User).where(User.email == "new@ecowatt.test"))
                assert db.scalar(select(EmailToken))
                db.add(RateBucket(key="probe", window_start=now(), attempts=1))
    environment.app.state.mailer = Probe()
    client = environment.client().prepare()
    assert client.request("POST", "/api/v1/auth/register", json=registration()).status_code == 202


def test_failed_delivery_is_neutral_revokes_token_and_allows_resend(environment):
    class Failure:
        def send(self, message):
            raise MailDeliveryError("Sensitive diagnostics must not be returned")
    environment.app.state.mailer = Failure()
    client = environment.client().prepare()
    response = client.request("POST", "/api/v1/auth/register", json=registration())
    assert response.status_code == 202 and "Sensitive" not in response.text
    known = client.request("POST", "/api/v1/auth/resend-activation", json={"email": "new@ecowatt.test"})
    unknown = client.request("POST", "/api/v1/auth/resend-activation", json={"email": "unknown@ecowatt.test"})
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    with transaction(environment.app.state.engine) as db:
        assert all(t.consumed_at is not None for t in db.scalars(select(EmailToken)))
        assert db.scalar(select(AuditEvent).where(AuditEvent.action == "email_delivery_failed"))
        assert db.scalar(select(User).where(User.email == "new@ecowatt.test")).status == "pending"
    environment.app.state.mailer = environment.mailer
    assert client.request("POST", "/api/v1/auth/resend-activation", json={"email": "new@ecowatt.test"}).status_code == 202
    assert len(environment.mailer.messages) == 1


@pytest.mark.parametrize("values", [
    {"smtp_host": "mail.example", "smtp_security": "local"},
    {"smtp_host": "localhost", "smtp_security": "local"},
    {"smtp_host": "127.0.0.1", "smtp_security": "local", "smtp_username": "user", "smtp_password": "secret"},
    {"smtp_host": "mail.example", "smtp_username": "user"},
    {"smtp_host": "mail.example", "smtp_sender": "bad\r\nBcc: injected@example.com"},
    {"smtp_host": "mail.example", "smtp_timeout_seconds": 0},
])
def test_unsafe_smtp_configuration_rejected(values):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, email_provider="smtp", **values)


@pytest.mark.parametrize("security", ["starttls", "ssl"])
def test_tls_and_login_order_and_sanitized_failure(monkeypatch, security):
    events = []

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            events.append("connect")
            if security == "ssl":
                assert kwargs["context"].check_hostname
                events.append("ssl")

        def ehlo(self): events.append("ehlo")
        def starttls(self, context):
            assert context.check_hostname
            events.append("tls")
        def login(self, user, password):
            assert events.index("tls" if security == "starttls" else "ssl") < len(events)
            events.append("login")
        def send_message(self, message):
            events.append("send")
            raise smtplib.SMTPDataError(550, b"sensitive-server-diagnostics")
        def close(self): events.append("close")

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)
    settings = Settings(_env_file=None, email_provider="smtp", smtp_host="mail.example",
                        smtp_security=security, smtp_username="synthetic", smtp_password="synthetic")
    with pytest.raises(MailDeliveryError) as error:
        SMTPMailer(settings).send(Message("user@ecowatt.test", "reset", "http://127.0.0.1:8000/auth/reset#token=synthetic"))
    assert "sensitive" not in str(error.value)
    assert events[-1] == "close"
    assert events.index("login") < events.index("send")


def test_missing_starttls_never_falls_back_to_plaintext(monkeypatch):
    events = []

    class NoTLS:
        def __init__(self, *args, **kwargs): pass
        def ehlo(self): pass
        def starttls(self, context): raise smtplib.SMTPNotSupportedError("TLS unsupported")
        def login(self, *args): events.append("login")
        def send_message(self, message): events.append("send")
        def close(self): events.append("close")

    monkeypatch.setattr(smtplib, "SMTP", NoTLS)
    settings = Settings(_env_file=None, email_provider="smtp", smtp_host="mail.example",
                        smtp_username="synthetic", smtp_password="synthetic")
    with pytest.raises(MailDeliveryError):
        SMTPMailer(settings).send(Message("user@ecowatt.test", "activation", "synthetic"))
    assert events == ["close"]
