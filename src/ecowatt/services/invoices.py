"""Consulta interna com autorização herdada da simulação; sem rotas de upload."""
from sqlalchemy import select

from ecowatt.db.invoices import Invoice
from ecowatt.errors import DomainError
from ecowatt.services.simulations import require_simulation


def require_invoice(db, actor, simulation_id, invoice_id, revision=None):
    simulation = require_simulation(db, actor, simulation_id, revision)
    invoice = db.scalar(select(Invoice).where(Invoice.id == invoice_id,
        Invoice.simulation_id == simulation.id).execution_options(populate_existing=True))
    if invoice is None:
        raise DomainError("not_found", "Recurso não encontrado.", 404)
    return invoice
