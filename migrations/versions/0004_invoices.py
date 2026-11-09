"""Faturas estruturadas, medi??es, itens, proveni?ncia, valida??es e mercado.

Migra??o aditiva; sem processamento de documentos ou altera??es dos pais.
"""
from alembic import op
import sqlalchemy as sa
from ecowatt.db.types import DecimalType

revision = "0004_invoices"
down_revision = "0003_simulation_tasks"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('invoices',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('simulation_id', sa.String(length=36), nullable=False),
    sa.Column('created_by', sa.String(length=36), nullable=False),
    sa.Column('dataset_revision', sa.Integer(), nullable=False),
    sa.Column('revision', sa.Integer(), nullable=False),
    sa.Column('contract_version', sa.String(length=30), nullable=False),
    sa.Column('source_hash', sa.String(length=64), nullable=False),
    sa.Column('source_kind', sa.String(length=12), nullable=False),
    sa.Column('parser_version', sa.String(length=80), nullable=True),
    sa.Column('layout_version', sa.String(length=80), nullable=True),
    sa.Column('status', sa.String(length=15), nullable=False),
    sa.Column('error_code', sa.String(length=60), nullable=True),
    sa.Column('coverage', sa.String(length=10), nullable=False),
    sa.Column('distributor_id', sa.String(length=36), nullable=True),
    sa.Column('consumer_unit_id', sa.String(length=100), nullable=True),
    sa.Column('holder_name', sa.String(length=200), nullable=True),
    sa.Column('printed_address_line', sa.String(length=300), nullable=True),
    sa.Column('printed_city', sa.String(length=100), nullable=True),
    sa.Column('printed_state', sa.String(length=2), nullable=True),
    sa.Column('printed_postal_code', sa.String(length=12), nullable=True),
    sa.Column('competence', sa.String(length=7), nullable=True),
    sa.Column('cycle_start', sa.Date(), nullable=True),
    sa.Column('cycle_end', sa.Date(), nullable=True),
    sa.Column('cycle_days', sa.Integer(), nullable=True),
    sa.Column('subgroup', sa.String(length=30), nullable=True),
    sa.Column('modality', sa.String(length=10), nullable=False),
    sa.Column('customer_class', sa.String(length=100), nullable=True),
    sa.Column('supply_type', sa.String(length=60), nullable=True),
    sa.Column('market', sa.String(length=10), nullable=False),
    sa.Column('market_candidate', sa.String(length=10), nullable=False),
    sa.Column('market_assessment', sa.String(length=12), nullable=False),
    sa.Column('invoice_number', sa.String(length=100), nullable=True),
    sa.Column('rebilling_status', sa.String(length=12), nullable=False),
    sa.Column('next_reading', sa.Date(), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('invoice_total', DecimalType(30, 10), nullable=True),
    sa.Column('amount_payable', DecimalType(30, 10), nullable=True),
    sa.Column('known_components_total', DecimalType(30, 10), nullable=True),
    sa.Column('residual', DecimalType(30, 10), nullable=True),
    sa.Column('created_at', sa.Integer(), nullable=False),
    sa.CheckConstraint("coverage IN ('complete','partial','unknown')", name=op.f('ck_invoices_coverage')),
    sa.CheckConstraint("market IN ('captive','free','unknown')", name=op.f('ck_invoices_market')),
    sa.CheckConstraint("market_assessment IN ('suggested','confirmed','conflicting')", name=op.f('ck_invoices_market_assessment')),
    sa.CheckConstraint("market_candidate IN ('captive','free','unknown')", name=op.f('ck_invoices_market_candidate')),
    sa.CheckConstraint("modality IN ('blue','green','other','unknown')", name=op.f('ck_invoices_modality')),
    sa.CheckConstraint("rebilling_status IN ('unknown','original','replacement','complement')", name=op.f('ck_invoices_rebilling_status')),
    sa.CheckConstraint("source_kind IN ('synthetic','document')", name=op.f('ck_invoices_source_kind')),
    sa.CheckConstraint("status IN ('uploaded','extracting','needs_review','ready','failed','expired')", name=op.f('ck_invoices_status')),
    sa.CheckConstraint('cycle_days IS NULL OR cycle_days > 0', name=op.f('ck_invoices_cycle_days')),
    sa.CheckConstraint('cycle_start IS NULL OR cycle_end IS NULL OR cycle_end >= cycle_start', name=op.f('ck_invoices_cycle')),
    sa.CheckConstraint('length(source_hash) = 64', name=op.f('ck_invoices_source_hash')),
    sa.CheckConstraint('revision >= 1 AND dataset_revision >= 1', name=op.f('ck_invoices_revision')),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_invoices_created_by_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['distributor_id'], ['distributors.id'], name=op.f('fk_invoices_distributor_id_distributors'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['simulation_id'], ['simulations.id'], name=op.f('fk_invoices_simulation_id_simulations'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_invoices')),
    sa.UniqueConstraint('simulation_id', 'source_hash', name=op.f('uq_invoices_simulation_id'))
    )
    op.create_index('ix_invoices_simulation_cycle', 'invoices', ['simulation_id', 'cycle_start', 'cycle_end', 'competence'], unique=False)
    op.create_index('ix_invoices_simulation_status', 'invoices', ['simulation_id', 'status'], unique=False)
    op.create_table('invoice_market_evidence',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('invoice_id', sa.String(length=36), nullable=False),
    sa.Column('code', sa.String(length=60), nullable=False),
    sa.CheckConstraint("code IN ('explicit_market_label','active_te_charge_present','active_te_charge_absent_with_complete_coverage','network_charge_present','user_confirmation','conflicting_evidence')", name=op.f('ck_invoice_market_evidence_code')),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], name=op.f('fk_invoice_market_evidence_invoice_id_invoices'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_invoice_market_evidence')),
    sa.UniqueConstraint('invoice_id', 'code', name=op.f('uq_invoice_market_evidence_invoice_id'))
    )
    op.create_table('invoice_measurements',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('invoice_id', sa.String(length=36), nullable=False),
    sa.Column('post', sa.String(length=10), nullable=False),
    sa.Column('contracted_demand', DecimalType(30, 10), nullable=True),
    sa.Column('measured_active_demand', DecimalType(30, 10), nullable=True),
    sa.Column('billed_active_demand', DecimalType(30, 10), nullable=True),
    sa.Column('active_energy', DecimalType(30, 10), nullable=True),
    sa.Column('reactive_energy', DecimalType(30, 10), nullable=True),
    sa.Column('reactive_demand', DecimalType(30, 10), nullable=True),
    sa.Column('reactive_demand_unit', sa.String(length=5), nullable=True),
    sa.Column('power_factor', DecimalType(20, 16), nullable=True),
    sa.Column('loss_adjustment_included', sa.Boolean(), nullable=True),
    sa.Column('reactive_nature', sa.String(length=12), nullable=False),
    sa.CheckConstraint("post IN ('peak','off_peak','single')", name=op.f('ck_invoice_measurements_post')),
    sa.CheckConstraint("reactive_demand_unit IS NULL OR reactive_demand_unit IN ('kvar','kW')", name=op.f('ck_invoice_measurements_reactive_demand_unit')),
    sa.CheckConstraint("reactive_nature IN ('inductive','capacitive','unknown')", name=op.f('ck_invoice_measurements_reactive_nature')),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], name=op.f('fk_invoice_measurements_invoice_id_invoices'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_invoice_measurements')),
    sa.UniqueConstraint('id', 'invoice_id', name='uq_invoice_measurements_id_invoice'),
    sa.UniqueConstraint('invoice_id', 'post', name=op.f('uq_invoice_measurements_invoice_id'))
    )
    op.create_table('invoice_validations',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('invoice_id', sa.String(length=36), nullable=False),
    sa.Column('field_path', sa.String(length=200), nullable=False),
    sa.Column('code', sa.String(length=60), nullable=False),
    sa.Column('result', sa.String(length=10), nullable=False),
    sa.Column('policy_version', sa.String(length=80), nullable=False),
    sa.Column('observed', DecimalType(38, 18), nullable=True),
    sa.Column('expected', DecimalType(38, 18), nullable=True),
    sa.Column('difference', DecimalType(38, 18), nullable=True),
    sa.CheckConstraint("result IN ('pass','warning','blocking')", name=op.f('ck_invoice_validations_result')),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], name=op.f('fk_invoice_validations_invoice_id_invoices'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_invoice_validations'))
    )
    op.create_index(op.f('ix_invoice_validations_invoice_id'), 'invoice_validations', ['invoice_id'], unique=False)
    op.create_table('invoice_items',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('invoice_id', sa.String(length=36), nullable=False),
    sa.Column('measurement_id', sa.String(length=36), nullable=True),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(length=30), nullable=False),
    sa.Column('description', sa.String(length=160), nullable=True),
    sa.Column('post', sa.String(length=10), nullable=True),
    sa.Column('quantity', DecimalType(30, 10), nullable=True),
    sa.Column('quantity_unit', sa.String(length=8), nullable=True),
    sa.Column('quantity_unit_definition', sa.String(length=60), nullable=True),
    sa.Column('regulated_rate', DecimalType(38, 18), nullable=True),
    sa.Column('effective_price', DecimalType(38, 18), nullable=True),
    sa.Column('price_basis', sa.String(length=12), nullable=False),
    sa.Column('amount', DecimalType(30, 10), nullable=True),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('segment_id', sa.String(length=36), nullable=True),
    sa.Column('grouped_te', sa.Boolean(), nullable=True),
    sa.Column('grouped_tusd', sa.Boolean(), nullable=True),
    sa.Column('reactive_nature', sa.String(length=12), nullable=False),
    sa.CheckConstraint("post IS NULL OR post IN ('peak','off_peak','single')", name=op.f('ck_invoice_items_post')),
    sa.CheckConstraint("price_basis IN ('with_tax','without_tax','unknown')", name=op.f('ck_invoice_items_price_basis')),
    sa.CheckConstraint("quantity_unit != 'other' OR quantity_unit_definition IS NOT NULL", name=op.f('ck_invoice_items_other_unit')),
    sa.CheckConstraint("quantity_unit IS NULL OR quantity_unit IN ('kWh','MWh','kW','kvarh','kvar','other')", name=op.f('ck_invoice_items_quantity_unit')),
    sa.CheckConstraint("reactive_nature IN ('inductive','capacitive','unknown')", name=op.f('ck_invoice_items_reactive_nature')),
    sa.CheckConstraint("type IN ('active_energy_te','active_energy_tusd','regular_demand','idle_demand','overrun_demand','reactive_energy_excess','reactive_demand_excess','flag','tax','other','unclassified')", name=op.f('ck_invoice_items_type')),
    sa.CheckConstraint('position >= 1', name=op.f('ck_invoice_items_position')),
    sa.CheckConstraint('valid_from IS NULL OR valid_to IS NULL OR valid_to >= valid_from', name=op.f('ck_invoice_items_segment_dates')),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], name=op.f('fk_invoice_items_invoice_id_invoices'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['measurement_id', 'invoice_id'], ['invoice_measurements.id', 'invoice_measurements.invoice_id'], name='fk_invoice_items_measurement_invoice', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_invoice_items')),
    sa.UniqueConstraint('id', 'invoice_id', name='uq_invoice_items_id_invoice'),
    sa.UniqueConstraint('invoice_id', 'position', name=op.f('uq_invoice_items_invoice_id'))
    )
    op.create_table('field_provenance',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('invoice_id', sa.String(length=36), nullable=False),
    sa.Column('item_id', sa.String(length=36), nullable=True),
    sa.Column('measurement_id', sa.String(length=36), nullable=True),
    sa.Column('field_path', sa.String(length=200), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('value', sa.String(length=300), nullable=True),
    sa.Column('unit', sa.String(length=30), nullable=True),
    sa.Column('state', sa.String(length=16), nullable=False),
    sa.Column('origin', sa.String(length=10), nullable=False),
    sa.Column('page', sa.Integer(), nullable=True),
    sa.Column('parser_version', sa.String(length=80), nullable=True),
    sa.Column('coverage', sa.String(length=10), nullable=False),
    sa.Column('actor_id', sa.String(length=36), nullable=True),
    sa.Column('recorded_at', sa.Integer(), nullable=False),
    sa.Column('reason_code', sa.String(length=60), nullable=True),
    sa.Column('hypothesis_code', sa.String(length=60), nullable=True),
    sa.Column('rule_version', sa.String(length=80), nullable=True),
    sa.Column('region_x', DecimalType(20, 10), nullable=True),
    sa.Column('region_y', DecimalType(20, 10), nullable=True),
    sa.Column('region_width', DecimalType(20, 10), nullable=True),
    sa.Column('region_height', DecimalType(20, 10), nullable=True),
    sa.Column('region_unit', sa.String(length=20), nullable=True),
    sa.Column('region_reference', sa.String(length=40), nullable=True),
    sa.CheckConstraint("(state IN ('missing','unreadable','not_applicable') AND value IS NULL) OR (state IN ('confirmed','zero_confirmed','estimated') AND value IS NOT NULL)", name=op.f('ck_field_provenance_value_state')),
    sa.CheckConstraint("coverage IN ('complete','partial','unknown')", name=op.f('ck_field_provenance_coverage')),
    sa.CheckConstraint("origin != 'derived' OR rule_version IS NOT NULL", name=op.f('ck_field_provenance_derived_rule')),
    sa.CheckConstraint("origin != 'user' OR actor_id IS NOT NULL", name=op.f('ck_field_provenance_user_actor')),
    sa.CheckConstraint("origin IN ('pdf_text','ocr','user','derived')", name=op.f('ck_field_provenance_origin')),
    sa.CheckConstraint("origin NOT IN ('pdf_text','ocr') OR (page IS NOT NULL AND parser_version IS NOT NULL)", name=op.f('ck_field_provenance_extraction')),
    sa.CheckConstraint("state != 'estimated' OR hypothesis_code IS NOT NULL", name=op.f('ck_field_provenance_estimate')),
    sa.CheckConstraint("state != 'not_applicable' OR reason_code IS NOT NULL", name=op.f('ck_field_provenance_not_applicable_reason')),
    sa.CheckConstraint("state != 'zero_confirmed' OR (value = '0' AND coverage = 'complete')", name=op.f('ck_field_provenance_zero')),
    sa.CheckConstraint("state IN ('confirmed','zero_confirmed','not_applicable','missing','unreadable','estimated')", name=op.f('ck_field_provenance_state')),
    sa.CheckConstraint('(region_x IS NULL AND region_y IS NULL AND region_width IS NULL AND region_height IS NULL AND region_unit IS NULL AND region_reference IS NULL) OR (region_x IS NOT NULL AND region_y IS NOT NULL AND region_width IS NOT NULL AND region_height IS NOT NULL AND region_unit IS NOT NULL AND region_reference IS NOT NULL AND page IS NOT NULL)', name=op.f('ck_field_provenance_region')),
    sa.CheckConstraint('item_id IS NULL OR measurement_id IS NULL', name=op.f('ck_field_provenance_target')),
    sa.CheckConstraint('page IS NULL OR page >= 1', name=op.f('ck_field_provenance_page')),
    sa.CheckConstraint('version = 1 OR (actor_id IS NOT NULL AND reason_code IS NOT NULL)', name=op.f('ck_field_provenance_correction')),
    sa.CheckConstraint('version >= 1', name=op.f('ck_field_provenance_version')),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_field_provenance_actor_id_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], name=op.f('fk_field_provenance_invoice_id_invoices'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['item_id', 'invoice_id'], ['invoice_items.id', 'invoice_items.invoice_id'], name='fk_field_provenance_item_invoice', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['measurement_id', 'invoice_id'], ['invoice_measurements.id', 'invoice_measurements.invoice_id'], name='fk_field_provenance_measurement_invoice', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_field_provenance')),
    sa.UniqueConstraint('id', 'invoice_id', name='uq_field_provenance_id_invoice'),
    sa.UniqueConstraint('invoice_id', 'field_path', 'version', name=op.f('uq_field_provenance_invoice_id'))
    )
    op.create_table('field_dependencies',
    sa.Column('field_id', sa.String(length=36), nullable=False),
    sa.Column('input_id', sa.String(length=36), nullable=False),
    sa.Column('invoice_id', sa.String(length=36), nullable=False),
    sa.CheckConstraint('field_id != input_id', name=op.f('ck_field_dependencies_distinct_input')),
    sa.ForeignKeyConstraint(['field_id', 'invoice_id'], ['field_provenance.id', 'field_provenance.invoice_id'], name='fk_field_dependencies_output', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['input_id', 'invoice_id'], ['field_provenance.id', 'field_provenance.invoice_id'], name='fk_field_dependencies_input', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('field_id', 'input_id', name=op.f('pk_field_dependencies'))
    )


def downgrade():
    op.drop_table('field_dependencies')
    op.drop_table('field_provenance')
    op.drop_table('invoice_items')
    op.drop_index(op.f('ix_invoice_validations_invoice_id'), table_name='invoice_validations')
    op.drop_table('invoice_validations')
    op.drop_table('invoice_measurements')
    op.drop_table('invoice_market_evidence')
    op.drop_index('ix_invoices_simulation_status', table_name='invoices')
    op.drop_index('ix_invoices_simulation_cycle', table_name='invoices')
    op.drop_table('invoices')
