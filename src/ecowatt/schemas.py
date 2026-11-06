from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator
from email_validator import validate_email, EmailNotValidError

Text = Annotated[str, Field(min_length=1, max_length=200)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Address(Input):
    address_line: Annotated[str, Field(min_length=1, max_length=300)]
    city: Annotated[str, Field(min_length=1, max_length=100)]
    state: Annotated[str, Field(pattern=r"^[A-Z]{2}$")]
    postal_code: Annotated[str, Field(min_length=5, max_length=12)]


class CompanyInput(Address):
    name: Text
    phone: Annotated[str, Field(min_length=8, max_length=30)]


class EmailInput(Input):
    email: Annotated[str, Field(max_length=254)]

    @field_validator("email")
    @classmethod
    def email_format(cls, value):
        try:
            # Domínios .test são permitidos para fixtures, sem consulta DNS.
            return validate_email(value, check_deliverability=False, test_environment=True).normalized.lower()
        except EmailNotValidError as exc:
            raise ValueError("E-mail inválido") from exc


def validate_password(value: str) -> str:
    if not (8 <= len(value) <= 128 and any(c.isupper() for c in value)
            and any(c.islower() for c in value) and sum(c.isdecimal() for c in value) >= 2
            and any(not c.isalnum() and not c.isspace() for c in value)):
        raise ValueError("Senha: 8–128 caracteres, maiúscula, minúscula, especial e dois algarismos")
    return value


class PasswordInput(Input):
    password: SecretStr
    password_confirmation: SecretStr

    @model_validator(mode="after")
    def password_policy(self):
        validate_password(self.password.get_secret_value())
        if self.password != self.password_confirmation:
            raise ValueError("Confirmação de senha diferente")
        return self


class Registration(EmailInput, PasswordInput):
    email_confirmation: str
    responsible_name: Text
    company: CompanyInput

    @model_validator(mode="after")
    def email_matches(self):
        if self.email != self.email_confirmation.strip().lower():
            raise ValueError("Confirmação de e-mail diferente")
        return self


class Login(EmailInput):
    password: SecretStr = Field(max_length=128)


class TokenInput(Input):
    token: Annotated[str, Field(min_length=32, max_length=128)]


class ResetPassword(PasswordInput, TokenInput):
    pass


class SimulationCreate(Input):
    """Dono/empresa derivados da sessão; admin seleciona dono na URL própria."""
    pass


class UnitInput(Address):
    expected_revision: int = Field(ge=1)
    distributor_id: UUID
    unit_identifier: Annotated[str, Field(min_length=1, max_length=100)]
    holder_name: Text


class DeleteInput(Input):
    confirm: bool
    expected_revision: int = Field(ge=1)


class StatusInput(Input):
    status: Annotated[str, Field(pattern="^(active|blocked)$")]


class ProfileInput(Input):
    responsible_name: Text


class ErrorResponse(BaseModel):
    code: str
    message: str
    fields: list[str]
    request_id: str


class SimulationOutput(BaseModel):
    id: str
    owner_id: str
    company_id: str
    created_by: str
    updated_by: str
    status: str
    revision: int
    distributor_id: str | None
    unit_identifier: str | None
    holder_name: str | None
    address_line: str | None
    city: str | None
    state: str | None
    postal_code: str | None
    created_at: int
    unit_saved: bool


class SimulationsPage(BaseModel):
    items: list[SimulationOutput]
    total: int
    page: int
    page_size: int
    limit: int


class CompanyOutput(CompanyInput):
    id: str


class MeOutput(BaseModel):
    id: str
    email: str
    responsible_name: str
    role: str
    company_id: str
