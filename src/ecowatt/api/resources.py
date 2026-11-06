from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import func, select

from ecowatt.api.dependencies import authenticated
from ecowatt.db.models import AuditEvent, Company, Distributor
from ecowatt.schemas import CompanyInput, DeleteInput, ProfileInput, SimulationCreate, UnitInput
from ecowatt.schemas import CompanyOutput, MeOutput, SimulationOutput, SimulationsPage
from ecowatt.services import simulations as service

router = APIRouter(tags=["resources"])
Key = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)]
Page = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


@router.get("/me", response_model=MeOutput)
def me(principal=Depends(authenticated, scope="function")):
    _, actor, _ = principal
    return {"id": actor.id, "email": actor.email, "responsible_name": actor.responsible_name,
            "role": actor.role, "company_id": actor.company_id}


@router.get("/me/company", response_model=CompanyOutput)
def company(principal=Depends(authenticated, scope="function")):
    db, actor, _ = principal
    return service.company_data(db.get(Company, actor.company_id))


@router.patch("/me")
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


@router.get("/distributors")
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
