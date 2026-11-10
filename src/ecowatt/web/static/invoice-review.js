"use strict";
(() => {
  function basePayload(form) {
    return {
      expected_revision: Number(form.elements.expected_revision.value),
      expected_dataset_revision: Number(form.elements.expected_dataset_revision.value),
      reason_code: form.elements.reason_code.value.trim(),
    };
  }

  function editValue(fieldset) {
    const raw = fieldset.querySelector("[data-field-value]").value;
    const kind = fieldset.dataset.kind;
    const state = fieldset.querySelector("[data-field-state]").value;
    let value = raw === "" ? null : raw;
    if (["missing", "unreadable", "not_applicable"].includes(state)) value = null;
    else if (raw !== "" && kind === "integer") value = Number(raw);
    else if (raw !== "" && kind === "boolean") value = raw === "true";
    const inputs = fieldset.querySelector("[data-field-inputs]").value
      .split(",").map((item) => item.trim()).filter(Boolean);
    const text = (selector) => fieldset.querySelector(selector).value.trim() || null;
    return {
      path: fieldset.querySelector("[data-field-path]").value,
      expected_version: Number(fieldset.querySelector("[data-field-version]").value),
      field: {
        value,
        state,
        unit: text("[data-field-unit]"),
        origin: fieldset.querySelector("[data-field-origin]").value,
        coverage: fieldset.querySelector("[data-field-coverage]").value,
        reason_code: text("[data-field-reason]"),
        hypothesis_code: text("[data-field-hypothesis]"),
        rule_version: text("[data-field-rule]"),
        inputs,
      },
    };
  }

  function payloadFor(form) {
    switch (form.dataset.apiKind) {
      case "review": {
        const payload = basePayload(form);
        payload.expected_invoice_revision = Number(form.elements.expected_invoice_revision.value);
        payload.edits = Array.from(form.querySelectorAll("fieldset"))
          .filter((fieldset) => fieldset.querySelector("[data-field-edit]").checked)
          .map(editValue);
        return payload;
      }
      case "confirmation": {
        const payload = basePayload(form);
        payload.expected_invoice_revision = Number(form.elements.expected_invoice_revision.value);
        payload.billing_coverage_confirmed = form.elements.billing_coverage_confirmed.checked;
        payload.accepted_limitations = Array.from(form.querySelectorAll("[data-accepted-limitation]:checked"))
          .map((input) => input.value);
        return payload;
      }
      case "selection": {
        const payload = basePayload(form);
        payload.relationship = form.elements.relationship.value;
        payload.member_versions = JSON.parse(form.querySelector("[data-member-versions]").value);
        const selected = Array.from(form.querySelectorAll("[data-included-invoice]:checked"))
          .map((input) => input.value);
        payload.included_ids = selected;
        return payload;
      }
      case "delete": {
        return {
          confirm: form.querySelector("[data-delete-confirm]").checked,
          expected_revision: Number(form.elements.expected_revision.value),
          expected_dataset_revision: Number(form.elements.expected_dataset_revision.value),
        };
      }
      default:
        throw new Error("Operação de conferência desconhecida.");
    }
  }

  document.addEventListener("submit", async (event) => {
    const form = event.target.closest("form[data-json-api-form]");
    if (!form) return;
    event.preventDefault();
    const status = form.querySelector("[data-status]");
    const button = form.querySelector('button[type="submit"], button:not([type])');
    if (button) button.disabled = true;
    try {
      const method = form.dataset.apiKind === "delete" ? "DELETE" : "POST";
      const result = await window.EcoWattHTTP.request(form.dataset.endpoint, {
        method,
        data: payloadFor(form),
        idempotencyKey: `invoice-ui-${crypto.randomUUID()}`,
      });
      if (status) {
        const receipt = result && (result.confirmation_id || result.selection_id || result.invoice_id);
        const summary = form.dataset.apiKind === "delete"
          ? "Remoção registrada. Redirecionando para a lista de faturas."
          : `Operação registrada${receipt ? ` (${receipt})` : ""}. Atualize a página para ver as revisões atuais.`;
        status.textContent = summary;
      }
      if (form.dataset.successUrl) {
        window.setTimeout(() => {
          window.location.assign(form.dataset.successUrl);
        }, 350);
      }
    } catch (error) {
      if (status) status.textContent = `${error.message || "Não foi possível concluir."} (${error.code || "erro"})`;
    } finally {
      if (button) button.disabled = false;
    }
  });

  document.addEventListener("change", (event) => {
    const relationship = event.target.closest("[data-selection-relationship]");
    if (!relationship) return;
    const form = relationship.closest("form");
    const includeAll = ["distinct_periods", "complement"].includes(relationship.value);
    for (const checkbox of form.querySelectorAll("[data-included-invoice]")) {
      checkbox.checked = includeAll;
      checkbox.disabled = includeAll;
    }
  });
})();
