"use strict";
(() => {
  class APIError extends Error {
    constructor(message, code, status, fields = [], requestId = null) {
      super(message);
      this.name = "APIError";
      Object.assign(this, {code, status, fields, requestId});
    }
  }
  async function request(path, {method = "GET", data, idempotencyKey, timeoutMs = 10000} = {}) {
    // Não enviar cookies/CSRF para URLs externas nem seguir redirects inesperados.
    if (typeof path !== "string" || !/^\/api\/v1\/[^#\\]*$/.test(path) ||
        !new URL(path, window.location.origin).pathname.startsWith("/api/v1/")) {
      throw new APIError("Caminho de API inválido.", "invalid_api_path", 0);
    }
    const verb = method.toUpperCase();
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    const headers = {"Accept": "application/json"};
    try {
      if (!["GET", "HEAD", "OPTIONS"].includes(verb)) {
        const csrfResponse = await fetch("/api/v1/auth/csrf", {
          credentials: "same-origin", cache: "no-store", redirect: "error", signal: controller.signal
        });
        if (!csrfResponse.ok) throw new APIError("Não foi possível preparar o acesso.", "csrf_unavailable", csrfResponse.status);
        headers["X-CSRF-Token"] = (await csrfResponse.json()).csrf_token;
      }
      if (data !== undefined) headers["Content-Type"] = "application/json";
      if (idempotencyKey) headers["Idempotency-Key"] = idempotencyKey;
      const response = await fetch(path, {
        method: verb, headers, credentials: "same-origin", cache: "no-store", redirect: "error",
        signal: controller.signal, ...(data !== undefined ? {body: JSON.stringify(data)} : {})
      });
      if (response.status === 204) return null;
      const result = await response.json();
      if (!response.ok) {
        throw new APIError(result.message || "Não foi possível concluir.", result.code || "http_error",
          response.status, result.fields || [], result.request_id || response.headers.get("X-Request-ID"));
      }
      return result;
    } catch (error) {
      if (error instanceof APIError) throw error;
      throw new APIError("Não foi possível concluir. Verifique a conexão e o resultado antes de tentar novamente.",
        error.name === "AbortError" ? "request_timeout" : "network_error", 0);
    } finally {
      clearTimeout(timer);
    }
  }
  // Nenhum retry automático: timeout não comprova que uma escrita falhou.
  window.EcoWattHTTP = Object.freeze({request, APIError});
})();
