import secrets

from fastapi import Request

from ecowatt.db.session import transaction
from ecowatt.errors import DomainError
from ecowatt.services.auth import authenticate

SESSION_COOKIE = "ecowatt_session"
CSRF_COOKIE = "ecowatt_csrf"


def check_origin(request: Request):
    if request.headers.get("origin") != request.app.state.settings.public_origin:
        raise DomainError("csrf_failed", "Origem não autorizada.", 403)


def check_public_csrf(request: Request):
    check_origin(request)
    cookie = request.cookies.get(CSRF_COOKIE, "")
    header = request.headers.get("x-csrf-token", "")
    if len(cookie) < 32 or not secrets.compare_digest(cookie, header):
        raise DomainError("csrf_failed", "Requisição não autorizada.", 403)


def authenticated(request: Request):
    unsafe = request.method not in {"GET", "HEAD", "OPTIONS"}
    if unsafe:
        check_origin(request)
    with transaction(request.app.state.engine, write=True) as db:
        user, session = authenticate(db, request.cookies.get(SESSION_COOKIE), request.app.state.settings,
            csrf=request.headers.get("x-csrf-token", "") if unsafe else None)
        yield db, user, session


def set_cookie(response, name, value, settings, max_age):
    response.set_cookie(name, value, httponly=True, secure=settings.cookie_secure,
                        samesite="strict", path="/", max_age=max_age)
