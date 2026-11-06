"""Raízes e dependentes da Fase 1; instantes UTC em segundos Unix."""

import time
from uuid import uuid4

from sqlalchemy import CheckConstraint, ForeignKey, ForeignKeyConstraint, Index, Integer, String, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column

from ecowatt.db.base import Base


def new_id():
    return str(uuid4())


def now():
    return int(time.time())


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str] = mapped_column(String(30))
    address_line: Mapped[str] = mapped_column(String(300))
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(2))
    postal_code: Mapped[str] = mapped_column(String(12))


class Distributor(Base):
    __tablename__ = "distributors"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    # Catálogo não equivale a parser/tarifa homologados.


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('client','admin')", name="role"),
        CheckConstraint("status IN ('pending','active','blocked')", name="status"),
        UniqueConstraint("id", "company_id", name="uq_users_id_company"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), unique=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    responsible_name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(10), default="client")
    status: Mapped[str] = mapped_column(String(10), default="pending")
    confirmed_at: Mapped[int | None] = mapped_column(Integer)
    fixture: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class AuthSession(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    csrf_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    last_seen_at: Mapped[int] = mapped_column(Integer, default=now)
    expires_at: Mapped[int] = mapped_column(Integer)
    revoked_at: Mapped[int | None] = mapped_column(Integer)


class EmailToken(Base):
    __tablename__ = "email_tokens"
    __table_args__ = (CheckConstraint("purpose IN ('activation','reset')", name="purpose"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    purpose: Mapped[str] = mapped_column(String(12))
    expires_at: Mapped[int] = mapped_column(Integer)
    consumed_at: Mapped[int | None] = mapped_column(Integer)


class RateBucket(Base):
    __tablename__ = "rate_buckets"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    window_start: Mapped[int] = mapped_column(Integer)
    attempts: Mapped[int] = mapped_column(Integer)


class Simulation(Base):
    __tablename__ = "simulations"
    __table_args__ = (
        ForeignKeyConstraint(["owner_id", "company_id"], ["users.id", "users.company_id"],
                             name="fk_simulations_owner_company", ondelete="RESTRICT"),
        CheckConstraint("status IN ('draft','processing','completed','partial','failed','deleted')", name="status"),
        CheckConstraint("slot IN (1,2) OR slot IS NULL", name="slot"),
        CheckConstraint("(status = 'deleted' AND slot IS NULL) OR (status != 'deleted' AND slot IS NOT NULL)", name="active_slot"),
        CheckConstraint("revision >= 1", name="revision"),
        UniqueConstraint("owner_id", "slot"),
        Index("ix_simulations_owner_created", "owner_id", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"))
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    updated_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    distributor_id: Mapped[str | None] = mapped_column(ForeignKey("distributors.id", ondelete="RESTRICT"))
    slot: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(15), default="draft")
    revision: Mapped[int] = mapped_column(Integer, default=1)
    unit_identifier: Mapped[str | None] = mapped_column(String(100))
    holder_name: Mapped[str | None] = mapped_column(String(200))
    address_line: Mapped[str | None] = mapped_column(String(300))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(2))
    postal_code: Mapped[str | None] = mapped_column(String(12))
    unit_saved_at: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    deleted_at: Mapped[int | None] = mapped_column(Integer)


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (UniqueConstraint("actor_id", "key_hash"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    key_hash: Mapped[str] = mapped_column(String(64))
    request_hash: Mapped[str] = mapped_column(String(64))
    simulation_id: Mapped[str] = mapped_column(ForeignKey("simulations.id", ondelete="CASCADE"))


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(60))
    resource_id: Mapped[str] = mapped_column(String(36))
    changes: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[int] = mapped_column(Integer, default=now)
