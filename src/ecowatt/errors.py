from dataclasses import dataclass, field


@dataclass
class DomainError(Exception):
    code: str
    message: str
    status: int = 400
    fields: list[str] = field(default_factory=list)
