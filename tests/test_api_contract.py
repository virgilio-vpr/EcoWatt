import pytest


def test_openapi_models_security_and_commands(environment):
    schema = environment.client().request("GET", "/api/v1/openapi.json").json()
    paths = schema["paths"]
    assert paths["/api/v1/me"]["get"]["security"] == [{"SessionCookie": []}]
    assert paths["/api/v1/simulations"]["post"]["security"] == [{"SessionCookie": [], "CSRFHeader": []}]
    assert paths["/api/v1/auth/login"]["post"]["security"] == [{"CSRFHeader": [], "CSRFCookie": []}]
    assert paths["/api/v1/health"]["get"]["security"] == []
    for path, operations in paths.items():
        for method, operation in operations.items():
            success = next(r for status, r in operation["responses"].items() if status.startswith("2"))
            if "204" not in operation["responses"]:
                assert success["content"]["application/json"]["schema"].get("$ref"), (path, method)
            assert "X-Request-ID" in success["headers"]
    command = paths["/api/v1/simulations"]["post"]
    assert {p["name"] for p in command["parameters"]} >= {"Origin", "Idempotency-Key"}
    assert "simulation_limit_reached" in command["description"]
    password = schema["components"]["schemas"]["Registration"]["properties"]["password"]
    assert password["minLength"] == 8 and password["maxLength"] == 128 and password["writeOnly"]
    assert schema["components"]["schemas"]["TokenInput"]["properties"]["token"]["writeOnly"]
    docs = environment.client().request("GET", "/api/v1/docs")
    assert "/api/v1/simulations" in docs.text and "/api/v1/auth/login" in docs.text


@pytest.mark.parametrize("query", ["?page=0", "?page_size=0", "?page_size=101"])
def test_pagination_bounds_and_error_id(environment, query):
    client = environment.client().login()
    response = client.request("GET", "/api/v1/simulations" + query)
    assert response.status_code == 422
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert set(response.json()) == {"code", "message", "fields", "request_id"}


def test_204_and_explicit_delete_confirmation(environment):
    client = environment.client().login()
    resource = client.request("POST", "/api/v1/simulations", json={}, headers={"Idempotency-Key": "contract-key"}).json()
    url = "/api/v1/simulations/" + resource["id"]
    assert client.request("DELETE", url, json={"confirm": "true", "expected_revision": 1}).status_code == 422
    response = client.request("DELETE", url, json={"confirm": True, "expected_revision": 1})
    assert response.status_code == 204 and response.content == b""
    assert client.request("GET", url).status_code == 404


def test_method_not_allowed_preserves_allow_header(environment):
    response = environment.client().request("POST", "/api/v1/health")
    assert response.status_code == 405
    assert "GET" in response.headers["Allow"]
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
