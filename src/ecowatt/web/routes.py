from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from ecowatt.api.dependencies import authenticated
from ecowatt.db.models import Company, AuditEvent
from ecowatt.services.invoices import list_invoices, require_invoice, scalar, serialize_invoice
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
    # O schema resolve routers incluídos mesmo quando não são APIRoute planos.
    operations = [{"path": path, "methods": sorted(method.upper() for method in methods)}
                  for path, methods in request.app.openapi()["paths"].items()]
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


@router.get("/simulations/{simulation_id}/invoices")
def invoice_listing_page(simulation_id: UUID, request: Request, principal=Depends(authenticated, scope="function")):
    from ecowatt.services.invoice_validation import dataset_readiness
    db, actor, _ = principal
    simulation = serialize(require_simulation(db, actor, simulation_id))
    readiness = dataset_readiness(db, actor, str(simulation_id))
    listing = list_invoices(db, actor, str(simulation_id), 1, 20)
    return templates.TemplateResponse(request=request, name="invoices.html", context={
        "simulation": simulation, "listing": listing, "readiness": readiness})


@router.get("/simulations/{simulation_id}/invoices/{invoice_id}")
def invoice_detail_page(simulation_id: UUID, invoice_id: UUID, request: Request,
        principal=Depends(authenticated, scope="function")):
    from ecowatt.services.invoice_validation import dataset_readiness
    from ecowatt.services.invoice_review import current_fields, targets
    from ecowatt.services.invoice_confirmation import list_selections
    db, actor, _ = principal
    simulation = serialize(require_simulation(db, actor, simulation_id))
    invoice_row = require_invoice(db, actor, str(simulation_id), str(invoice_id))
    invoice = serialize_invoice(db, invoice_row)
    readiness = dataset_readiness(db, actor, str(simulation_id))
    entry = next((item for item in readiness["invoices"] if item["invoice_id"] == str(invoice_id)), None)
    group = next((group for group in readiness["duplicate_groups"] if str(invoice_id) in group["member_versions"]), None)
    latest, mapped = current_fields(db, str(invoice_id)), targets(db, invoice_row)
    editable_fields = []
    for path, provenance in sorted(latest.items()):
        if path not in mapped:
            continue
        target, name, spec = mapped[path]
        history = next(item for item in invoice["provenance"] if item["id"] == provenance.id)
        editable_fields.append({"path": path, "version": provenance.version, "kind": spec.kind,
            "value": scalar(getattr(target, name)), "unit": provenance.unit, "state": provenance.state,
            "origin": provenance.origin, "coverage": provenance.coverage, "reason_code": provenance.reason_code,
            "hypothesis_code": provenance.hypothesis_code, "rule_version": provenance.rule_version,
            "inputs": history["inputs"]})
    group_invoices = {item["id"]: item for item in list_invoices(db, actor, str(simulation_id), 1, 100)["items"]}
    selections = list_selections(db, actor, str(simulation_id), 1, 20)
    return templates.TemplateResponse(request=request, name="invoice_detail.html", context={
        "simulation": simulation, "detail": invoice, "entry": entry, "duplicate_group": group,
        "readiness": readiness, "editable_fields": editable_fields, "group_invoices": group_invoices,
        "selection_history": selections})


@router.get("/simulations/{simulation_id}/invoices/{invoice_id}/fragment")
def invoice_detail_fragment(simulation_id: UUID, invoice_id: UUID, request: Request,
        principal=Depends(authenticated, scope="function")):
    from ecowatt.services.invoice_validation import dataset_readiness
    from ecowatt.services.invoice_review import current_fields, targets
    from ecowatt.services.invoice_confirmation import list_selections
    db, actor, _ = principal
    simulation = serialize(require_simulation(db, actor, simulation_id))
    invoice_row = require_invoice(db, actor, str(simulation_id), str(invoice_id))
    invoice = serialize_invoice(db, invoice_row)
    readiness = dataset_readiness(db, actor, str(simulation_id))
    entry = next((item for item in readiness["invoices"] if item["invoice_id"] == str(invoice_id)), None)
    group = next((group for group in readiness["duplicate_groups"] if str(invoice_id) in group["member_versions"]), None)
    latest, mapped = current_fields(db, str(invoice_id)), targets(db, invoice_row)
    editable_fields = []
    for path, provenance in sorted(latest.items()):
        if path not in mapped:
            continue
        target, name, spec = mapped[path]
        history = next(item for item in invoice["provenance"] if item["id"] == provenance.id)
        editable_fields.append({"path": path, "version": provenance.version, "kind": spec.kind,
            "value": scalar(getattr(target, name)), "unit": provenance.unit, "state": provenance.state,
            "origin": provenance.origin, "coverage": provenance.coverage, "reason_code": provenance.reason_code,
            "hypothesis_code": provenance.hypothesis_code, "rule_version": provenance.rule_version,
            "inputs": history["inputs"]})
    group_invoices = {item["id"]: item for item in list_invoices(db, actor, str(simulation_id), 1, 100)["items"]}
    selections = list_selections(db, actor, str(simulation_id), 1, 20)
    return templates.TemplateResponse(request=request, name="invoice_detail_fragment.html", context={
        "simulation": simulation, "detail": invoice, "entry": entry, "duplicate_group": group,
        "readiness": readiness, "editable_fields": editable_fields, "group_invoices": group_invoices,
        "selection_history": selections})


@router.get("/account/simulations")
def simulations_fragment(request: Request, principal=Depends(authenticated, scope="function")):
    db, actor, _ = principal
    return templates.TemplateResponse(request=request, name="partials/simulations.html", context={
        "listing": list_simulations(db, actor, actor.id, 1, 20)})
