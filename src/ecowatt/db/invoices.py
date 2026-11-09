"""Dados faturáveis estruturados. Nenhum documento ou texto integral é armazenado.

Estado de campo e histórico ficam em field_provenance; os valores atuais tipados
ficam nas tabelas de domínio. O futuro serviço de revisão deve gravá-los juntos.
"""
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, ForeignKeyConstraint, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, validates

from ecowatt.db.base import Base
from ecowatt.db.models import new_id, now
from ecowatt.db.types import DecimalType


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("simulation_id", "source_hash"),
        CheckConstraint("length(source_hash) = 64", name="source_hash"),
        CheckConstraint("source_kind IN ('synthetic','document')", name="source_kind"),
        CheckConstraint("status IN ('uploaded','extracting','needs_review','ready','failed','expired')", name="status"),
        CheckConstraint("revision >= 1 AND dataset_revision >= 1", name="revision"),
        CheckConstraint("coverage IN ('complete','partial','unknown')", name="coverage"),
        CheckConstraint("cycle_days IS NULL OR cycle_days > 0", name="cycle_days"),
        CheckConstraint("cycle_start IS NULL OR cycle_end IS NULL OR cycle_end >= cycle_start", name="cycle"),
        CheckConstraint("modality IN ('blue','green','other','unknown')", name="modality"),
        CheckConstraint("market IN ('captive','free','unknown')", name="market"),
        CheckConstraint("market_candidate IN ('captive','free','unknown')", name="market_candidate"),
        CheckConstraint("market_assessment IN ('suggested','confirmed','conflicting')", name="market_assessment"),
        CheckConstraint("rebilling_status IN ('unknown','original','replacement','complement')", name="rebilling_status"),
        Index("ix_invoices_simulation_cycle", "simulation_id", "cycle_start", "cycle_end", "competence"),
        Index("ix_invoices_simulation_status", "simulation_id", "status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    simulation_id: Mapped[str] = mapped_column(ForeignKey("simulations.id", ondelete="CASCADE"))
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    dataset_revision: Mapped[int] = mapped_column(Integer)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    contract_version: Mapped[str] = mapped_column(String(30), default="invoice-v0.2")
    source_hash: Mapped[str] = mapped_column(String(64))
    source_kind: Mapped[str] = mapped_column(String(12))
    parser_version: Mapped[str | None] = mapped_column(String(80))
    layout_version: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(15), default="needs_review")
    error_code: Mapped[str | None] = mapped_column(String(60))
    coverage: Mapped[str] = mapped_column(String(10), default="unknown")
    distributor_id: Mapped[str | None] = mapped_column(ForeignKey("distributors.id", ondelete="RESTRICT"))
    consumer_unit_id: Mapped[str | None] = mapped_column(String(100))
    holder_name: Mapped[str | None] = mapped_column(String(200))
    printed_address_line: Mapped[str | None] = mapped_column(String(300))
    printed_city: Mapped[str | None] = mapped_column(String(100))
    printed_state: Mapped[str | None] = mapped_column(String(2))
    printed_postal_code: Mapped[str | None] = mapped_column(String(12))
    competence: Mapped[str | None] = mapped_column(String(7))
    cycle_start: Mapped[date | None] = mapped_column(Date)
    cycle_end: Mapped[date | None] = mapped_column(Date)
    cycle_days: Mapped[int | None] = mapped_column(Integer)
    subgroup: Mapped[str | None] = mapped_column(String(30))
    modality: Mapped[str] = mapped_column(String(10), default="unknown")
    customer_class: Mapped[str | None] = mapped_column(String(100))
    supply_type: Mapped[str | None] = mapped_column(String(60))
    market: Mapped[str] = mapped_column(String(10), default="unknown")
    market_candidate: Mapped[str] = mapped_column(String(10), default="unknown")
    market_assessment: Mapped[str] = mapped_column(String(12), default="suggested")
    invoice_number: Mapped[str | None] = mapped_column(String(100))
    rebilling_status: Mapped[str] = mapped_column(String(12), default="unknown")
    next_reading: Mapped[date | None] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date)
    invoice_total: Mapped[Decimal | None] = mapped_column(DecimalType(30, 10))
    amount_payable: Mapped[Decimal | None] = mapped_column(DecimalType(30, 10))
    known_components_total: Mapped[Decimal | None] = mapped_column(DecimalType(30, 10))
    residual: Mapped[Decimal | None] = mapped_column(DecimalType(30, 10))
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class InvoiceMeasurement(Base):
    __tablename__ = "invoice_measurements"
    __table_args__ = (
        UniqueConstraint("id", "invoice_id", name="uq_invoice_measurements_id_invoice"),
        UniqueConstraint("invoice_id", "post"),
        CheckConstraint("post IN ('peak','off_peak','single')", name="post"),
        CheckConstraint("reactive_nature IN ('inductive','capacitive','unknown')", name="reactive_nature"),
        CheckConstraint("reactive_demand_unit IS NULL OR reactive_demand_unit IN ('kvar','kW')", name="reactive_demand_unit"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"))
    post: Mapped[str] = mapped_column(String(10))
    contracted_demand: Mapped[Decimal | None] = mapped_column(DecimalType(30, 10))
    measured_active_demand: Mapped[Decimal | None] = mapped_column(DecimalType(30, 10))
    billed_active_demand: Mapped[Decimal | None] = mapped_column(DecimalType(30, 10))
    active_energy: Mapped[Decimal | None] = mapped_column(DecimalType(30, 10))
    reactive_energy: Mapped[Decimal | None] = mapped_column(DecimalType(30, 10))
    reactive_demand: Mapped[Decimal | None] = mapped_column(DecimalType(30, 10))
    reactive_demand_unit: Mapped[str | None] = mapped_column(String(5))
    power_factor: Mapped[Decimal | None] = mapped_column(DecimalType(20, 16))
    loss_adjustment_included: Mapped[bool | None] = mapped_column(Boolean)
    reactive_nature: Mapped[str] = mapped_column(String(12), default="unknown")

    @validates("contracted_demand", "measured_active_demand", "billed_active_demand",
               "active_energy", "reactive_energy", "reactive_demand", "power_factor")
    def validate_quantity(self, key, value):
        if value is not None:
            if not isinstance(value, (Decimal, str)):
                raise TypeError("Usar Decimal ou string")
            number = Decimal(value)
            if not number.is_finite() or number < 0 or (key == "power_factor" and number > 1):
                raise ValueError("Grandeza fora dos limites")
        return value


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    __table_args__ = (
        UniqueConstraint("id", "invoice_id", name="uq_invoice_items_id_invoice"),
        UniqueConstraint("invoice_id", "position"),
        ForeignKeyConstraint(["measurement_id", "invoice_id"], ["invoice_measurements.id", "invoice_measurements.invoice_id"],
                             name="fk_invoice_items_measurement_invoice", ondelete="RESTRICT"),
        CheckConstraint("position >= 1", name="position"),
        CheckConstraint("type IN ('active_energy_te','active_energy_tusd','regular_demand','idle_demand',"
                        "'overrun_demand','reactive_energy_excess','reactive_demand_excess','flag','tax','other','unclassified')", name="type"),
        CheckConstraint("post IS NULL OR post IN ('peak','off_peak','single')", name="post"),
        CheckConstraint("price_basis IN ('with_tax','without_tax','unknown')", name="price_basis"),
        CheckConstraint("quantity_unit IS NULL OR quantity_unit IN ('kWh','MWh','kW','kvarh','kvar','other')", name="quantity_unit"),
        CheckConstraint("quantity_unit != 'other' OR quantity_unit_definition IS NOT NULL", name="other_unit"),
        CheckConstraint("reactive_nature IN ('inductive','capacitive','unknown')", name="reactive_nature"),
        CheckConstraint("valid_from IS NULL OR valid_to IS NULL OR valid_to >= valid_from", name="segment_dates"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"))
    measurement_id: Mapped[str | None] = mapped_column(String(36))
    position: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String(30), default="unclassified")
    description: Mapped[str | None] = mapped_column(String(160))
    post: Mapped[str | None] = mapped_column(String(10))
    quantity: Mapped[Decimal | None] = mapped_column(DecimalType(30, 10))
    quantity_unit: Mapped[str | None] = mapped_column(String(8))
    quantity_unit_definition: Mapped[str | None] = mapped_column(String(60))
    regulated_rate: Mapped[Decimal | None] = mapped_column(DecimalType(38, 18))
    effective_price: Mapped[Decimal | None] = mapped_column(DecimalType(38, 18))
    price_basis: Mapped[str] = mapped_column(String(12), default="unknown")
    amount: Mapped[Decimal | None] = mapped_column(DecimalType(30, 10))
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    segment_id: Mapped[str | None] = mapped_column(String(36))
    grouped_te: Mapped[bool | None] = mapped_column(Boolean)
    grouped_tusd: Mapped[bool | None] = mapped_column(Boolean)
    reactive_nature: Mapped[str] = mapped_column(String(12), default="unknown")


class FieldProvenance(Base):
    """Versões de campos normalizados; valor anterior é a versão precedente.

    field_path é relativo ao alvo (cabeçalho, medição ou item). value é escalar
    normalizado, nunca trecho de extração; decimais usam string canônica.
    """
    __tablename__ = "field_provenance"
    __table_args__ = (
        UniqueConstraint("invoice_id", "field_path", "version"),
        UniqueConstraint("id", "invoice_id", name="uq_field_provenance_id_invoice"),
        ForeignKeyConstraint(["item_id", "invoice_id"], ["invoice_items.id", "invoice_items.invoice_id"],
                             name="fk_field_provenance_item_invoice", ondelete="CASCADE"),
        ForeignKeyConstraint(["measurement_id", "invoice_id"], ["invoice_measurements.id", "invoice_measurements.invoice_id"],
                             name="fk_field_provenance_measurement_invoice", ondelete="CASCADE"),
        CheckConstraint("item_id IS NULL OR measurement_id IS NULL", name="target"),
        CheckConstraint("version >= 1", name="version"),
        CheckConstraint("state IN ('confirmed','zero_confirmed','not_applicable','missing','unreadable','estimated')", name="state"),
        CheckConstraint("origin IN ('pdf_text','ocr','user','derived')", name="origin"),
        CheckConstraint("page IS NULL OR page >= 1", name="page"),
        CheckConstraint("origin NOT IN ('pdf_text','ocr') OR (page IS NOT NULL AND parser_version IS NOT NULL)", name="extraction"),
        CheckConstraint("origin != 'user' OR actor_id IS NOT NULL", name="user_actor"),
        CheckConstraint("state != 'estimated' OR hypothesis_code IS NOT NULL", name="estimate"),
        CheckConstraint("state != 'not_applicable' OR reason_code IS NOT NULL", name="not_applicable_reason"),
        CheckConstraint("origin != 'derived' OR rule_version IS NOT NULL", name="derived_rule"),
        CheckConstraint("state != 'zero_confirmed' OR (value = '0' AND coverage = 'complete')", name="zero"),
        CheckConstraint("(state IN ('missing','unreadable','not_applicable') AND value IS NULL) OR "
                        "(state IN ('confirmed','zero_confirmed','estimated') AND value IS NOT NULL)", name="value_state"),
        CheckConstraint("coverage IN ('complete','partial','unknown')", name="coverage"),
        CheckConstraint("version = 1 OR (actor_id IS NOT NULL AND reason_code IS NOT NULL)", name="correction"),
        CheckConstraint("(region_x IS NULL AND region_y IS NULL AND region_width IS NULL AND region_height IS NULL "
                        "AND region_unit IS NULL AND region_reference IS NULL) OR "
                        "(region_x IS NOT NULL AND region_y IS NOT NULL AND region_width IS NOT NULL "
                        "AND region_height IS NOT NULL AND region_unit IS NOT NULL AND region_reference IS NOT NULL "
                        "AND page IS NOT NULL)", name="region"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"))
    item_id: Mapped[str | None] = mapped_column(String(36))
    measurement_id: Mapped[str | None] = mapped_column(String(36))
    field_path: Mapped[str] = mapped_column(String(200))
    version: Mapped[int] = mapped_column(Integer, default=1)
    value: Mapped[str | None] = mapped_column(String(300))
    unit: Mapped[str | None] = mapped_column(String(30))
    state: Mapped[str] = mapped_column(String(16))
    origin: Mapped[str] = mapped_column(String(10))
    page: Mapped[int | None] = mapped_column(Integer)
    parser_version: Mapped[str | None] = mapped_column(String(80))
    coverage: Mapped[str] = mapped_column(String(10), default="unknown")
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    recorded_at: Mapped[int] = mapped_column(Integer, default=now)
    reason_code: Mapped[str | None] = mapped_column(String(60))
    hypothesis_code: Mapped[str | None] = mapped_column(String(60))
    rule_version: Mapped[str | None] = mapped_column(String(80))
    region_x: Mapped[Decimal | None] = mapped_column(DecimalType(20, 10))
    region_y: Mapped[Decimal | None] = mapped_column(DecimalType(20, 10))
    region_width: Mapped[Decimal | None] = mapped_column(DecimalType(20, 10))
    region_height: Mapped[Decimal | None] = mapped_column(DecimalType(20, 10))
    region_unit: Mapped[str | None] = mapped_column(String(20))
    region_reference: Mapped[str | None] = mapped_column(String(40))

    @validates("value")
    def validate_value(self, key, value):
        if value is not None and not isinstance(value, str):
            raise TypeError("Valor normalizado deve ser string, nunca float")
        return value


class FieldDependency(Base):
    """Entradas de uma regra/estimativa referenciam versões concretas de campos."""
    __tablename__ = "field_dependencies"
    __table_args__ = (
        ForeignKeyConstraint(["field_id", "invoice_id"], ["field_provenance.id", "field_provenance.invoice_id"],
                             name="fk_field_dependencies_output", ondelete="CASCADE"),
        ForeignKeyConstraint(["input_id", "invoice_id"], ["field_provenance.id", "field_provenance.invoice_id"],
                             name="fk_field_dependencies_input", ondelete="CASCADE"),
        CheckConstraint("field_id != input_id", name="distinct_input"),
    )
    field_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    input_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    invoice_id: Mapped[str] = mapped_column(String(36))


class InvoiceValidation(Base):
    __tablename__ = "invoice_validations"
    __table_args__ = (
        CheckConstraint("result IN ('pass','warning','blocking')", name="result"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), index=True)
    field_path: Mapped[str] = mapped_column(String(200))
    code: Mapped[str] = mapped_column(String(60))
    result: Mapped[str] = mapped_column(String(10))
    policy_version: Mapped[str] = mapped_column(String(80))
    observed: Mapped[Decimal | None] = mapped_column(DecimalType(38, 18))
    expected: Mapped[Decimal | None] = mapped_column(DecimalType(38, 18))
    difference: Mapped[Decimal | None] = mapped_column(DecimalType(38, 18))


class InvoiceMarketEvidence(Base):
    __tablename__ = "invoice_market_evidence"
    __table_args__ = (
        UniqueConstraint("invoice_id", "code"),
        CheckConstraint("code IN ('explicit_market_label','active_te_charge_present',"
                        "'active_te_charge_absent_with_complete_coverage','network_charge_present',"
                        "'user_confirmation','conflicting_evidence')", name="code"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(60))

