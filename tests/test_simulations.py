from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import select

from ecowatt.db.models import Simulation, User
from ecowatt.db.session import transaction
from ecowatt.errors import DomainError
from ecowatt.services.simulations import require_simulation


def create(client, key="synthetic-0001", path="/api/v1/simulations"):
    return client.request("POST", path, json={}, headers={"Idempotency-Key": key})


def test_quota_retry_deletion_revision_and_late_writer(environment):
    client = environment.client().login()
    first = create(client).json()
    assert create(client).json()["id"] == first["id"]
    assert create(client, "synthetic-0002").status_code == 201
    assert create(client, "synthetic-0003").json()["code"] == "simulation_limit_reached"
    assert client.request("DELETE", f"/api/v1/simulations/{first['id']}", json={"confirm": False, "expected_revision": 1}).status_code == 422
    assert client.request("DELETE", f"/api/v1/simulations/{first['id']}", json={"confirm": True, "expected_revision": 2}).status_code == 409
    assert client.request("DELETE", f"/api/v1/simulations/{first['id']}", json={"confirm": True, "expected_revision": 1}).status_code == 204
    assert client.request("GET", f"/api/v1/simulations/{first['id']}").status_code == 404
    assert create(client).status_code == 404  # retry não recria excluída
    assert create(client, "synthetic-0003").status_code == 201
    with transaction(environment.app.state.engine, write=True) as db:
        user = db.scalar(select(User).where(User.role == "client"))
        try:
            require_simulation(db, user, first["id"], 1)
        except DomainError as exc:
            assert exc.code == "not_found"
        else:
            raise AssertionError("Resultado tardio aceito")
    listing = client.request("GET", "/api/v1/simulations?page_size=1").json()
    assert listing["total"] == 2 and len(listing["items"]) == 1


def test_parallel_creations_and_same_key_retry(environment):
    primary = environment.client().login()
    secondary = environment.client().login()
    create(primary)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda pair: create(*pair), [(primary, "parallel-0001"), (secondary, "parallel-0002")]))
    assert sorted(r.status_code for r in results) == [201, 409]
    with transaction(environment.app.state.engine) as db:
        assert len(list(db.scalars(select(Simulation).where(Simulation.status != "deleted")))) == 2


def test_parallel_same_idempotency_key_is_one_creation(environment):
    first, second = environment.client().login(), environment.client().login()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda client: create(client, "same-parallel-key"), [first, second]))
    assert [r.status_code for r in results] == [201, 201]
    assert results[0].json()["id"] == results[1].json()["id"]
    assert first.request("GET", "/api/v1/simulations").json()["total"] == 1


def test_owner_admin_isolation_and_injection(environment):
    client = environment.client().login()
    admin = environment.client().login("admin@ecowatt.test")
    client_id = client.request("GET", "/api/v1/me").json()["id"]
    mine = create(client).json()
    admin_sim = create(admin).json()
    assert client.request("GET", f"/api/v1/simulations/{admin_sim['id']}").status_code == 404
    assert client.request("GET", f"/simulations/{admin_sim['id']}", headers={"HX-Request": "true"}).status_code == 404
    assert client.request("POST", "/api/v1/simulations", json={"owner_id": admin_sim["owner_id"]}, headers={"Idempotency-Key": "bad-owner"}).status_code == 422
    assert client.request("GET", f"/api/v1/admin/users/{client_id}/simulations").status_code == 403
    for_client = create(admin, "admin-client", f"/api/v1/admin/users/{client_id}/simulations").json()
    assert for_client["owner_id"] == client_id and for_client["created_by"] == admin_sim["owner_id"]
    assert for_client["company_id"] == mine["company_id"]
    assert create(admin, "admin-third", f"/api/v1/admin/users/{client_id}/simulations").status_code == 409
    assert create(admin, "admin-second").status_code == 201
    assert create(admin, "admin-third-own").status_code == 409
    assert create(admin, "admin-client").json()["code"] == "idempotency_conflict"
    assert client.request("GET", "/account").status_code == 200
    fragment = client.request("GET", "/account/simulations", headers={"HX-Request": "true"})
    assert fragment.status_code == 200 and "2 de 2" in fragment.text
    assert environment.client().request("GET", "/account/simulations", headers={"HX-Request": "true"}).status_code == 401
    asset = client.request("GET", "/static/vendor/htmx-2.0.11.min.js")
    assert asset.status_code == 200


def test_save_unit_snapshot_catalog_and_escaping(environment):
    client = environment.client().login()
    simulation = create(client).json()
    assert simulation["unit_saved"] is False
    distributor = client.request("GET", "/api/v1/distributors").json()["items"][0]
    payload = {"expected_revision": 1, "distributor_id": distributor["id"], "unit_identifier": "UC-SYNTHETIC",
               "holder_name": "<script>alert(1)</script>", "address_line": "Rua da Cabine, 2",
               "city": "Exemplo", "state": "SP", "postal_code": "00000-000"}
    saved = client.request("PATCH", f"/api/v1/simulations/{simulation['id']}/unit", json=payload)
    assert saved.status_code == 200, saved.text
    assert saved.json()["unit_saved"] is True and saved.json()["revision"] == 2
    assert client.request("PATCH", f"/api/v1/simulations/{simulation['id']}/unit", json=payload).status_code == 409
    changed = {**payload, "expected_revision": 2, "unit_identifier": "OTHER-UC"}
    assert client.request("PATCH", f"/api/v1/simulations/{simulation['id']}/unit", json=changed).status_code == 409
    company = client.request("GET", "/api/v1/me/company").json()
    assert company["address_line"] != payload["address_line"]
    page = client.request("GET", f"/simulations/{simulation['id']}")
    assert "<script>" not in page.text and "&lt;script&gt;" in page.text
    assert "frame-ancestors 'none'" in page.headers["Content-Security-Policy"]
    assert client.request("GET", "/api/v1/ready").status_code == 200
