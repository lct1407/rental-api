"""UI alignment - services table and credit fields

Revision ID: 002_ui_alignment
Revises: 001_initial_migration
Create Date: 2025-11-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_ui_alignment'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # Create services table
    op.create_table(
        'services',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('endpoint', sa.String(500), nullable=False),
        sa.Column('credits_per_call', sa.Integer(), server_default='1', nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_services_slug', 'services', ['slug'], unique=True)
    op.create_index('ix_services_is_active', 'services', ['is_active'])

    # Seed services data
    op.execute("""
        INSERT INTO services (name, slug, endpoint, credits_per_call, description, is_active)
        VALUES
        ('Etsy Publish', 'etsy_publish', '/v1/etsy/listings/publish', 5, 'Publish listings to Etsy marketplace', true),
        ('Address Verify', 'address_verify', '/v1/address/verify', 1, 'Verify and standardize postal addresses', true),
        ('Email Validate', 'email_validate', '/v1/email/validate', 1, 'Validate email address format and deliverability', true)
    """)

    # Add credit columns to users table
    op.add_column('users', sa.Column('first_name', sa.String(100)))
    op.add_column('users', sa.Column('last_name', sa.String(100)))
    op.add_column('users', sa.Column('credits_free', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('credits_paid', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('credits_total', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('monthly_free_credits', sa.Integer(), server_default='1000', nullable=False))

    # Migrate existing credit data - set total and paid to current credits value
    op.execute("""
        UPDATE users
        SET credits_total = credits,
            credits_paid = credits,
            credits_free = 0
        WHERE credits > 0
    """)

    # Update credits_total for users with 0 credits
    op.execute("""
        UPDATE users
        SET credits_total = 0,
            credits_paid = 0,
            credits_free = 0
        WHERE credits = 0
    """)

    # Add api_keys columns
    op.add_column('api_keys', sa.Column('project', sa.String(255), server_default='Default Project', nullable=False))
    op.add_column('api_keys', sa.Column('environment', sa.String(10), server_default='test', nullable=False))
    op.add_column('api_keys', sa.Column('status', sa.String(20), server_default='active', nullable=False))

    # Migrate is_active to status
    op.execute("""
        UPDATE api_keys
        SET status = CASE
            WHEN is_active = true THEN 'active'
            ELSE 'revoked'
        END
    """)

    # Add credit_transaction columns
    op.add_column('credit_transactions', sa.Column('service_id', sa.BigInteger()))
    op.add_column('credit_transactions', sa.Column('credit_type', sa.String(10)))
    op.add_column('credit_transactions', sa.Column('bonus_credits', sa.Integer(), server_default='0', nullable=False))

    # Add foreign key for service_id
    op.create_foreign_key(
        'fk_credit_transactions_service_id',
        'credit_transactions',
        'services',
        ['service_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Create index for service_id
    op.create_index('ix_credit_transactions_service_id', 'credit_transactions', ['service_id'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_credit_transactions_service_id', 'credit_transactions')

    # Drop foreign key
    op.drop_constraint('fk_credit_transactions_service_id', 'credit_transactions', type_='foreignkey')

    # Drop credit_transaction columns
    op.drop_column('credit_transactions', 'bonus_credits')
    op.drop_column('credit_transactions', 'credit_type')
    op.drop_column('credit_transactions', 'service_id')

    # Drop api_keys columns
    op.drop_column('api_keys', 'status')
    op.drop_column('api_keys', 'environment')
    op.drop_column('api_keys', 'project')

    # Drop user columns
    op.drop_column('users', 'monthly_free_credits')
    op.drop_column('users', 'credits_total')
    op.drop_column('users', 'credits_paid')
    op.drop_column('users', 'credits_free')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')

    # Drop services table indexes
    op.drop_index('ix_services_is_active', 'services')
    op.drop_index('ix_services_slug', 'services')

    # Drop services table
    op.drop_table('services')
