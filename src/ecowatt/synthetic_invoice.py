"""Gabarito inventado para exercitar transporte/persistência, sem PDF ou tarifa."""
from ecowatt.invoice_result import ExtractionResult


def field(value, unit=None, **kwargs):
    return {"value": value, "state": "confirmed", "unit": unit, **kwargs}


def synthetic_result(source_hash, byte_count, page_count, unit_identifier, serial=0):
    """Valores fixos de teste, sem origem PDF/OCR ou homologação financeira."""
    return ExtractionResult.model_validate({
        "source_hash": source_hash, "byte_count": byte_count, "page_count": page_count,
        "coverage": "partial",
        "header": {"consumer_unit_id": field(unit_identifier), "holder_name": field("Titular sintético"),
            "competence": field(f"2026-{serial % 12 + 1:02d}"), "cycle_start": field("2026-01-01"),
            "cycle_end": field("2026-01-31"), "cycle_days": field(30), "subgroup": field("A4"),
            "modality": field("green"), "customer_class": field("Industrial sintética"),
            "invoice_total": field("19.99", "BRL"), "amount_payable": field("23.99", "BRL")},
        "measurements": [
            {"key": "single", "post": "single", "fields": {"contracted_demand": field("150", "kW")}},
            {"key": "peak", "post": "peak", "fields": {"measured_active_demand": field("123.4567890123", "kW")}},
            {"key": "off-peak", "post": "off_peak", "fields": {"measured_active_demand": field("140", "kW")}}],
        "items": [{"key": "line-1", "measurement_key": "peak", "fields": {
            "type": field("active_energy_te"), "post": field("peak"), "quantity": field("10", "kWh"),
            "quantity_unit": field("kWh"), "effective_price": field("1.999", "BRL/kWh"),
            "price_basis": field("with_tax"), "amount": field("19.99", "BRL")}},
            {"key": "line-2", "fields": {"type": field("idle_demand"), "amount": field("-1.23", "BRL")}}],
        "evidence": ["network_charge_present"]})
