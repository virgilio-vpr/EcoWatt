"""Vínculo tarefa/fatura e revisão do conjunto, sem documento."""
from alembic import op
import sqlalchemy as sa

revision = "0007_invoice_publications"
down_revision = "0006_coordinator_lease"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("simulations", sa.Column("dataset_revision", sa.Integer(),
        sa.CheckConstraint("dataset_revision >= 1", name=op.f("ck_simulations_dataset_revision")),
        nullable=False, server_default="1"))
    op.create_table("invoice_publications",
        sa.Column("task_id", sa.String(36), nullable=False),
        sa.Column("invoice_id", sa.String(36), nullable=False),
        sa.Column("result_hash", sa.String(64), nullable=False),
        sa.Column("completion_hash", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("task_id", name=op.f("pk_invoice_publications")),
        sa.UniqueConstraint("invoice_id", name=op.f("uq_invoice_publications_invoice_id")),
        sa.ForeignKeyConstraint(["task_id"], ["invoice_admissions.task_id"], ondelete="CASCADE", name=op.f("fk_invoice_publications_task_id_invoice_admissions")),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE", name=op.f("fk_invoice_publications_invoice_id_invoices")),
        sa.CheckConstraint("length(result_hash) = 64 AND length(completion_hash) = 64", name=op.f("ck_invoice_publications_hashes")))


def downgrade():
    op.drop_table("invoice_publications")
    # SQLite >=3.35 suporta DROP COLUMN sem recriar o pai de todas as FKs.
    op.execute("ALTER TABLE simulations DROP COLUMN dataset_revision")
