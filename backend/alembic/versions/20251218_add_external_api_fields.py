"""add_external_api_fields

Добавление полей для совместимости с внешним AI API:
- os_vision_without_correction (острота зрения левого глаза)
- od_vision_without_correction (острота зрения правого глаза)
- dentist_json (зубная формула стоматолога)

Revision ID: a1b2c3d4e5f6
Revises: c62587cc55d7
Create Date: 2025-12-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'c62587cc55d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Добавление новых полей в таблицу specialists_examinations
    для полной совместимости с форматом внешнего AI API
    """

    # 1. Поле для офтальмолога - зрение левого глаза без коррекции
    op.add_column(
        'specialists_examinations',
        sa.Column(
            'os_vision_without_correction',
            sa.Numeric(precision=3, scale=2),
            nullable=True,
            comment='Острота зрения левого глаза без коррекции (для офтальмолога)'
        )
    )

    # 2. Поле для офтальмолога - зрение правого глаза без коррекции
    op.add_column(
        'specialists_examinations',
        sa.Column(
            'od_vision_without_correction',
            sa.Numeric(precision=3, scale=2),
            nullable=True,
            comment='Острота зрения правого глаза без коррекции (для офтальмолога)'
        )
    )

    # 3. Поле для стоматолога - зубная формула в формате JSON
    op.add_column(
        'specialists_examinations',
        sa.Column(
            'dentist_json',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='Зубная формула стоматолога (JSON с ключами 11-48)'
        )
    )

    print("✅ Успешно добавлены 3 поля для совместимости с внешним API:")
    print("   - os_vision_without_correction (Numeric)")
    print("   - od_vision_without_correction (Numeric)")
    print("   - dentist_json (JSONB)")


def downgrade() -> None:
    """
    Откат изменений - удаление добавленных полей
    """

    # Удаляем поля в обратном порядке
    op.drop_column('specialists_examinations', 'dentist_json')
    op.drop_column('specialists_examinations', 'od_vision_without_correction')
    op.drop_column('specialists_examinations', 'os_vision_without_correction')

    print("⏪ Откачены изменения: удалены поля для внешнего API")
