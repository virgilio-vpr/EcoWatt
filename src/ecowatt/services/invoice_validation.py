"""Conferência observada, sem tarifas, tributos ou motor de oportunidades."""
from decimal import Decimal, localcontext

from sqlalchemy import select

from ecowatt.db.admissions import InvoiceAdmission, InvoicePublication
from ecowatt.db.invoices import Invoice, InvoiceItem, InvoiceValidation
from ecowatt.db.models import SimulationTask
from ecowatt.services.simulations import require_simulation

POLICY = "observed-financial-v1"


def financial_checks(db, invoice):
    rows = list(db.scalars(select(InvoiceItem).where(InvoiceItem.invoice_id == invoice.id).order_by(InvoiceItem.position)))
    output = []

    def add(code, path, result, observed=None, expected=None, difference=None):
        # Memória persistida é exata ou explicitamente indisponível; nunca arredonda.
        numbers = (observed, expected, difference)
        if any(n is not None and (abs(n) >= Decimal(10) ** 20 or n != n.quantize(Decimal("1e-18"))) for n in numbers):
            code, result, observed, expected, difference = "validation_numeric_range", "blocking", None, None, None
        output.append(dict(code=code, field_path=path, result=result,
            observed=observed, expected=expected, difference=difference))

    with localcontext() as ctx:
        ctx.prec = 110
        for item in rows:
            path = f"items.{item.id}.amount"
            if item.quantity is None or item.effective_price is None:
                add("product_unavailable", path, "warning")
            elif (item.quantity_unit is None or item.price_basis != "with_tax"):
                add("product_basis_unconfirmed", path, "blocking")
            elif item.amount is None:
                add("item_amount_missing", path, "blocking")
            else:
                product = item.quantity * item.effective_price
                difference = item.amount - product
                add("item_product", path, "pass" if abs(difference) <= Decimal("0.99") else "blocking",
                    item.amount, product, difference)
        if not rows or any(row.amount is None for row in rows) or invoice.invoice_total is None:
            add("billing_total_incomplete", "header.invoice_total", "blocking")
        else:
            total = sum((row.amount for row in rows), Decimal(0))
            residual = invoice.invoice_total - total
            add("billing_residual", "header.invoice_total", "pass" if residual == 0 else "blocking",
                invoice.invoice_total, total, residual)
            for name, expected in (("known_components_total", total), ("residual", residual)):
                value = getattr(invoice, name)
                if value is not None:
                    add("reported_" + name, "header." + name, "pass" if value == expected else "blocking",
                        value, expected, value - expected)
        if invoice.amount_payable is not None and invoice.invoice_total is not None:
            add("payable_information", "header.amount_payable", "warning" if invoice.amount_payable != invoice.invoice_total else "pass",
                invoice.amount_payable, invoice.invoice_total, invoice.amount_payable - invoice.invoice_total)
    return output


def record_validations(db, invoice):
    # Append-only: a política inclui a revisão que foi validada. GET usa o estado atual.
    db.flush()
    db.add_all(InvoiceValidation(invoice_id=invoice.id,
        policy_version=f"{POLICY}:r{invoice.revision}", **check) for check in financial_checks(db, invoice))


def dataset_readiness(db, actor, simulation_id):
    sim = require_simulation(db, actor, simulation_id)
    invoices = list(db.scalars(select(Invoice).where(Invoice.simulation_id == sim.id).order_by(Invoice.id)))
    reasons = {"confirmation_workflow_pending", "duplicate_resolution_pending"}
    if sim.unit_saved_at is None:
        reasons.add("unit_not_saved")
    if not invoices:
        reasons.add("no_invoices")
    entries = []
    for invoice in invoices:
        checks = financial_checks(db, invoice)
        if invoice.status != "ready":
            reasons.add("invoice_review_required")
        if any(check["result"] == "blocking" for check in checks):
            reasons.add("financial_review_required")
        entries.append({"invoice_id": invoice.id, "revision": invoice.revision, "status": invoice.status,
            "checks": [{key: format(value, "f") if isinstance(value, Decimal) else value
                for key, value in check.items()} for check in checks]})
    # Até tarefa finished sem publicação exige resolução; falha/expiração não some do conjunto.
    admissions = list(db.scalars(select(InvoiceAdmission).where(InvoiceAdmission.simulation_id == sim.id,
        InvoiceAdmission.removed.is_(False))))
    for row in admissions:
        task = db.get(SimulationTask, row.task_id)
        if task.status in ("queued", "running"):
            reasons.add("processing_pending")
        elif db.get(InvoicePublication, row.task_id) is None:
            reasons.add("admission_unresolved")
    return {"dataset_revision": sim.dataset_revision, "unit_revision": sim.revision,
        "ready_for_calculation": False, "policy_version": POLICY,
        "reasons": sorted(reasons), "invoices": entries}
