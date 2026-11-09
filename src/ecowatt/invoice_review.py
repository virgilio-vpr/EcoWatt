"""Comandos fechados de revisão; apenas escalares estruturados, nunca arquivos."""
from typing import Annotated

from pydantic import Field, model_validator

from ecowatt.invoice_result import Closed, Value


class FieldEdit(Closed):
    path: Annotated[str, Field(strict=True, max_length=200)]
    expected_version: Annotated[int, Field(strict=True, ge=1)]
    field: Value


class ReviewInput(Closed):
    expected_revision: Annotated[int, Field(strict=True, ge=1)]
    expected_dataset_revision: Annotated[int, Field(strict=True, ge=1)]
    expected_invoice_revision: Annotated[int, Field(strict=True, ge=1)]
    reason_code: Annotated[str, Field(strict=True, pattern=r"^[a-zA-Z0-9_.:-]{1,60}$")]
    edits: tuple[FieldEdit, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def unique_paths(self):
        if len({edit.path for edit in self.edits}) != len(self.edits):
            raise ValueError("Campo repetido")
        return self
