from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from ecowatt.api.dependencies import authenticated
from ecowatt.db.models import Company, AuditEvent
from ecowatt.services.simulations import company_data, list_simulations, require_simulation, serialize

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@router.get("/auth/{page}")
def access_page(page: str, request: Request):
    pages = {
        "activation": ("Confirmar e-mail", "/api/v1/auth/activate"),
        "reset": ("Redefinir senha", "/api/v1/auth/reset-password"),
        "login": ("Entrar", "/api/v1/auth/login"),
        "register": ("Criar conta", "/api/v1/auth/register"),
        "forgot-password": ("Recuperar acesso", "/api/v1/auth/forgot-password"),
        "resend-activation": ("Reenviar confirmação", "/api/v1/auth/resend-activation"),
    }
    if page not in pages:
        from ecowatt.errors import DomainError
        raise DomainError("not_found", "Página não encontrada.", 404)
    title, endpoint = pages[page]
    return templates.TemplateResponse(request=request, name="auth/access.html", context={
        "page": page, "title": title, "endpoint": endpoint})


@router.get("/api/v1/docs")
def documentation(request: Request):
    operations = [{"path": route.path, "methods": sorted(route.methods)}
                  for route in request.app.routes if getattr(route, "include_in_schema", False)]
    return templates.TemplateResponse(request=request, name="docs.html", context={"operations": operations})


@router.get("/account")
def account(request: Request, principal=Depends(authenticated, scope="function")):
    db, actor, _ = principal
    return templates.TemplateResponse(request=request, name="account.html", context={
        "company": company_data(db.get(Company, actor.company_id)),
        "listing": list_simulations(db, actor, actor.id, 1, 20),
    })


@router.get("/simulations/{simulation_id}")
def simulation_page(simulation_id: UUID, request: Request, principal=Depends(authenticated, scope="function")):
    db, actor, _ = principal
    simulation = serialize(require_simulation(db, actor, simulation_id))
    if actor.role == "admin":
        db.add(AuditEvent(actor_id=actor.id, action="simulation_viewed", resource_id=simulation["id"]))
    return templates.TemplateResponse(request=request, name="simulation.html", context={"simulation": simulation})


@router.get("/account/simulations")
def simulations_fragment(request: Request, principal=Depends(authenticated, scope="function")):
    db, actor, _ = principal
    return templates.TemplateResponse(request=request, name="partials/simulations.html", context={
        "listing": list_simulations(db, actor, actor.id, 1, 20)})
