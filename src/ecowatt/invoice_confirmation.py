"""Comandos explícitos de conferência e seleção do conjunto sintético."""
from typing import Annotated, Literal
from uuid import UUID
from pydantic import Field, model_validator
from ecowatt.invoice_result import Closed

Revision = Annotated[int, Field(strict=True, ge=1)]
Reason = Annotated[str, Field(strict=True, pattern=r"^[a-zA-Z0-9_.:-]{1,60}$")]
Limitation = Literal["estimated_data", "market_unconfirmed", "free_market_scope",
    "contracted_demand_incomplete", "measured_demand_incomplete", "cycle_days_disagreement"]


class ConfirmationInput(Closed):
    expected_revision: Revision
    expected_dataset_revision: Revision
    expected_invoice_revision: Revision
    reason_code: Reason
    billing_coverage_confirmed: Annotated[bool, Field(strict=True)]
    accepted_limitations: tuple[Limitation, ...] = Field(default=(), max_length=6)

    @model_validator(mode="after")
    def distinct(self):
        if not self.billing_coverage_confirmed:
            raise ValueError("Confirme a cobertura do quadro")
        if len(set(self.accepted_limitations)) != len(self.accepted_limitations):
            raise ValueError("Limitação repetida")
        return self


class SelectionInput(Closed):
    expected_revision: Revision
    expected_dataset_revision: Revision
    reason_code: Reason
    relationship: Literal["duplicate", "replacement", "distinct_periods", "complement"]
    member_versions: Annotated[dict[UUID, Revision], Field(min_length=1, max_length=12)]
    included_ids: tuple[UUID, ...] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def consistent(self):
        if len(set(self.included_ids)) != len(self.included_ids) or not set(self.included_ids) <= self.member_versions.keys():
            raise ValueError("Escolha inválida")
        if self.relationship in ("duplicate", "replacement") and len(self.included_ids) != 1:
            raise ValueError("Selecione uma versão válida")
        if self.relationship in ("distinct_periods", "complement") and set(self.included_ids) != self.member_versions.keys():
            raise ValueError("Classificação deve abranger o grupo inteiro")
        return self
