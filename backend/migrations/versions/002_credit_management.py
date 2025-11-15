"""Add advanced credit management and rate limiting tables

Revision ID: 002_credit_management
Revises: 001_initial
Create Date: 2025-11-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '002_credit_management'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create credit management and rate limiting tables
    """

    # Create enum types for credit management
    op.execute("""
        CREATE TYPE credittype AS ENUM (
            'monthly_grant',
            'purchased',
            'bonus',
            'refund',
            'promotional'
        )
    """)

    op.execute("""
        CREATE TYPE credittransactiontype AS ENUM (
            'credit',
            'debit',
            'expire',
            'rollover',
            'admin_adjustment'
        )
    """)

    # Credit Wallets table
    op.create_table(
        'credit_wallets',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('total_balance', sa.Integer(), default=0, nullable=False),
        sa.Column('monthly_balance', sa.Integer(), default=0, nullable=False),
        sa.Column('purchased_balance', sa.Integer(), default=0, nullable=False),
        sa.Column('bonus_balance', sa.Integer(), default=0, nullable=False),
        sa.Column('total_consumed', sa.Integer(), default=0, nullable=False),
        sa.Column('monthly_consumed', sa.Integer(), default=0, nullable=False),
        sa.Column('lifetime_consumed', sa.Integer(), default=0, nullable=False),
        sa.Column('last_monthly_reset', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_monthly_reset', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_consumption', sa.DateTime(timezone=True), nullable=True),
        sa.Column('low_balance_threshold', sa.Integer(), default=100, nullable=False),
        sa.Column('alert_sent', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_credit_wallets_user_id', 'credit_wallets', ['user_id'])

    # Feature Definitions table
    op.create_table(
        'feature_definitions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('feature_key', sa.String(length=100), nullable=False),
        sa.Column('feature_name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('credit_cost', sa.Integer(), default=1, nullable=False),
        sa.Column('admin_exempt', sa.Boolean(), default=False, nullable=False),
        sa.Column('super_admin_exempt', sa.Boolean(), default=True, nullable=False),
        sa.Column('rpm_limit', sa.Integer(), nullable=True),
        sa.Column('rph_limit', sa.Integer(), nullable=True),
        sa.Column('rpd_limit', sa.Integer(), nullable=True),
        sa.Column('rpm_limit_monthly', sa.Integer(), nullable=True),
        sa.Column('cost_modifiers', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('plan_overrides', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_billable', sa.Boolean(), default=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('display_order', sa.Integer(), default=100, nullable=False),
        sa.Column('icon', sa.String(length=100), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('feature_key')
    )
    op.create_index('ix_feature_definitions_feature_key', 'feature_definitions', ['feature_key'])
    op.create_index('ix_feature_definitions_category', 'feature_definitions', ['category'])
    op.create_index('ix_feature_definitions_is_active', 'feature_definitions', ['is_active'])

    # Credit Packages table
    op.create_table(
        'credit_packages',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('wallet_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('credit_type', postgresql.ENUM(name='credittype'), nullable=False),
        sa.Column('original_amount', sa.Integer(), nullable=False),
        sa.Column('remaining_amount', sa.Integer(), nullable=False),
        sa.Column('consumed_amount', sa.Integer(), default=0, nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_expired', sa.Boolean(), default=False, nullable=False),
        sa.Column('expired_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payment_id', sa.BigInteger(), nullable=True),
        sa.Column('purchase_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('currency', sa.String(length=3), default='USD', nullable=True),
        sa.Column('priority', sa.Integer(), default=100, nullable=False),
        sa.Column('granted_by_id', sa.BigInteger(), nullable=True),
        sa.Column('grant_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['wallet_id'], ['credit_wallets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['granted_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_credit_packages_wallet_id', 'credit_packages', ['wallet_id'])
    op.create_index('ix_credit_packages_user_id', 'credit_packages', ['user_id'])
    op.create_index('ix_credit_packages_expires_at', 'credit_packages', ['expires_at'])
    op.create_index('ix_credit_packages_is_expired', 'credit_packages', ['is_expired'])
    op.create_index('ix_credit_packages_priority', 'credit_packages', ['priority'])

    # Credit Ledgers table (transaction history)
    op.create_table(
        'credit_ledgers',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('wallet_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('transaction_type', postgresql.ENUM(name='credittransactiontype'), nullable=False),
        sa.Column('credit_type', postgresql.ENUM(name='credittype'), nullable=True),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('balance_before', sa.Integer(), nullable=False),
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.String(length=255), nullable=True),
        sa.Column('source_type', sa.String(length=100), nullable=True),
        sa.Column('feature_id', sa.BigInteger(), nullable=True),
        sa.Column('feature_name', sa.String(length=255), nullable=True),
        sa.Column('admin_id', sa.BigInteger(), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['wallet_id'], ['credit_wallets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['feature_id'], ['feature_definitions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_credit_ledgers_wallet_id', 'credit_ledgers', ['wallet_id'])
    op.create_index('ix_credit_ledgers_user_id', 'credit_ledgers', ['user_id'])
    op.create_index('ix_credit_ledgers_transaction_type', 'credit_ledgers', ['transaction_type'])
    op.create_index('ix_credit_ledgers_source_id', 'credit_ledgers', ['source_id'])
    op.create_index('ix_credit_ledgers_created_at', 'credit_ledgers', ['created_at'])

    # Credit Pricing table
    op.create_table(
        'credit_pricing',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('credits', sa.Integer(), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(length=3), default='USD', nullable=False),
        sa.Column('discount_percentage', sa.Numeric(5, 2), default=0, nullable=False),
        sa.Column('original_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('valid_days', sa.Integer(), default=365, nullable=False),
        sa.Column('is_featured', sa.Boolean(), default=False, nullable=False),
        sa.Column('is_popular', sa.Boolean(), default=False, nullable=False),
        sa.Column('display_order', sa.Integer(), default=100, nullable=False),
        sa.Column('badge_text', sa.String(length=50), nullable=True),
        sa.Column('stripe_price_id', sa.String(length=255), nullable=True),
        sa.Column('paypal_plan_id', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('min_purchase_count', sa.Integer(), default=1, nullable=False),
        sa.Column('max_purchase_count', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('features', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('stripe_price_id'),
        sa.UniqueConstraint('paypal_plan_id')
    )
    op.create_index('ix_credit_pricing_is_active', 'credit_pricing', ['is_active'])

    # Rate Limit Rules table
    op.create_table(
        'rate_limit_rules',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('api_key_id', sa.BigInteger(), nullable=True),
        sa.Column('organization_id', sa.BigInteger(), nullable=True),
        sa.Column('rule_name', sa.String(length=255), nullable=False),
        sa.Column('rule_type', sa.String(length=50), nullable=False),
        sa.Column('rpm_limit', sa.Integer(), nullable=True),
        sa.Column('rph_limit', sa.Integer(), nullable=True),
        sa.Column('rpd_limit', sa.Integer(), nullable=True),
        sa.Column('rpm_limit_monthly', sa.Integer(), nullable=True),
        sa.Column('burst_limit', sa.Integer(), nullable=True),
        sa.Column('burst_window_seconds', sa.Integer(), default=1, nullable=False),
        sa.Column('feature_key', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('priority', sa.Integer(), default=100, nullable=False),
        sa.Column('created_by_id', sa.BigInteger(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rate_limit_rules_user_id', 'rate_limit_rules', ['user_id'])
    op.create_index('ix_rate_limit_rules_api_key_id', 'rate_limit_rules', ['api_key_id'])
    op.create_index('ix_rate_limit_rules_organization_id', 'rate_limit_rules', ['organization_id'])
    op.create_index('ix_rate_limit_rules_feature_key', 'rate_limit_rules', ['feature_key'])
    op.create_index('ix_rate_limit_rules_is_active', 'rate_limit_rules', ['is_active'])


def downgrade() -> None:
    """
    Drop credit management and rate limiting tables
    """

    # Drop tables in reverse order
    op.drop_table('rate_limit_rules')
    op.drop_table('credit_pricing')
    op.drop_table('credit_ledgers')
    op.drop_table('credit_packages')
    op.drop_table('feature_definitions')
    op.drop_table('credit_wallets')

    # Drop enum types
    op.execute('DROP TYPE credittransactiontype')
    op.execute('DROP TYPE credittype')
