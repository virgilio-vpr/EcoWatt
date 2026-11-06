"""Controle de cancelamento e leases de operações da simulação, sem payload."""
from alembic import op
import sqlalchemy as sa

revision = "0003_simulation_tasks"
down_revision = "0002_access_simulations"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("simulation_tasks",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("simulation_id", sa.String(36), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("executor_id", sa.String(64), nullable=True),
        sa.Column("lease_hash", sa.String(64), nullable=True),
        sa.Column("lease_expires_at", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.Column("ended_at", sa.Integer(), nullable=True),
        sa.Column("reason", sa.String(30), nullable=True),
        sa.CheckConstraint("status IN ('queued','running','finished','cancelled','expired')", name=op.f("ck_simulation_tasks_status")),
        sa.CheckConstraint("revision >= 1", name=op.f("ck_simulation_tasks_revision")),
        sa.CheckConstraint("(status = 'running' AND lease_hash IS NOT NULL AND lease_expires_at IS NOT NULL "
            "AND executor_id IS NOT NULL) OR (status != 'running' AND lease_hash IS NULL "
            "AND lease_expires_at IS NULL)", name=op.f("ck_simulation_tasks_lease")),
        sa.ForeignKeyConstraint(["simulation_id"], ["simulations.id"], ondelete="CASCADE", name=op.f("fk_simulation_tasks_simulation_id_simulations")),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT", name=op.f("fk_simulation_tasks_actor_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_simulation_tasks")))
    op.create_index("ix_simulation_tasks_simulation_status", "simulation_tasks", ["simulation_id", "status"])


def downgrade():
    op.drop_index("ix_simulation_tasks_simulation_status", table_name="simulation_tasks")
    op.drop_table("simulation_tasks")
