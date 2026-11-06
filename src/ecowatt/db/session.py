from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from ecowatt.config import Settings


def make_engine(settings: Settings):
    """Não abre conexão ou cria diretórios ao construir o engine."""
    url = make_url(settings.database_url.get_secret_value())
    engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 10},
                           hide_parameters=True)

    @event.listens_for(engine, "connect")
    def configure(connection, _):
        connection.isolation_level = None
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=10000")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    @event.listens_for(engine, "begin")
    def begin(connection):
        # Todos os serviços de escrita usam writer; leituras não reservam escrita.
        mode = " IMMEDIATE" if connection.get_execution_options().get("writer") else ""
        connection.exec_driver_sql("BEGIN" + mode)

    return engine


def prepare_directory(settings: Settings):
    """Somente comandos explícitos de migração podem preparar armazenamento."""
    path = make_url(settings.database_url.get_secret_value()).database
    if path and path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def transaction(engine, *, write=False):
    with engine.connect().execution_options(writer=write) as connection:
        with connection.begin():
            with Session(bind=connection, expire_on_commit=False) as session:
                yield session
                session.flush()
