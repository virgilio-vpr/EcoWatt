"""Eleição/fencing do coordenador; nenhum conteúdo ou segredo em claro."""
from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ecowatt.db.base import Base


class CoordinatorLease(Base):
    __tablename__ = "coordinator_lease"
    __table_args__ = (
        CheckConstraint("id = 1", name="singleton"),
        CheckConstraint("epoch >= 1", name="epoch"),
        CheckConstraint("length(token_hash) = 64", name="token_hash"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    epoch: Mapped[int] = mapped_column(Integer)
    token_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[int] = mapped_column(Integer)
