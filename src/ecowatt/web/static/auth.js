"use strict";
(() => {
  const form = document.getElementById("auth-form");
  if (!form) return;
  const page = form.dataset.page;
  const requiresToken = page === "activation" || page === "reset";
  let linkToken = "";
  const status = document.getElementById("auth-status");
  const submit = document.getElementById("auth-submit");
  const password = form.elements.namedItem("password");
  const confirmation = form.elements.namedItem("password_confirmation");
  const email = form.elements.namedItem("email");
  const emailConfirmation = form.elements.namedItem("email_confirmation");
  let validLink = !requiresToken;
  function readLink() {
    if (requiresToken) {
      linkToken = new URLSearchParams(window.location.hash.slice(1)).get("token") || "";
      window.history.replaceState(null, "", window.location.pathname);
      validLink = /^[A-Za-z0-9_-]{32,128}$/.test(linkToken);
      status.textContent = validLink ? "Confirme o formulário para continuar." : "Link inválido. Solicite um novo link.";
    }
    submit.disabled = !validLink;
  }
  readLink();
  window.addEventListener("hashchange", readLink);

  function validate() {
    if (password && confirmation) {
      const chars = Array.from(password.value);
      const valid = chars.length >= 8 && chars.length <= 128 &&
        /\p{Lu}/u.test(password.value) && /\p{Ll}/u.test(password.value) &&
        (password.value.match(/\p{Nd}/gu) || []).length >= 2 &&
        /[^\p{L}\p{N}\s]/u.test(password.value);
      password.setCustomValidity(valid ? "" : "Confira a política de senha exibida.");
      confirmation.setCustomValidity(password.value === confirmation.value ? "" : "As senhas devem coincidir.");
    }
    if (emailConfirmation) {
      emailConfirmation.setCustomValidity(email.value.trim().toLowerCase() === emailConfirmation.value.trim().toLowerCase()
        ? "" : "Os e-mails devem coincidir.");
    }
  }
  form.addEventListener("input", validate);
  const show = document.getElementById("show-password");
  if (show) show.addEventListener("click", () => {
    const visible = password.type === "password";
    password.type = visible ? "text" : "password";
    if (confirmation) confirmation.type = password.type;
    show.textContent = visible ? "Ocultar senha" : "Mostrar senha";
    show.setAttribute("aria-pressed", String(visible));
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    validate();
    if (!validLink || !form.reportValidity()) return;
    submit.disabled = true;
    status.textContent = "Aguarde…";
    let completed = false;
    const payload = {};
    for (const [name, value] of new FormData(form)) {
      if (name.startsWith("company.")) {
        payload.company ||= {};
        payload.company[name.slice(8)] = value;
      } else payload[name] = value;
    }
    if (requiresToken) payload.token = linkToken;
    try {
      const csrfResponse = await fetch("/api/v1/auth/csrf", {credentials: "same-origin", cache: "no-store"});
      if (!csrfResponse.ok) throw new Error("request_failed");
      const csrf = await csrfResponse.json();
      const response = await fetch(form.dataset.endpoint, {
        method: "POST", credentials: "same-origin", cache: "no-store",
        headers: {"Content-Type": "application/json", "X-CSRF-Token": csrf.csrf_token},
        body: JSON.stringify(payload)
      });
      const result = await response.json();
      status.textContent = result.message || "Não foi possível concluir. Tente novamente.";
      if (response.ok) {
        completed = true;
        linkToken = "";
        form.reset();
        if (page === "login") window.location.assign("/account");
      }
    } catch {
      status.textContent = "Não foi possível concluir. Verifique a conexão e tente novamente.";
    } finally {
      // Não conservar senhas no objeto do envio ou na interface após a tentativa.
      if (password) password.value = "";
      if (confirmation) confirmation.value = "";
      delete payload.password;
      delete payload.password_confirmation;
      delete payload.token;
      submit.disabled = !validLink || (requiresToken && completed);
    }
  });
})();
