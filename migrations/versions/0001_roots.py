"""Phase 1: 0001_roots. Reviewed dependency order; no data fixtures."""
from alembic import op
import sqlalchemy as sa

revision = '0001_roots'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Reviewed migration: explicit tables and named constraints.
    op.create_table('companies',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('phone', sa.String(length=30), nullable=False),
    sa.Column('address_line', sa.String(length=300), nullable=False),
    sa.Column('city', sa.String(length=100), nullable=False),
    sa.Column('state', sa.String(length=2), nullable=False),
    sa.Column('postal_code', sa.String(length=12), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_companies'))
    )
    op.create_table('distributors',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_distributors')),
    sa.UniqueConstraint('code', name=op.f('uq_distributors_code'))
    )
    op.create_table('users',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('company_id', sa.String(length=36), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('responsible_name', sa.String(length=200), nullable=False),
    sa.Column('password_hash', sa.String(length=512), nullable=False),
    sa.Column('role', sa.String(length=10), nullable=False),
    sa.Column('status', sa.String(length=10), nullable=False),
    sa.Column('confirmed_at', sa.Integer(), nullable=True),
    sa.Column('fixture', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.Integer(), nullable=False),
    sa.CheckConstraint("role IN ('client','admin')", name=op.f('ck_users_role')),
    sa.CheckConstraint("status IN ('pending','active','blocked')", name=op.f('ck_users_status')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_users_company_id_companies'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('company_id', name=op.f('uq_users_company_id')),
    sa.UniqueConstraint('email', name=op.f('uq_users_email')),
    sa.UniqueConstraint('id', 'company_id', name='uq_users_id_company')
    )


def downgrade():
    # Reviewed migration: explicit tables and named constraints.
    op.drop_table('users')
    op.drop_table('distributors')
    op.drop_table('companies')

