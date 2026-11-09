"""Contrato normalizado puro, fechado e versionado; sem ORM/PDF/OCR/rotas."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, model_validator

Coverage = Literal["complete", "partial", "unknown"]
Post = Literal["peak", "off_peak", "single"]
Key = Annotated[str, Field(strict=True, pattern=r"^[a-z][a-z0-9_-]{0,39}$")]
Code = Annotated[str, Field(strict=True, pattern=r"^[a-zA-Z0-9_.:-]{1,80}$")]


class Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")


class Value(Closed):
    value: StrictStr | StrictInt | StrictBool | None = None
    state: Literal["confirmed", "zero_confirmed", "missing", "unreadable", "not_applicable", "estimated"] = "missing"
    unit: Annotated[str, Field(strict=True, max_length=30)] | None = None
    # Somente origem sintética honesta nesta versão. PDF/OCR não habilitados.
    origin: Literal["user", "derived"] = "user"
    coverage: Coverage = "unknown"
    reason_code: Annotated[str, Field(strict=True, pattern=r"^[a-zA-Z0-9_.:-]{1,60}$")] | None = None
    hypothesis_code: Annotated[str, Field(strict=True, pattern=r"^[a-zA-Z0-9_.:-]{1,60}$")] | None = None
    rule_version: Code | None = None
    inputs: tuple[Annotated[str, Field(strict=True, max_length=200)], ...] = Field(default=(), max_length=32)

    @model_validator(mode="after")
    def consistent(self):
        absent = self.state in ("missing", "unreadable", "not_applicable")
        if absent != (self.value is None):
            raise ValueError("Estado e valor incompatíveis")
        if self.state == "not_applicable" and not self.reason_code:
            raise ValueError("Inaplicabilidade exige motivo")
        if self.state == "estimated" and (not self.hypothesis_code or not self.inputs):
            raise ValueError("Estimativa exige hipótese e dependências")
        if self.origin == "derived" and (not self.rule_version or not self.inputs):
            raise ValueError("Derivado exige regra e dependências")
        if self.inputs and self.origin != "derived" and self.state != "estimated":
            raise ValueError("Dependências exigem derivação ou estimativa")
        return self


@dataclass(frozen=True)
class Spec:
    kind: str = "text"
    size: int = 100
    scale: int = 0
    unit: str | None = None
    choices: tuple[str, ...] = ()
    fallback: str | None = None
    nonnegative: bool = False


def enum(*values, fallback=None):
    return Spec(choices=tuple(values), fallback=fallback)


QUANTITY = Spec("decimal", 30, 10, "*", nonnegative=True)
MONEY = Spec("decimal", 30, 10, "BRL")
PRICE = Spec("decimal", 38, 18, "BRL/*", nonnegative=True)
HEADER = {
    "consumer_unit_id": Spec(size=100), "holder_name": Spec(size=200),
    "printed_address_line": Spec(size=300), "printed_city": Spec(size=100),
    "printed_state": Spec(size=2), "printed_postal_code": Spec(size=12),
    "competence": Spec("competence"), "cycle_start": Spec("date"), "cycle_end": Spec("date"),
    "cycle_days": Spec("integer"), "subgroup": Spec(size=30),
    "modality": enum("blue", "green", "other", fallback="unknown"),
    "customer_class": Spec(size=100), "supply_type": Spec(size=60),
    "market": enum("captive", "free", fallback="unknown"),
    "invoice_number": Spec(size=100),
    "rebilling_status": enum("original", "replacement", "complement", fallback="unknown"),
    "next_reading": Spec("date"), "due_date": Spec("date"),
    "invoice_total": MONEY, "amount_payable": MONEY,
    "known_components_total": MONEY, "residual": MONEY,
}
MEASUREMENT = {
    **{name: Spec("decimal", 30, 10, "kW", nonnegative=True) for name in
        ("contracted_demand", "measured_active_demand", "billed_active_demand")},
    "active_energy": Spec("decimal", 30, 10, "kWh", nonnegative=True),
    "reactive_energy": Spec("decimal", 30, 10, "kvarh", nonnegative=True),
    "reactive_demand": QUANTITY,
    "reactive_demand_unit": enum("kvar", "kW"),
    "power_factor": Spec("factor", 20, 16, "1", nonnegative=True),
    "loss_adjustment_included": Spec("boolean"),
    "reactive_nature": enum("inductive", "capacitive", fallback="unknown"),
}
ITEM = {
    "type": enum("active_energy_te", "active_energy_tusd", "regular_demand", "idle_demand",
        "overrun_demand", "reactive_energy_excess", "reactive_demand_excess", "flag", "tax", "other", fallback="unclassified"),
    "description": Spec(size=160), "post": enum("peak", "off_peak", "single"),
    "quantity": QUANTITY, "quantity_unit": enum("kWh", "MWh", "kW", "kvarh", "kvar", "other"),
    "quantity_unit_definition": Spec(size=60), "regulated_rate": PRICE, "effective_price": PRICE,
    "price_basis": enum("with_tax", "without_tax", fallback="unknown"), "amount": MONEY,
    "valid_from": Spec("date"), "valid_to": Spec("date"), "segment_id": Spec(size=36),
    "grouped_te": Spec("boolean"), "grouped_tusd": Spec("boolean"),
    "reactive_nature": enum("inductive", "capacitive", fallback="unknown"),
}


def normalize(field, spec):
    """Devolve valor tipado atual e escalar canônico para proveniência/JSON."""
    value = field.value
    if value is None:
        return spec.fallback, None
    if spec.kind in ("decimal", "factor"):
        if type(value) is not str or len(value) > 100 or not re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", value):
            raise ValueError("Decimal exige string normalizada, sem float/expoente")
        number = Decimal(value)
        with localcontext() as context:
            context.prec = spec.size + spec.scale + 2
            try:
                scaled = number.quantize(Decimal(1).scaleb(-spec.scale))
            except InvalidOperation as exc:
                raise ValueError("Precisão excedida") from exc
            if scaled != number or abs(number) >= Decimal(10) ** (spec.size - spec.scale):
                raise ValueError("Precisão/escala excedida")
        if spec.nonnegative and number < 0 or spec.kind == "factor" and number > 1:
            raise ValueError("Grandeza fora dos limites")
        text = format(number, "f")
        text = text.rstrip("0").rstrip(".") if "." in text else text
        text = "0" if number == 0 else text
        if spec.unit == "*":
            valid_unit = field.unit in ("kWh", "MWh", "kW", "kvarh", "kvar", "other")
        elif spec.unit == "BRL/*":
            valid_unit = field.unit in ("BRL/kWh", "BRL/MWh", "BRL/kW", "BRL/kvarh", "BRL/kvar", "BRL/other")
        else:
            valid_unit = field.unit == spec.unit
        if not valid_unit:
            raise ValueError("Unidade incompatível")
        if field.state == "zero_confirmed" and (number != 0 or field.coverage != "complete"):
            raise ValueError("Zero confirmado exige zero e cobertura completa")
        return number, text
    if field.state == "zero_confirmed" or field.unit is not None:
        raise ValueError("Estado/unidade incompatível com campo não numérico")
    if spec.kind == "boolean":
        if type(value) is not bool:
            raise ValueError("Boolean estrito exigido")
        return value, "true" if value else "false"
    if spec.kind == "integer":
        if type(value) is not int or not 1 <= value <= 366:
            raise ValueError("Dias do ciclo inválidos")
        return value, str(value)
    if type(value) is not str or not 1 <= len(value) <= spec.size or any(ord(c) < 32 for c in value):
        raise ValueError("Texto normalizado inválido")
    if spec.choices and value not in spec.choices:
        raise ValueError("Classificação inválida")
    if spec.kind == "date":
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            raise ValueError("Data inválida")
        return date.fromisoformat(value), value
    if spec.kind == "competence" and not re.fullmatch(r"[0-9]{4}-(?:0[1-9]|1[0-2])", value):
        raise ValueError("Competência inválida")
    return value, value


def validate_fields(fields, specs):
    if not set(fields) <= set(specs):
        raise ValueError("Campo fora do contrato")
    for key, value in fields.items():
        normalize(value, specs[key])


class Measurement(Closed):
    key: Key
    post: Post
    fields: dict[str, Value] = Field(default_factory=dict, max_length=len(MEASUREMENT))

    @model_validator(mode="after")
    def check(self):
        validate_fields(self.fields, MEASUREMENT)
        unit = self.fields.get("reactive_demand_unit", Value()).value
        demand = self.fields.get("reactive_demand", Value())
        if demand.value is not None and demand.unit != unit:
            raise ValueError("Unidade da demanda reativa exige identificação explícita")
        return self


class Item(Closed):
    key: Key
    measurement_key: Key | None = None
    fields: dict[str, Value] = Field(default_factory=dict, max_length=len(ITEM))

    @model_validator(mode="after")
    def check(self):
        validate_fields(self.fields, ITEM)
        unit = self.fields.get("quantity_unit", Value()).value
        if unit == "other" and self.fields.get("quantity_unit_definition", Value()).value is None:
            raise ValueError("Outra unidade exige definição")
        for key in ("quantity", "regulated_rate", "effective_price"):
            field = self.fields.get(key, Value())
            if field.value is not None and (unit is None or field.unit != (unit if key == "quantity" else f"BRL/{unit}")):
                raise ValueError("Unidade do item inconsistente")
        start, end = (self.fields.get(k, Value()).value for k in ("valid_from", "valid_to"))
        if start and end and start > end:
            raise ValueError("Vigência invertida")
        return self


Evidence = Literal["explicit_market_label", "active_te_charge_present", "active_te_charge_absent_with_complete_coverage",
    "network_charge_present", "user_confirmation", "conflicting_evidence"]


class ExtractionResult(Closed):
    version: Literal["normalized-invoice-v1"] = "normalized-invoice-v1"
    source_kind: Literal["synthetic"] = "synthetic"
    source_hash: Annotated[str, Field(strict=True, pattern=r"^[0-9a-f]{64}$")]
    byte_count: Annotated[int, Field(strict=True, ge=1, le=10_000_000)]
    page_count: Annotated[int, Field(strict=True, ge=1, le=10)]
    distributor_code: Literal["SYNTHETIC"] = "SYNTHETIC"
    parser_version: Literal["synthetic-v1"] = "synthetic-v1"
    layout_version: Literal["synthetic-v1"] = "synthetic-v1"
    coverage: Coverage
    header: dict[str, Value] = Field(max_length=len(HEADER))
    measurements: tuple[Measurement, ...] = Field(default=(), max_length=3)
    items: tuple[Item, ...] = Field(default=(), max_length=128)
    market_candidate: Literal["captive", "free", "unknown"] = "unknown"
    market_assessment: Literal["suggested", "conflicting"] = "suggested"
    evidence: tuple[Evidence, ...] = Field(default=(), max_length=6)

    def fields(self):
        output = {f"header.{k}": v for k, v in self.header.items()}
        for collection, records in (("measurements", self.measurements), ("items", self.items)):
            for record in records:
                output.update({f"{collection}.{record.key}.{k}": v for k, v in record.fields.items()})
        return output

    @model_validator(mode="after")
    def check(self):
        validate_fields(self.header, HEADER)
        start, end = (self.header.get(k, Value()).value for k in ("cycle_start", "cycle_end"))
        if start and end and start > end:
            raise ValueError("Ciclo invertido")
        keys = [m.key for m in self.measurements]
        if len(keys) != len(set(keys)) or len({m.post for m in self.measurements}) != len(keys):
            raise ValueError("Medição/posto duplicado")
        if len({i.key for i in self.items}) != len(self.items):
            raise ValueError("Item duplicado")
        for item in self.items:
            if item.measurement_key is not None and item.measurement_key not in keys:
                raise ValueError("Referência de medição ausente")
        if len(set(self.evidence)) != len(self.evidence):
            raise ValueError("Evidência duplicada")
        if self.market_candidate == "free" and not {"explicit_market_label", "user_confirmation"} & set(self.evidence) and (self.coverage != "complete"
                or not {"active_te_charge_absent_with_complete_coverage", "network_charge_present"} <= set(self.evidence)):
            raise ValueError("Sugestão ACL exige cobertura/evidência suficientes")
        conflicting = ("conflicting_evidence" in self.evidence or
            {"active_te_charge_present", "active_te_charge_absent_with_complete_coverage"} <= set(self.evidence))
        if conflicting and self.market_assessment != "conflicting":
            raise ValueError("Evidências conflitantes exigem estado explícito")
        fields = self.fields()
        remaining = {key: set(field.inputs) for key, field in fields.items()}
        for key, inputs in remaining.items():
            if key in inputs or not inputs <= fields.keys() or len(inputs) != len(fields[key].inputs):
                raise ValueError("Dependência inválida")
        # Ordenação topológica iterativa, sem recursão sobre dados de entrada.
        while remaining:
            roots = {key for key, inputs in remaining.items() if not inputs}
            if not roots:
                raise ValueError("Ciclo de dependências")
            remaining = {key: inputs - roots for key, inputs in remaining.items() if key not in roots}
        return self
