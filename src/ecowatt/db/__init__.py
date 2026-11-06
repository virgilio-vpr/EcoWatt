"""Persistência SQLAlchemy 2 com esquema versionado por Alembic.

Não usar create_all no startup. Migrações definirão esquema e constraints.
"""
