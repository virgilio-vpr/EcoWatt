from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from ecowatt.api.dependencies import authenticated
from ecowatt.db.models import Company, AuditEvent
from ecowatt.services.simulations import company_data, list_simulations, require_simulation, serialize

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


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
