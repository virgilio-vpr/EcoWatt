from decimal import Decimal, InvalidOperation, localcontext

from sqlalchemy import Numeric, Text
from sqlalchemy.types import TypeDecorator


class DecimalType(TypeDecorator):
    """SQLite guarda texto; PostgreSQL usa Numeric(p,s), sem float."""

    impl = Text
    cache_ok = True

    def __init__(self, precision: int, scale: int):
        if not 0 <= scale <= precision or precision < 1:
            raise ValueError("Precisão/escala inválidas")
        self.precision, self.scale = precision, scale
        super().__init__()

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Numeric(self.precision, self.scale, asdecimal=True))
        if dialect.name != "sqlite":
            raise ValueError("Dialeto não suportado")
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, (Decimal, str)):
            raise TypeError("Usar Decimal ou string; float não é permitido")
        number = Decimal(value)
        if not number.is_finite():
            raise ValueError("Decimal deve ser finito")
        with localcontext() as ctx:
            ctx.prec = self.precision + self.scale + 2
            try:
                scaled = number.quantize(Decimal(1).scaleb(-self.scale))
            except InvalidOperation as exc:
                raise ValueError("Precisão excedida") from exc
            if scaled != number or abs(number) >= Decimal(10) ** (self.precision - self.scale):
                raise ValueError("Precisão/escala excedidas; arredondamento deve ser explícito")
        return format(scaled, "f") if dialect.name == "sqlite" else scaled

    def process_result_value(self, value, dialect):
        return None if value is None else Decimal(value)
