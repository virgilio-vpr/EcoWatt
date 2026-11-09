"""Reservas sintéticas de admissão, sem habilitar uploads."""
from alembic import op
import sqlalchemy as sa

revision = "0005_invoice_admissions"
down_revision = "0004_invoices"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("invoice_admissions",
        sa.Column("task_id", sa.String(36), nullable=False),
        sa.Column("simulation_id", sa.String(36), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("byte_count", sa.Integer(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("layout_version", sa.String(80), nullable=False),
        sa.Column("parser_version", sa.String(80), nullable=False),
        sa.Column("removed", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("task_id", name=op.f("pk_invoice_admissions")),
        sa.ForeignKeyConstraint(["task_id"], ["simulation_tasks.id"], ondelete="CASCADE", name=op.f("fk_invoice_admissions_task_id_simulation_tasks")),
        sa.ForeignKeyConstraint(["simulation_id"], ["simulations.id"], ondelete="CASCADE", name=op.f("fk_invoice_admissions_simulation_id_simulations")),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT", name=op.f("fk_invoice_admissions_actor_id_users")),
        sa.UniqueConstraint("actor_id", "key_hash", name=op.f("uq_invoice_admissions_actor_id")),
        sa.CheckConstraint("byte_count > 0 AND byte_count <= 10000000", name=op.f("ck_invoice_admissions_bytes")),
        sa.CheckConstraint("page_count > 0 AND page_count <= 10", name=op.f("ck_invoice_admissions_pages")),
        sa.CheckConstraint("length(source_hash) = 64", name=op.f("ck_invoice_admissions_hash")))


def downgrade():
    op.drop_table("invoice_admissions")
