"""Phase 1: 0002_access_simulations. Reviewed dependency order; no data fixtures."""
from alembic import op
import sqlalchemy as sa

revision = '0002_access_simulations'
down_revision = '0001_roots'
branch_labels = None
depends_on = None

def upgrade():
    # Reviewed migration: explicit tables and named constraints.
    op.create_table('rate_buckets',
    sa.Column('key', sa.String(length=64), nullable=False),
    sa.Column('window_start', sa.Integer(), nullable=False),
    sa.Column('attempts', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('key', name=op.f('pk_rate_buckets'))
    )
    op.create_table('email_tokens',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('purpose', sa.String(length=12), nullable=False),
    sa.Column('expires_at', sa.Integer(), nullable=False),
    sa.Column('consumed_at', sa.Integer(), nullable=True),
    sa.CheckConstraint("purpose IN ('activation','reset')", name=op.f('ck_email_tokens_purpose')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_email_tokens_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_email_tokens')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_email_tokens_token_hash'))
    )
    op.create_index(op.f('ix_email_tokens_user_id'), 'email_tokens', ['user_id'], unique=False)
    op.create_table('sessions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('csrf_hash', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.Integer(), nullable=False),
    sa.Column('last_seen_at', sa.Integer(), nullable=False),
    sa.Column('expires_at', sa.Integer(), nullable=False),
    sa.Column('revoked_at', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_sessions_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_sessions')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_sessions_token_hash'))
    )
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)
    op.create_table('simulations',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('owner_id', sa.String(length=36), nullable=False),
    sa.Column('company_id', sa.String(length=36), nullable=False),
    sa.Column('created_by', sa.String(length=36), nullable=False),
    sa.Column('updated_by', sa.String(length=36), nullable=False),
    sa.Column('distributor_id', sa.String(length=36), nullable=True),
    sa.Column('slot', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=15), nullable=False),
    sa.Column('revision', sa.Integer(), nullable=False),
    sa.Column('unit_identifier', sa.String(length=100), nullable=True),
    sa.Column('holder_name', sa.String(length=200), nullable=True),
    sa.Column('address_line', sa.String(length=300), nullable=True),
    sa.Column('city', sa.String(length=100), nullable=True),
    sa.Column('state', sa.String(length=2), nullable=True),
    sa.Column('postal_code', sa.String(length=12), nullable=True),
    sa.Column('unit_saved_at', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.Integer(), nullable=False),
    sa.Column('deleted_at', sa.Integer(), nullable=True),
    sa.CheckConstraint("(status = 'deleted' AND slot IS NULL) OR (status != 'deleted' AND slot IS NOT NULL)", name=op.f('ck_simulations_active_slot')),
    sa.CheckConstraint("status IN ('draft','processing','completed','partial','failed','deleted')", name=op.f('ck_simulations_status')),
    sa.CheckConstraint('revision >= 1', name=op.f('ck_simulations_revision')),
    sa.CheckConstraint('slot IN (1,2) OR slot IS NULL', name=op.f('ck_simulations_slot')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_simulations_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_simulations_created_by_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['distributor_id'], ['distributors.id'], name=op.f('fk_simulations_distributor_id_distributors'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name=op.f('fk_simulations_owner_id_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['owner_id', 'company_id'], ['users.id', 'users.company_id'], name='fk_simulations_owner_company', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name=op.f('fk_simulations_updated_by_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_simulations')),
    sa.UniqueConstraint('owner_id', 'slot', name=op.f('uq_simulations_owner_id'))
    )
    op.create_index('ix_simulations_owner_created', 'simulations', ['owner_id', 'created_at'], unique=False)
    op.create_table('idempotency_keys',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('actor_id', sa.String(length=36), nullable=False),
    sa.Column('key_hash', sa.String(length=64), nullable=False),
    sa.Column('request_hash', sa.String(length=64), nullable=False),
    sa.Column('simulation_id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_idempotency_keys_actor_id_users'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['simulation_id'], ['simulations.id'], name=op.f('fk_idempotency_keys_simulation_id_simulations'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_idempotency_keys')),
    sa.UniqueConstraint('actor_id', 'key_hash', name=op.f('uq_idempotency_keys_actor_id'))
    )

    op.create_table('audit_events',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('actor_id', sa.String(length=36), nullable=True),
    sa.Column('action', sa.String(length=60), nullable=False),
    sa.Column('resource_id', sa.String(length=36), nullable=False),
    sa.Column('changes', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_audit_events_actor_id_users'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_events'))
    )

def downgrade():
    # Children before roots.
    op.drop_table('audit_events')
    op.drop_table('idempotency_keys')
    op.drop_index('ix_simulations_owner_created', table_name='simulations')
    op.drop_table('simulations')
    op.drop_index(op.f('ix_sessions_user_id'), table_name='sessions')
    op.drop_table('sessions')
    op.drop_index(op.f('ix_email_tokens_user_id'), table_name='email_tokens')
    op.drop_table('email_tokens')
    op.drop_table('rate_buckets')

