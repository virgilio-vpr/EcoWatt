from fastapi import FastAPI

from ecowatt.api.health import router
from ecowatt.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Construir a API sem criar banco, diretórios ou contas."""
    settings = settings if settings is not None else Settings()
    app = FastAPI(
        title="EcoWatt API",
        version="0.1.0",
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url=None,
    )
    app.state.settings = settings
    app.include_router(router, prefix="/api/v1")
    return app
