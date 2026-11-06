import secrets

from sqlalchemy import delete, select, update

from ecowatt.config import Settings
from ecowatt.db.models import AuditEvent, AuthSession, Company, EmailToken, RateBucket, User, now
from ecowatt.db.session import transaction
from ecowatt.errors import DomainError
from ecowatt.schemas import Registration
from ecowatt.security.passwords import hasher, verify
from ecowatt.security.tokens import digest, new_token
from ecowatt.services.mail import Message, MailDeliveryError


def rate_limit(engine, purpose: str, ip: str, email: str = ""):
    """Contadores persistentes, commit independente mesmo quando login falha."""
    stamp = now()
    exceeded = False
    with transaction(engine, write=True) as db:
        db.execute(delete(RateBucket).where(RateBucket.window_start < stamp - 3600))
        for scope, value, maximum in [("ip", ip, 50), ("email", email, 10)]:
            if not value:
                continue
            key = digest(f"{purpose}:{scope}:{value}")
            bucket = db.get(RateBucket, key)
            if bucket is None:
                db.add(RateBucket(key=key, window_start=stamp, attempts=1))
            else:
                bucket.attempts += 1
                exceeded |= bucket.attempts > maximum
    if exceeded:
        raise DomainError("rate_limited", "Tente novamente mais tarde.", 429)


def issue_token(db, user: User, purpose: str, settings: Settings):
    stamp = now()
    db.execute(update(EmailToken).where(EmailToken.user_id == user.id,
               EmailToken.purpose == purpose, EmailToken.consumed_at.is_(None)).values(consumed_at=stamp))
    token = new_token()
    db.add(EmailToken(user_id=user.id, token_hash=digest(token), purpose=purpose,
                      expires_at=stamp + (86400 if purpose == "activation" else 1800)))
    # Fragmento evita token em access logs; tela lê e envia POST JSON.
    return Message(user.email, purpose, f"{settings.public_origin}/auth/{purpose}#token={token}")


def register(engine, payload: Registration, settings):
    encoded = hasher.hash(payload.password.get_secret_value())
    with transaction(engine, write=True) as db:
        existing = db.scalar(select(User).where(User.email == payload.email))
        if existing:
            return
        company = Company(**payload.company.model_dump())
        db.add(company)
        db.flush()
        user = User(company_id=company.id, email=payload.email,
                    responsible_name=payload.responsible_name, password_hash=encoded)
        db.add(user)
        db.flush()
        message = issue_token(db, user, "activation", settings)
    return message


def request_email(engine, email, purpose, settings, dummy_hash):
    # Custo de hash também no caminho sem usuário para reduzir enumeração temporal.
    verify(dummy_hash, "unmatched-password")
    message = None
    with transaction(engine, write=True) as db:
        user = db.scalar(select(User).where(User.email == email))
        eligible = user and ((purpose == "activation" and user.status == "pending")
                            or (purpose == "reset" and user.status == "active"))
        if eligible:
            message = issue_token(db, user, purpose, settings)
    return message


def deliver(engine, mailer, message):
    """Rede fora da transação. Falha não revela existência de conta."""
    try:
        mailer.send(message)
    except MailDeliveryError:
        # Revogar apenas o token cujo envio falhou, sem invalidar reenvio mais novo.
        token = message.link.rsplit("#token=", 1)[1]
        with transaction(engine, write=True) as db:
            record = db.scalar(select(EmailToken).where(EmailToken.token_hash == digest(token)))
            if record:
                record.consumed_at = now()
                db.add(AuditEvent(actor_id=None, action="email_delivery_failed", resource_id=record.id))


def consume_email(engine, token: str, purpose: str, password: str | None = None):
    encoded = hasher.hash(password) if password is not None else None
    with transaction(engine, write=True) as db:
        record = db.scalar(select(EmailToken).where(EmailToken.token_hash == digest(token),
                           EmailToken.purpose == purpose, EmailToken.consumed_at.is_(None),
                           EmailToken.expires_at > now()))
        if not record:
            raise DomainError("invalid_token", "Link inválido ou expirado.")
        user = db.get(User, record.user_id)
        expected_status = "pending" if purpose == "activation" else "active"
        if not user or user.status != expected_status:
            raise DomainError("invalid_token", "Link inválido ou expirado.")
        record.consumed_at = now()
        if purpose == "activation":
            user.status, user.confirmed_at = "active", now()
        else:
            user.password_hash = encoded
            revoke_sessions(db, user.id)
        db.add(AuditEvent(actor_id=user.id, action=purpose, resource_id=user.id))


def revoke_sessions(db, user_id):
    db.execute(update(AuthSession).where(AuthSession.user_id == user_id,
               AuthSession.revoked_at.is_(None)).values(revoked_at=now()))


def login(engine, email, password, settings, dummy_hash, previous_token=None):
    # Argon2 fora da transação de escrita; revalidar hash/estado após verificação.
    with transaction(engine) as db:
        user = db.scalar(select(User).where(User.email == email))
        encoded = user.password_hash if user else dummy_hash
        user_id = user.id if user else None
    valid = verify(encoded, password)
    if not valid or user_id is None:
        raise DomainError("invalid_credentials", "E-mail ou senha inválidos.", 401)
    replacement = hasher.hash(password) if hasher.check_needs_rehash(encoded) else encoded
    token, csrf = new_token(), new_token()
    with transaction(engine, write=True) as db:
        user = db.get(User, user_id)
        if user.status != "active" or user.confirmed_at is None or user.password_hash != encoded:
            raise DomainError("invalid_credentials", "E-mail ou senha inválidos.", 401)
        user.password_hash = replacement
        if previous_token:
            db.execute(update(AuthSession).where(AuthSession.token_hash == digest(previous_token)).values(revoked_at=now()))
        db.add(AuthSession(user_id=user.id, token_hash=digest(token), csrf_hash=digest(csrf),
                           expires_at=now() + settings.session_absolute_seconds))
        db.add(AuditEvent(actor_id=user.id, action="login", resource_id=user.id))
    return token, csrf


def authenticate(db, token, settings, csrf=None):
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == digest(token or "")))
    stamp = now()
    if (not session or session.revoked_at is not None or session.expires_at <= stamp
            or session.last_seen_at + settings.session_idle_seconds <= stamp):
        raise DomainError("authentication_required", "Entre novamente.", 401)
    user = db.get(User, session.user_id)
    if user.status != "active" or user.confirmed_at is None:
        raise DomainError("authentication_required", "Entre novamente.", 401)
    if csrf is not None and not secrets.compare_digest(session.csrf_hash, digest(csrf)):
        raise DomainError("csrf_failed", "Requisição não autorizada.", 403)
    session.last_seen_at = stamp
    return user, session
