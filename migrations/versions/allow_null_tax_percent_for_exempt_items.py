"""allow null tax_percent for exempt items

Revision ID: allow_null_tax_percent
Revises: edd7f639fd7b
Create Date: 2025-08-05 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'allow_null_tax_percent'
down_revision = 'device_global_number_001'
branch_labels = None
depends_on = None


def upgrade():
    # Allow NULL values for tax_percent column in invoice_line_item table
    op.alter_column('invoice_line_item', 'tax_percent',
                    existing_type=sa.Float(),
                    nullable=True)


def downgrade():
    # Revert to NOT NULL constraint for tax_percent column
    op.alter_column('invoice_line_item', 'tax_percent',
                    existing_type=sa.Float(),
                    nullable=False) 