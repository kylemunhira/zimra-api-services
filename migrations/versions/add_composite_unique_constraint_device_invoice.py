"""add_composite_unique_constraint_device_invoice

Revision ID: composite_unique_device_invoice_001
Revises: manual_invoice_001
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'composite_unique_device_invoice_001'
down_revision = 'manual_invoice_001'
branch_labels = None
depends_on = None


def upgrade():
    # Remove the existing unique constraint on invoice_id only
    op.drop_constraint('invoice_id', 'invoice', type_='unique')
    
    # Add composite unique constraint on device_id and invoice_id
    op.create_unique_constraint('uq_device_invoice', 'invoice', ['device_id', 'invoice_id'])


def downgrade():
    # Remove the composite unique constraint
    op.drop_constraint('uq_device_invoice', 'invoice', type_='unique')
    
    # Restore the original unique constraint on invoice_id only
    op.create_unique_constraint('invoice_id', 'invoice', ['invoice_id'])

