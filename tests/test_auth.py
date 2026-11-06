from urllib.parse import urlsplit, parse_qs

import pytest
from sqlalchemy import select

from ecowatt.db.models import AuthSession, EmailToken, User, now
from ecowatt.db.session import transaction
from ecowatt.main import create_app
from ecowatt.security.tokens import digest
from ecowatt.schemas import validate_password
from conftest import Client, PASSWORD


@pytest.mark.parametrize("password,valid", [
    ("weak", False), ("lowercase!12", False), ("UPPERCASE!12", False),
    ("NoSpecial123", False), ("OneDigit!1", False), ("Aa!12", False),
    ("Valida_12", True), ("Ábcdef!12", True),
])
def test_password_policy(password, valid):
    if valid:
        assert validate_password(password) == password
    else:
        with pytest.raises(ValueError):
            validate_password(password)


def registration(email="new@ecowatt.test"):
    return {"email": email, "email_confirmation": email, "password": PASSWORD,
            "password_confirmation": PASSWORD, "responsible_name": "Synthetic Name",
            "company": {"name": "Synthetic Company", "phone": "11999999999", "address_line": "Rua Exemplo 1",
                        "city": "Exemplo", "state": "SP", "postal_code": "00000-000"}}


def token(message):
    return parse_qs(urlsplit(message.link).fragment)["token"][0]


def test_registration_activation_login_and_single_use(environment):
    client = environment.client().prepare()
    payload = registration()
    assert client.request("POST", "/api/v1/auth/register", json=payload).status_code == 202
    assert client.request("POST", "/api/v1/auth/login", json={"email": payload["email"], "password": PASSWORD}).status_code == 401
    first = token(environment.mailer.messages[-1])
    with transaction(environment.app.state.engine) as db:
        user = db.scalar(select(User).where(User.email == payload["email"]))
        assert user.status == "pending" and user.role == "client" and not user.fixture
        assert user.password_hash.startswith("$argon2id$")
        stored = db.scalar(select(EmailToken).where(EmailToken.user_id == user.id))
        assert stored.token_hash == digest(first) and stored.token_hash != first
    assert client.request("POST", "/api/v1/auth/resend-activation", json={"email": payload["email"]}).status_code == 202
    second = token(environment.mailer.messages[-1])
    assert client.request("POST", "/api/v1/auth/activate", json={"token": first}).status_code == 400
    assert client.request("POST", "/api/v1/auth/activate", json={"token": second}).status_code == 200
    assert client.request("POST", "/api/v1/auth/activate", json={"token": second}).status_code == 400
    client.login(payload["email"])
    assert client.request("GET", "/api/v1/me").json()["role"] == "client"
    response = client.request("POST", "/api/v1/auth/register", json=payload)
    assert response.status_code == 202
    assert len(environment.mailer.messages) == 2


@pytest.mark.parametrize("changes", [
    {"password": "weak", "password_confirmation": "weak"},
    {"password_confirmation": "Different!12"},
    {"email_confirmation": "other@ecowatt.test"},
    {"role": "admin"}, {"owner_id": "someone"},
    {"company": {"name": "Missing required address"}},
])
def test_invalid_registration_and_no_sensitive_error_values(environment, changes):
    client = environment.client().prepare()
    payload = {**registration(), **changes}
    response = client.request("POST", "/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    assert "password" not in response.text or PASSWORD not in response.text
    assert set(response.json()) == {"code", "message", "fields", "request_id"}


def test_reset_revokes_all_sessions_and_neutral_unknown(environment):
    client = environment.client().login()
    other = environment.client().login()
    response = client.request("POST", "/api/v1/auth/forgot-password", json={"email": "cliente@ecowatt.test"})
    unknown = client.request("POST", "/api/v1/auth/forgot-password", json={"email": "nobody@ecowatt.test"})
    assert response.status_code == unknown.status_code == 202
    assert response.json() == unknown.json()
    reset = token(environment.mailer.messages[-1])
    new_password = "NewSecret!456"
    assert client.request("POST", "/api/v1/auth/reset-password", json={"token": reset,
        "password": new_password, "password_confirmation": new_password}).status_code == 200
    assert client.request("GET", "/api/v1/me").status_code == 401
    assert other.request("GET", "/account").status_code == 401
    fresh = environment.client().login(password=new_password)
    assert fresh.request("POST", "/api/v1/auth/reset-password", json={"token": reset,
        "password": new_password, "password_confirmation": new_password}).status_code == 400


def test_csrf_cookie_rotation_logout_and_admin_block(environment):
    client = environment.client().login()
    original_cookie = client.cookies.get("ecowatt_session")
    response = client.request("POST", "/api/v1/auth/login", json={"email": "cliente@ecowatt.test", "password": PASSWORD})
    assert response.status_code == 200
    client.csrf = response.json()["csrf_token"]
    assert client.cookies.get("ecowatt_session") != original_cookie
    assert "HttpOnly" in response.headers.get_list("set-cookie")[0]
    assert "SameSite=strict" in response.headers.get_list("set-cookie")[0]
    old = environment.client()
    old.cookies.set("ecowatt_session", original_cookie)
    assert old.request("GET", "/api/v1/me").status_code == 401
    assert client.request("POST", "/api/v1/auth/logout", headers={"X-CSRF-Token": "wrong"}).status_code == 403
    assert client.request("POST", "/api/v1/auth/logout", headers={"Origin": "https://evil.example"}).status_code == 403
    me = client.request("GET", "/api/v1/me").json()
    admin = environment.client().login("admin@ecowatt.test")
    assert admin.request("PATCH", f"/api/v1/admin/users/{me['id']}/status", json={"status": "blocked"}).status_code == 204
    assert client.request("GET", "/api/v1/me").status_code == 401
    assert admin.request("POST", "/api/v1/auth/logout").status_code == 204
    assert admin.request("GET", "/account").status_code == 401


@pytest.mark.parametrize("expiry", ["absolute", "idle"])
def test_expiration(environment, expiry):
    client = environment.client().login()
    with transaction(environment.app.state.engine, write=True) as db:
        session = db.scalar(select(AuthSession))
        if expiry == "absolute":
            session.expires_at = now() - 1
        else:
            session.last_seen_at = now() - environment.settings.session_idle_seconds - 1
    assert client.request("GET", "/api/v1/me").status_code == 401
    client.login()
    assert client.request("GET", "/api/v1/me").status_code == 200


def test_rate_limit_survives_failed_logins(environment):
    client = environment.client().prepare()
    for _ in range(10):
        response = client.request("POST", "/api/v1/auth/login", json={"email": "nobody@ecowatt.test", "password": "wrong"})
        assert response.status_code == 401
    assert client.request("POST", "/api/v1/auth/login", json={"email": "nobody@ecowatt.test", "password": "wrong"}).status_code == 429


def test_expired_activation_and_reset_does_not_activate_pending(environment):
    client = environment.client().prepare()
    assert client.request("POST", "/api/v1/auth/register", json=registration()).status_code == 202
    activation = token(environment.mailer.messages[-1])
    assert client.request("POST", "/api/v1/auth/forgot-password", json={"email": "new@ecowatt.test"}).status_code == 202
    assert len(environment.mailer.messages) == 1
    with transaction(environment.app.state.engine, write=True) as db:
        challenge = db.scalar(select(EmailToken))
        challenge.expires_at = now() - 1
    assert client.request("POST", "/api/v1/auth/activate", json={"token": activation}).status_code == 400


def test_revoke_sessions_and_secure_cookie(environment):
    client, other = environment.client().login(), environment.client().login()
    assert client.request("POST", "/api/v1/auth/revoke-sessions").status_code == 204
    assert other.request("GET", "/api/v1/me").status_code == 401
    secure_app = create_app(environment.settings.model_copy(update={"cookie_secure": True}))
    try:
        response = Client(secure_app).request("GET", "/api/v1/auth/csrf")
        assert "Secure" in response.headers["set-cookie"]
    finally:
        secure_app.state.engine.dispose()


def test_no_mail_provider_does_not_create_pending_account(environment):
    app = create_app(environment.settings)
    try:
        client = Client(app).prepare()
        assert client.request("POST", "/api/v1/auth/register", json=registration()).status_code == 503
        with transaction(app.state.engine) as db:
            assert db.scalar(select(User).where(User.email == "new@ecowatt.test")) is None
    finally:
        app.state.engine.dispose()
