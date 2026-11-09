from typing import Literal

from pathlib import Path

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy.engine import make_url
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ecowatt.errors import DomainError

router = APIRouter(tags=["operation"])


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness do processo; não verifica banco ou migrações."""
    return HealthResponse()


@router.get("/ready", response_model=HealthResponse)
def ready(request: Request) -> HealthResponse:
    database = make_url(request.app.state.settings.database_url.get_secret_value()).database
    if not database or database == ":memory:" or not Path(database).is_file():
        raise DomainError("not_ready", "Serviço ainda não disponível.", 503)
    try:
        with request.app.state.engine.connect() as conn:
            revision = conn.scalar(text("SELECT version_num FROM alembic_version"))
            if revision != "0004_invoices":
                raise DomainError("not_ready", "Serviço ainda não disponível.", 503)
    except SQLAlchemyError:
        raise DomainError("not_ready", "Serviço ainda não disponível.", 503) from None
    return HealthResponse()
