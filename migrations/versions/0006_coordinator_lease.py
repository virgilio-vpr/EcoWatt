"""Liderança única e geração das reservas, sem documentos."""
from alembic import op
import sqlalchemy as sa

revision = "0006_coordinator_lease"
down_revision = "0005_invoice_admissions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("coordinator_lease",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("epoch", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_coordinator_lease")),
        sa.CheckConstraint("id = 1", name=op.f("ck_coordinator_lease_singleton")),
        sa.CheckConstraint("epoch >= 1", name=op.f("ck_coordinator_lease_epoch")),
        sa.CheckConstraint("length(token_hash) = 64", name=op.f("ck_coordinator_lease_token_hash")))
    op.add_column("invoice_admissions", sa.Column("coordinator_epoch", sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table("invoice_admissions") as batch:
        batch.drop_column("coordinator_epoch")
    op.drop_table("coordinator_lease")
