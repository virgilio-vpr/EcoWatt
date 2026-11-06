from decimal import Decimal

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Column, MetaData, Table, inspect, select, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError, StatementError

from ecowatt.config import Settings
from ecowatt.db.models import Company, Simulation, User
from ecowatt.db.session import make_engine, transaction
from ecowatt.db.types import DecimalType
from ecowatt.seed import seed


def test_migrations_upgrade_preserves_roots_and_rollback(tmp_path):
    settings = Settings(_env_file=None, database_url="sqlite:///" + str(tmp_path / "fresh.db"))
    cfg = Config("alembic.ini")
    cfg.attributes["settings"] = settings
    command.upgrade(cfg, "0001_roots")
    engine = make_engine(settings)
    with transaction(engine, write=True) as db:
        db.add(Company(id="root", name="Synthetic", phone="11999999999", address_line="A", city="B", state="SP", postal_code="00000"))
    command.upgrade(cfg, "head")
    command.check(cfg)
    with engine.connect() as conn:
        assert conn.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
        assert conn.exec_driver_sql("PRAGMA journal_mode").scalar() == "wal"
        assert conn.exec_driver_sql("PRAGMA foreign_key_check").all() == []
        assert conn.scalar(text("select name from companies where id='root'")) == "Synthetic"
    command.downgrade(cfg, "0001_roots")
    assert "sessions" not in inspect(engine).get_table_names()
    command.upgrade(cfg, "head")
    command.check(cfg)
    engine.dispose()


def test_foreign_keys_constraints_and_atomicity(environment):
    engine = environment.app.state.engine
    with pytest.raises(IntegrityError), transaction(engine, write=True) as db:
        db.add(Company(id="rollback", name="Atomic", phone="11999999999", address_line="A", city="B", state="SP", postal_code="00000"))
        db.flush()
        db.add(User(company_id="missing", email="orphan@ecowatt.test", responsible_name="A", password_hash="x"))
    with transaction(engine) as db:
        assert db.get(Company, "rollback") is None
    with engine.connect() as conn:
        assert conn.exec_driver_sql("PRAGMA foreign_key_check").all() == []
    with transaction(engine) as db:
        users = list(db.scalars(select(User)))
        owner, other = users
    # Mesmo com UUIDs válidos, empresa de outro dono é rejeitada pela FK composta.
    with pytest.raises(IntegrityError), transaction(engine, write=True) as db:
        db.add(Simulation(owner_id=owner.id, company_id=other.company_id,
                          created_by=owner.id, updated_by=owner.id, slot=1))


def test_unique_quota_slots_cannot_be_bypassed(environment):
    engine = environment.app.state.engine
    with transaction(engine, write=True) as db:
        owner = db.scalar(select(User).where(User.role == "client"))
        for slot in (1, 2):
            db.add(Simulation(owner_id=owner.id, company_id=owner.company_id,
                created_by=owner.id, updated_by=owner.id, slot=slot, status="failed"))
    with pytest.raises(IntegrityError), transaction(engine, write=True) as db:
        db.add(Simulation(owner_id=owner.id, company_id=owner.company_id,
            created_by=owner.id, updated_by=owner.id, slot=1))
    with pytest.raises(IntegrityError), transaction(engine, write=True) as db:
        db.add(Simulation(owner_id=owner.id, company_id=owner.company_id,
            created_by=owner.id, updated_by=owner.id, slot=None))


def test_decimal_roundtrip_without_float(environment):
    engine = environment.app.state.engine
    metadata = MetaData()
    table = Table("decimal_probe", metadata, Column("value", DecimalType(30, 10)))
    table.create(engine)
    values = [Decimal("12345678901234567890.1234567890"), Decimal("-0.0000000001"), None]
    with engine.begin() as conn:
        for value in values:
            conn.execute(table.insert().values(value=value))
        assert list(conn.scalars(select(table.c.value))) == values
        assert conn.exec_driver_sql("select typeof(value) from decimal_probe where value is not null").scalars().all() == ["text", "text"]
    for invalid in [0.1, Decimal("NaN"), Decimal("0.00000000001"), Decimal("100000000000000000000")]:
        with pytest.raises(StatementError), engine.begin() as conn:
            conn.execute(table.insert().values(value=invalid))
    dialect = postgresql.dialect()
    assert "NUMERIC(30, 10)" == str(DecimalType(30, 10).load_dialect_impl(dialect))


def test_seed_idempotent_and_existing_data_preserved(environment):
    engine, settings = environment.app.state.engine, environment.settings
    with transaction(engine, write=True) as db:
        user = db.scalar(select(User).where(User.role == "client"))
        user.responsible_name = "Changed"
        original_hash = user.password_hash
    for _ in range(2):
        seed(engine, settings)
    with transaction(engine) as db:
        users = list(db.scalars(select(User)))
        assert len(users) == 2
        client = next(u for u in users if u.role == "client")
        assert client.responsible_name == "Changed"
        assert client.password_hash == original_hash
        assert all(u.fixture and u.confirmed_at for u in users)
    unsupported = settings.model_copy(update={"environment": "production"})
    with pytest.raises(ValueError):
        seed(engine, unsupported)
