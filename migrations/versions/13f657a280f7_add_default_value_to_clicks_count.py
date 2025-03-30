"""Add default value to clicks_count

Revision ID: 13f657a280f7
Revises: df7e361f6ef8
Create Date: 2025-03-20 20:48:59.265730

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '13f657a280f7'
down_revision: Union[str, None] = 'df7e361f6ef8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "links",
        "clicks_count",
        existing_type=sa.Integer(),
        server_default="0"
    )


def downgrade() -> None:
    op.alter_column(
        "links",
        "clicks_count",
        existing_type=sa.Integer(),
        server_default=None
    )
