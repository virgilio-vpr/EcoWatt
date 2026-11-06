"""Comando explícito local; nunca chamado pelo startup."""
from sqlalchemy import select

from ecowatt.config import Settings
from ecowatt.db.models import AuditEvent, Company, Distributor, User, now
from ecowatt.db.session import make_engine, transaction
from ecowatt.schemas import validate_password
from ecowatt.security.passwords import hasher


def seed(engine, settings):
    if settings.environment not in {"development", "test"}:
        raise ValueError("Seed proibido fora de desenvolvimento/teste")
    accounts = [("admin@ecowatt.test", "admin", settings.seed_admin_password.get_secret_value()),
                ("cliente@ecowatt.test", "client", settings.seed_client_password.get_secret_value())]
    with transaction(engine, write=True) as db:
        missing = [(email, role, password) for email, role, password in accounts
                   if not db.scalar(select(User.id).where(User.email == email))]
        # Validar todos antes de qualquer escrita; não sobrescrever contas existentes.
        for _, _, password in missing:
            validate_password(password)
        for email, role, password in missing:
            company = Company(name=f"Demonstração EcoWatt {role}", phone="11999990000",
                              address_line="Rua Sintética, 100", city="São Paulo", state="SP",
                              postal_code="01000-000")
            db.add(company)
            db.flush()
            user = User(company_id=company.id, email=email, responsible_name=f"Teste {role}",
                        password_hash=hasher.hash(password), role=role, status="active",
                        confirmed_at=now(), fixture=True)
            db.add(user)
            db.flush()
            db.add(AuditEvent(actor_id=user.id, action="fixture_created", resource_id=user.id))
        if not db.scalar(select(Distributor.id).where(Distributor.code == "synthetic-test")):
            db.add(Distributor(code="synthetic-test", name="Distribuidora sintética — sem tarifas ou parser"))


def main():
    settings = Settings()
    engine = make_engine(settings)
    try:
        seed(engine, settings)
        print("Seed local concluído; contas existentes preservadas.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
