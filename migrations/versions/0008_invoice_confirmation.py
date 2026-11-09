"""Confirmação e escolha versionadas, sem documentos ou dados retroativos."""
from alembic import op
import sqlalchemy as sa

revision = "0008_invoice_confirmation"
down_revision = "0007_invoice_publications"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("invoice_confirmations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("invoice_id", sa.String(36), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("unit_revision", sa.Integer(), nullable=False),
        sa.Column("invoice_revision", sa.Integer(), nullable=False),
        sa.Column("dataset_revision", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("policy_version", sa.String(80), nullable=False),
        sa.Column("reason_code", sa.String(60), nullable=False),
        sa.Column("field_versions", sa.JSON(), nullable=False),
        sa.Column("accepted_limitations", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.CheckConstraint("unit_revision >= 1 AND invoice_revision >= 1 AND dataset_revision >= 1", name="revisions"),
        sa.CheckConstraint("length(content_hash) = 64", name="hash"))
    op.create_index("ix_invoice_confirmations_invoice_revision", "invoice_confirmations", ["invoice_id", "invoice_revision", "unit_revision"])
    op.create_table("invoice_selections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("simulation_id", sa.String(36), sa.ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("unit_revision", sa.Integer(), nullable=False),
        sa.Column("dataset_revision", sa.Integer(), nullable=False),
        sa.Column("relationship", sa.String(20), nullable=False),
        sa.Column("reason_code", sa.String(60), nullable=False),
        sa.Column("member_versions", sa.JSON(), nullable=False),
        sa.Column("included_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.CheckConstraint("unit_revision >= 1 AND dataset_revision >= 1", name="revisions"),
        sa.CheckConstraint("relationship IN ('duplicate','replacement','distinct_periods','complement')", name="relationship"))
    op.create_index("ix_invoice_selections_simulation", "invoice_selections", ["simulation_id"])


def downgrade():
    op.execute("UPDATE invoices SET status = 'needs_review' WHERE id IN (SELECT invoice_id FROM invoice_confirmations)")
    op.drop_table("invoice_selections")
    op.drop_table("invoice_confirmations")
