from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response
from sqlalchemy import update
from uuid import UUID

from ecowatt.api.dependencies import (CSRF_COOKIE, SESSION_COOKIE, authenticated,
    check_public_csrf, set_cookie)
from ecowatt.db.models import AuditEvent, EmailToken, User, now
from ecowatt.db.session import transaction
from ecowatt.errors import DomainError
from ecowatt.schemas import EmailInput, Login, Registration, ResetPassword, StatusInput, TokenInput
from ecowatt.schemas import CSRFOutput, LoginOutput, MessageOutput
from ecowatt.security.tokens import new_token
from ecowatt.services import auth
from ecowatt.services.mail import DisabledMailer
from ecowatt.services.simulations import require_admin

router = APIRouter(tags=["auth"])
NEUTRAL = {"message": "Solicitação recebida. Se não receber instruções, aguarde e tente reenviar."}


def throttle(request, purpose, email=""):
    auth.rate_limit(request.app.state.engine, purpose,
                    request.client.host if request.client else "unknown", email)


def require_mailer(request):
    if isinstance(request.app.state.mailer, DisabledMailer):
        raise DomainError("email_unavailable", "Provedor de e-mail ainda não configurado.", 503)


@router.get("/auth/csrf", response_model=CSRFOutput)
def csrf(request: Request, response: Response):
    token = request.cookies.get(CSRF_COOKIE)
    if request.cookies.get(SESSION_COOKIE):
        try:
            with transaction(request.app.state.engine, write=True) as db:
                auth.authenticate(db, request.cookies[SESSION_COOKIE], request.app.state.settings, csrf=token or "")
        except DomainError:
            # Sessão expirada não pode impedir novo login pelo navegador.
            response.delete_cookie(SESSION_COOKIE, path="/")
            token = None
    if not token or not 32 <= len(token) <= 128:
        token = new_token()
        set_cookie(response, CSRF_COOKIE, token, request.app.state.settings, 43200)
    return {"csrf_token": token}


@router.post("/auth/register", status_code=202, response_model=MessageOutput, dependencies=[Depends(check_public_csrf)])
def register(payload: Registration, request: Request, background_tasks: BackgroundTasks):
    require_mailer(request)
    throttle(request, "register", payload.email)
    message = auth.register(request.app.state.engine, payload, request.app.state.settings)
    if message is not None:
        background_tasks.add_task(auth.deliver, request.app.state.engine, request.app.state.mailer, message)
    return NEUTRAL


@router.post("/auth/resend-activation", status_code=202, response_model=MessageOutput, dependencies=[Depends(check_public_csrf)])
def resend(payload: EmailInput, request: Request, background_tasks: BackgroundTasks):
    require_mailer(request)
    throttle(request, "activation_request", payload.email)
    message = auth.request_email(request.app.state.engine, payload.email, "activation", request.app.state.settings,
                       request.app.state.dummy_hash)
    if message is not None:
        background_tasks.add_task(auth.deliver, request.app.state.engine, request.app.state.mailer, message)
    return NEUTRAL


@router.post("/auth/activate", response_model=MessageOutput, dependencies=[Depends(check_public_csrf)])
def activate(payload: TokenInput, request: Request):
    throttle(request, "activation_consume")
    auth.consume_email(request.app.state.engine, payload.token, "activation")
    return {"message": "E-mail confirmado. Entre com sua senha."}


@router.post("/auth/forgot-password", status_code=202, response_model=MessageOutput, dependencies=[Depends(check_public_csrf)])
def forgot(payload: EmailInput, request: Request, background_tasks: BackgroundTasks):
    require_mailer(request)
    throttle(request, "reset_request", payload.email)
    message = auth.request_email(request.app.state.engine, payload.email, "reset", request.app.state.settings,
                       request.app.state.dummy_hash)
    if message is not None:
        background_tasks.add_task(auth.deliver, request.app.state.engine, request.app.state.mailer, message)
    return NEUTRAL


@router.post("/auth/reset-password", response_model=MessageOutput, dependencies=[Depends(check_public_csrf)])
def reset(payload: ResetPassword, request: Request):
    throttle(request, "reset_consume")
    auth.consume_email(request.app.state.engine, payload.token, "reset", payload.password.get_secret_value())
    return {"message": "Senha redefinida. Entre novamente."}


@router.post("/auth/login", response_model=LoginOutput, dependencies=[Depends(check_public_csrf)])
def login(payload: Login, request: Request, response: Response):
    throttle(request, "login", payload.email)
    settings = request.app.state.settings
    token, csrf_token = auth.login(request.app.state.engine, payload.email, payload.password.get_secret_value(),
                        settings, request.app.state.dummy_hash, request.cookies.get(SESSION_COOKIE))
    set_cookie(response, SESSION_COOKIE, token, settings, settings.session_absolute_seconds)
    set_cookie(response, CSRF_COOKIE, csrf_token, settings, settings.session_absolute_seconds)
    return {"message": "Acesso autorizado.", "csrf_token": csrf_token}


@router.post("/auth/logout", status_code=204)
def logout(response: Response, principal=Depends(authenticated, scope="function")):
    db, actor, session = principal
    session.revoked_at = now()
    db.add(AuditEvent(actor_id=actor.id, action="logout", resource_id=actor.id))
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")


@router.post("/auth/revoke-sessions", status_code=204)
def revoke(response: Response, principal=Depends(authenticated, scope="function")):
    db, actor, _ = principal
    auth.revoke_sessions(db, actor.id)
    db.add(AuditEvent(actor_id=actor.id, action="sessions_revoked", resource_id=actor.id))
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")


@router.patch("/admin/users/{user_id}/status", status_code=204)
def status(user_id: UUID, payload: StatusInput, principal=Depends(authenticated, scope="function")):
    db, actor, _ = principal
    require_admin(actor)
    user = db.get(User, str(user_id))
    if not user:
        raise DomainError("not_found", "Usuário não encontrado.", 404)
    if payload.status == "active" and user.confirmed_at is None:
        raise DomainError("email_not_confirmed", "Ativação por e-mail necessária.", 409)
    if user.id == actor.id:
        raise DomainError("self_status_change", "Não altere seu próprio estado administrativo.", 409)
    user.status = payload.status
    auth.revoke_sessions(db, user.id)
    db.execute(update(EmailToken).where(EmailToken.user_id == user.id,
                EmailToken.consumed_at.is_(None)).values(consumed_at=now()))
    db.add(AuditEvent(actor_id=actor.id, action="user_status_changed", resource_id=user.id,
                      changes={"status": payload.status}))
