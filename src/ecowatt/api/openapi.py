"""Documentar o contrato JSON sem alterar autorização em runtime."""
from fastapi.openapi.utils import get_openapi
from ecowatt.api.dependencies import SESSION_COOKIE, CSRF_COOKIE

PUBLIC_GET = {"/api/v1/health", "/api/v1/ready", "/api/v1/auth/csrf"}
PUBLIC_COMMANDS = {"/api/v1/auth/" + name for name in (
    "register", "login", "activate", "resend-activation", "forgot-password", "reset-password")}


def install_openapi(app):
    def schema():
        if app.openapi_schema:
            return app.openapi_schema
        result = get_openapi(title=app.title, version=app.version, routes=app.routes,
            description="API local EcoWatt. Decimais financeiros são strings, nunca floats. "
                "Sessão opaca em cookie HttpOnly; obter CSRF antes de comandos. "
                "Listas usam page/page_size (1–100). Simulações: duas não excluídas por dono. "
                "SMTP disabled por padrão; 202 aceita o pedido, sem comprovar entrega.")
        result["components"]["securitySchemes"] = {
            "SessionCookie": {"type": "apiKey", "in": "cookie", "name": SESSION_COOKIE},
            "CSRFCookie": {"type": "apiKey", "in": "cookie", "name": CSRF_COOKIE},
            "CSRFHeader": {"type": "apiKey", "in": "header", "name": "X-CSRF-Token"},
        }
        for path, operations in result["paths"].items():
            for method, operation in operations.items():
                if method not in {"get", "post", "patch", "delete", "put", "head", "options"}:
                    continue
                private = path not in PUBLIC_GET and path not in PUBLIC_COMMANDS
                unsafe = method not in {"get", "head", "options"}
                security = {"SessionCookie": []} if private else {}
                if unsafe:
                    security["CSRFHeader"] = []
                    if not private:
                        security["CSRFCookie"] = []
                    operation.setdefault("parameters", []).append({"in": "header", "name": "Origin",
                        "required": True, "schema": {"type": "string"},
                        "description": "Origem exata configurada em PUBLIC_ORIGIN; navegador envia automaticamente."})
                operation["security"] = [security] if security else []
                if path.startswith("/api/v1/admin/"):
                    operation["description"] = "Exige administrador; não dispensa autorização por titular nem cota."
                if method == "post" and path.endswith("/simulations"):
                    operation["description"] = (
                        "Exige Idempotency-Key (8–128). Mesma chave e dono retorna o recurso existente, "
                        "com 201. Trocar dono: 409 idempotency_conflict. Retry após exclusão: 404. "
                        "Máximo duas não excluídas por dono, inclusive admin: 409 simulation_limit_reached."
                    ) + (" Exige administrador." if "/admin/" in path else "")
                if method in {"patch", "delete"} and "/simulations/" in path:
                    operation["description"] = (
                        "expected_revision deve coincidir; conflito: 409 simulation_revision_conflict. "
                        "Outra UC/distribuidora exige nova simulação: 409 unit_identity_conflict. "
                        "DELETE exige confirm=true e retorna 204 sem corpo; recurso excluído retorna 404."
                    )
                for response in operation["responses"].values():
                    response.setdefault("headers", {})["X-Request-ID"] = {
                        "schema": {"type": "string", "format": "uuid"},
                        "description": "Identificador técnico, sem dados pessoais ou tokens."}
        app.openapi_schema = result
        return result
    app.openapi = schema
