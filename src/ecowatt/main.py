from contextlib import asynccontextmanager
from uuid import uuid4
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from ecowatt.api.health import router
from ecowatt.config import Settings
from ecowatt.db.session import make_engine
from ecowatt.errors import DomainError
from ecowatt.security.passwords import hasher
from ecowatt.security.tokens import new_token
from ecowatt.services.mail import make_mailer
from ecowatt.api.auth import router as auth_router
from ecowatt.api.resources import router as resources_router
from ecowatt.web.routes import router as web_router
from ecowatt.schemas import ErrorResponse
from ecowatt.api.openapi import install_openapi


def create_app(settings: Settings | None = None, *, mailer=None) -> FastAPI:
    """Construir a API sem criar banco, diretórios ou contas."""
    settings = settings if settings is not None else Settings()
    engine = make_engine(settings)

    @asynccontextmanager
    async def lifespan(app):
        yield
        engine.dispose()

    app = FastAPI(
        title="EcoWatt API",
        version="0.1.0",
        openapi_url="/api/v1/openapi.json",
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
        responses={code: {"model": ErrorResponse} for code in (400, 401, 403, 404, 409, 422, 429, 503)},
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.mailer = mailer if mailer is not None else make_mailer(settings)
    app.state.dummy_hash = hasher.hash(new_token())

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        request.state.request_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        return response

    def error(request, code, message, status, fields=None):
        return JSONResponse(status_code=status, content={"code": code, "message": message,
            "fields": fields or [], "request_id": request.state.request_id})

    @app.exception_handler(DomainError)
    async def domain_error(request, exc):
        return error(request, exc.code, exc.message, exc.status, exc.fields)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        fields = sorted({".".join(str(p) for p in e["loc"]) for e in exc.errors()})
        return error(request, "validation_error", "Confira os campos informados.", 422, fields)

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request, exc):
        return error(request, "database_unavailable", "Banco indisponível. Tente novamente.", 503)

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        response = error(request, "http_error", "Operação indisponível.", exc.status_code)
        if exc.headers:
            response.headers.update(exc.headers)
        return response

    app.include_router(router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(resources_router, prefix="/api/v1")
    app.include_router(web_router)
    app.mount("/static", StaticFiles(directory=Path(__file__).parent / "web" / "static"), name="static")
    install_openapi(app)
    return app
