from alembic import context

from ecowatt.config import Settings
from ecowatt.db.base import Base
from ecowatt.db import models  # noqa: F401 — registrar metadata
from ecowatt.db import invoices  # noqa: F401 — registrar metadata faturável
from ecowatt.db import admissions  # noqa: F401 — registrar reservas
from ecowatt.db.session import make_engine, prepare_directory

config = context.config
settings = config.attributes.get("settings") or Settings()
if context.is_offline_mode():
    raise RuntimeError("Migrações locais exigem conexão; modo offline não validado")
prepare_directory(settings)
engine = make_engine(settings)
try:
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata,
                          render_as_batch=True, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
finally:
    engine.dispose()
