from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import func, select

from ecowatt.api.dependencies import authenticated
from ecowatt.db.models import AuditEvent, Company, Distributor
from ecowatt.schemas import CompanyInput, DeleteInput, ProfileInput, SimulationCreate, UnitInput
from ecowatt.schemas import CompanyOutput, MeOutput, SimulationOutput, SimulationsPage
from ecowatt.schemas import ProfileOutput, DistributorsPage
from ecowatt.schemas import InvoiceAdmissionContext
from ecowatt.schemas import InvoiceDeleteInput, StructuredInvoiceOutput, InvoicesPage
from ecowatt.services import simulations as service
from ecowatt.invoice_review import ReviewInput
from ecowatt.schemas import ReviewReceipt, DatasetReadiness
from ecowatt.invoice_confirmation import ConfirmationInput, SelectionInput
from ecowatt.schemas import ConfirmationReceipt, SelectionReceipt, SelectionsPage

router = APIRouter(tags=["resources"])
Key = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)]
Page = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


@router.get("/simulations/{simulation_id}/invoice-selections", response_model=SelectionsPage)
def invoice_selections(simulation_id: UUID, page: Page = 1, page_size: PageSize = 20,
        principal=Depends(authenticated, scope="function")):
    from ecowatt.services.invoice_confirmation import list_selections
    db, actor, _ = principal
    return list_selections(db, actor, str(simulation_id), page, page_size)


@router.post("/simulations/{simulation_id}/invoices/{invoice_id}/confirmations", response_model=ConfirmationReceipt)
def invoice_confirm(simulation_id: UUID, invoice_id: UUID, payload: ConfirmationInput, idempotency_key: Key,
        principal=Depends(authenticated, scope="function")):
    from ecowatt.services.invoice_confirmation import confirm_invoice
    db, actor, _ = principal
    return confirm_invoice(db, actor, str(simulation_id), str(invoice_id), idempotency_key, payload)


@router.post("/simulations/{simulation_id}/invoice-selections", response_model=SelectionReceipt)
def invoice_select(simulation_id: UUID, payload: SelectionInput, idempotency_key: Key,
        principal=Depends(authenticated, scope="function")):
    from ecowatt.services.invoice_confirmation import select_invoices
    db, actor, _ = principal
    return select_invoices(db, actor, str(simulation_id), idempotency_key, payload)


@router.get("/simulations/{simulation_id}/invoice-readiness", response_model=DatasetReadiness)
def invoice_readiness(simulation_id: UUID, principal=Depends(authenticated, scope="function")):
    from ecowatt.services.invoice_validation import dataset_readiness
    db, actor, _ = principal
    return dataset_readiness(db, actor, str(simulation_id))


@router.post("/simulations/{simulation_id}/invoices/{invoice_id}/reviews", response_model=ReviewReceipt)
def invoice_review(simulation_id: UUID, invoice_id: UUID, payload: ReviewInput, idempotency_key: Key,
        principal=Depends(authenticated, scope="function")):
    from ecowatt.services.invoice_review import review_invoice
    db, actor, _ = principal
    return review_invoice(db, actor, str(simulation_id), str(invoice_id), idempotency_key, payload)


@router.get("/simulations/{simulation_id}/invoices", response_model=InvoicesPage)
def invoice_listing(simulation_id: UUID, page: Page = 1, page_size: PageSize = 20,
        principal=Depends(authenticated, scope="function")):
    from ecowatt.services.invoices import list_invoices
    db, actor, _ = principal
    return list_invoices(db, actor, str(simulation_id), page, page_size)


@router.get("/simulations/{simulation_id}/invoices/{invoice_id}", response_model=StructuredInvoiceOutput)
def invoice_detail(simulation_id: UUID, invoice_id: UUID, principal=Depends(authenticated, scope="function")):
    from ecowatt.services.invoices import require_invoice, serialize_invoice
    db, actor, _ = principal
    return serialize_invoice(db, require_invoice(db, actor, str(simulation_id), str(invoice_id)))


@router.delete("/simulations/{simulation_id}/invoices/{invoice_id}", status_code=204)
def invoice_remove(simulation_id: UUID, invoice_id: UUID, payload: InvoiceDeleteInput,
        principal=Depends(authenticated, scope="function")):
    from ecowatt.services.invoices import remove_invoice
    db, actor, _ = principal
    remove_invoice(db, actor, str(simulation_id), str(invoice_id), payload)


@router.get("/simulations/{simulation_id}/invoice-admission", response_model=InvoiceAdmissionContext)
def invoice_admission_context(simulation_id: UUID,
        layout_version: Annotated[str, Query(min_length=1, max_length=80)] = "unknown",
        principal=Depends(authenticated, scope="function")):
    """Consulta suporte; não recebe arquivos nem inicia leitura. PDFs desabilitados."""
    from ecowatt.services.admission import support
    db, actor, _ = principal
    simulation = service.require_simulation(db, actor, simulation_id)
    distributor = db.get(Distributor, simulation.distributor_id) if simulation.distributor_id else None
    capability = support(distributor.code if distributor else None, layout_version)
    if simulation.unit_saved_at is None:
        capability.update(supported=False, reason="unit_not_saved")
    return {"unit_saved": simulation.unit_saved_at is not None,
            "distributor_id": simulation.distributor_id,
            "distributor_code": distributor.code if distributor else None,
            "layout_version": layout_version, **capability}


@router.get("/me", response_model=MeOutput)
def me(principal=Depends(authenticated, scope="function")):
    _, actor, _ = principal
    return {"id": actor.id, "email": actor.email, "responsible_name": actor.responsible_name,
            "role": actor.role, "company_id": actor.company_id}


@router.get("/me/company", response_model=CompanyOutput)
def company(principal=Depends(authenticated, scope="function")):
    db, actor, _ = principal
    return service.company_data(db.get(Company, actor.company_id))


@router.patch("/me", response_model=ProfileOutput)
def profile(payload: ProfileInput, principal=Depends(authenticated, scope="function")):
    db, actor, _ = principal
    before = actor.responsible_name
    actor.responsible_name = payload.responsible_name
    db.add(AuditEvent(actor_id=actor.id, action="profile_updated", resource_id=actor.id,
                      changes={"before": before, "after": actor.responsible_name}))
    return {"id": actor.id, "responsible_name": actor.responsible_name}


@router.patch("/me/company", response_model=CompanyOutput)
def update_company(payload: CompanyInput, principal=Depends(authenticated, scope="function")):
    db, actor, _ = principal
    company = db.get(Company, actor.company_id)
    before = service.company_data(company)
    for name, value in payload.model_dump().items():
        setattr(company, name, value)
    db.add(AuditEvent(actor_id=actor.id, action="company_updated", resource_id=company.id,
                      changes={"before": before, "after": service.company_data(company)}))
    return service.company_data(company)


@router.get("/distributors", response_model=DistributorsPage)
def distributors(page: Page = 1, page_size: PageSize = 20, principal=Depends(authenticated, scope="function")):
    db, _, _ = principal
    return {"items": [{"id": d.id, "code": d.code, "name": d.name}
                       for d in db.scalars(select(Distributor).order_by(Distributor.code)
                           .offset((page - 1) * page_size).limit(page_size))],
            "total": db.scalar(select(func.count()).select_from(Distributor)),
            "page": page, "page_size": page_size}


@router.post("/simulations", status_code=201, response_model=SimulationOutput)
def create(payload: SimulationCreate, idempotency_key: Key, principal=Depends(authenticated, scope="function")):
    db, actor, _ = principal
    return service.serialize(service.create_simulation(db, actor, actor.id, idempotency_key))


@router.post("/admin/users/{owner_id}/simulations", status_code=201, response_model=SimulationOutput)
def create_for(owner_id: UUID, payload: SimulationCreate, idempotency_key: Key,
               principal=Depends(authenticated, scope="function")):
    db, actor, _ = principal
    service.require_admin(actor)
    return service.serialize(service.create_simulation(db, actor, str(owner_id), idempotency_key))


@router.get("/simulations", response_model=SimulationsPage)
def listing(page: Page = 1, page_size: PageSize = 20, principal=Depends(authenticated, scope="function")):
    db, actor, _ = principal
    return service.list_simulations(db, actor, actor.id, page, page_size)


@router.get("/admin/users/{owner_id}/simulations", response_model=SimulationsPage)
def list_for(owner_id: UUID, page: Page = 1, page_size: PageSize = 20, principal=Depends(authenticated, scope="function")):
    db, actor, _ = principal
    service.require_admin(actor)
    return service.list_simulations(db, actor, str(owner_id), page, page_size)


@router.get("/simulations/{simulation_id}", response_model=SimulationOutput)
def detail(simulation_id: UUID, principal=Depends(authenticated, scope="function")):
    db, actor, _ = principal
    simulation = service.require_simulation(db, actor, simulation_id)
    if actor.role == "admin":
        db.add(AuditEvent(actor_id=actor.id, action="simulation_viewed", resource_id=simulation.id))
    return service.serialize(simulation)


@router.patch("/simulations/{simulation_id}/unit", response_model=SimulationOutput)
def unit(simulation_id: UUID, payload: UnitInput, principal=Depends(authenticated, scope="function")):
    db, actor, _ = principal
    return service.serialize(service.save_unit(db, actor, simulation_id, payload))


@router.delete("/simulations/{simulation_id}", status_code=204)
def remove(simulation_id: UUID, payload: DeleteInput, principal=Depends(authenticated, scope="function")):
    db, actor, _ = principal
    service.delete_simulation(db, actor, simulation_id, payload)
