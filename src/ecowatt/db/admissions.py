"""Reservas de metadados; nunca contém arquivo ou resultado de extração."""
from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ecowatt.db.base import Base


class InvoiceAdmission(Base):
    __tablename__ = "invoice_admissions"
    __table_args__ = (
        UniqueConstraint("actor_id", "key_hash"),
        CheckConstraint("byte_count > 0 AND byte_count <= 10000000", name="bytes"),
        CheckConstraint("page_count > 0 AND page_count <= 10", name="pages"),
        CheckConstraint("length(source_hash) = 64", name="hash"),
    )
    task_id: Mapped[str] = mapped_column(ForeignKey("simulation_tasks.id", ondelete="CASCADE"), primary_key=True)
    simulation_id: Mapped[str] = mapped_column(ForeignKey("simulations.id", ondelete="CASCADE"))
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    key_hash: Mapped[str] = mapped_column(String(64))
    request_hash: Mapped[str] = mapped_column(String(64))
    source_hash: Mapped[str] = mapped_column(String(64))
    byte_count: Mapped[int] = mapped_column(Integer)
    page_count: Mapped[int] = mapped_column(Integer)
    layout_version: Mapped[str] = mapped_column(String(80))
    parser_version: Mapped[str] = mapped_column(String(80))
    removed: Mapped[bool] = mapped_column(Boolean, default=False)
