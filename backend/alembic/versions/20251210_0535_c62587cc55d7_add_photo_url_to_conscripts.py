"""add_photo_url_to_conscripts

Revision ID: c62587cc55d7
Revises: 
Create Date: 2025-12-10 05:35:41.714083

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c62587cc55d7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавление поля photo_url в таблицу conscripts
    op.add_column('conscripts', sa.Column('photo_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    # Удаление поля photo_url из таблицы conscripts
    op.drop_column('conscripts', 'photo_url')
