"""Primitiva ASGI interna sem spool, ainda sem rota/multipart/proxy homologado.

Usar antes de qualquer Request.form/body/parser. Teto inclui todo o corpo,
inclusive envelope multipart futuro. Não inspeciona PDF nem autoriza admissão.
"""
from contextlib import asynccontextmanager

MAX_BODY_BYTES = 10_000_000


class IngressError(ValueError):
    pass


@asynccontextmanager
async def memory_body(scope, receive, *, limit=MAX_BODY_BYTES):
    if type(limit) is not int or not 0 < limit <= MAX_BODY_BYTES:
        raise ValueError("invalid_ingress_limit")
    if scope.get("type") != "http":
        raise IngressError("invalid_ingress_scope")
    headers = scope.get("headers", [])
    sizes = [value for name, value in headers if name.lower() == b"content-length"]
    if len(sizes) > 1 or any(name.lower() == b"content-encoding" for name, _ in headers):
        raise IngressError("invalid_ingress_headers")
    declared = None
    if sizes:
        value = sizes[0]
        if not value or len(value) > 8 or not value.isdigit():
            raise IngressError("invalid_content_length")
        declared = int(value)
        if not 0 < declared <= limit:
            raise IngressError("ingress_size")
    content = bytearray()
    try:
        while True:
            message = await receive()
            if message.get("type") == "http.disconnect":
                raise IngressError("ingress_disconnected")
            if message.get("type") != "http.request":
                raise IngressError("invalid_ingress_message")
            chunk = message.get("body", b"")
            if type(chunk) is not bytes:
                raise IngressError("invalid_ingress_chunk")
            if len(chunk) > limit - len(content):
                raise IngressError("ingress_size")
            content.extend(chunk)
            if not message.get("more_body", False):
                break
        if not content or declared is not None and len(content) != declared:
            raise IngressError("ingress_length_mismatch")
        yield content
    finally:
        content[:] = b"\0" * len(content)
        content.clear()
