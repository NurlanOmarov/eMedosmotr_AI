"""rename_fields_to_api_format

Переименование полей в specialists_examinations для соответствия внешнему API:
- specialty_ru → med_commission_member
- doctor_category → valid_category
- icd10_code → diagnosis_accompany_id
- additional_comment → additional_act_comment
- complaints → complain

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-18 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Переименование полей для полного соответствия формату внешнего API
    """

    # 1. specialty_ru → med_commission_member
    op.alter_column(
        'specialists_examinations',
        'specialty_ru',
        new_column_name='med_commission_member',
        existing_type=sa.String(255),
        existing_nullable=True
    )

    # 2. doctor_category → valid_category
    op.alter_column(
        'specialists_examinations',
        'doctor_category',
        new_column_name='valid_category',
        existing_type=sa.String(10),
        existing_nullable=False
    )

    # 3. icd10_code → diagnosis_accompany_id
    op.alter_column(
        'specialists_examinations',
        'icd10_code',
        new_column_name='diagnosis_accompany_id',
        existing_type=sa.String(10),
        existing_nullable=False
    )

    # 4. additional_comment → additional_act_comment
    op.alter_column(
        'specialists_examinations',
        'additional_comment',
        new_column_name='additional_act_comment',
        existing_type=sa.Text(),
        existing_nullable=True
    )

    # 5. complaints → complain
    op.alter_column(
        'specialists_examinations',
        'complaints',
        new_column_name='complain',
        existing_type=sa.Text(),
        existing_nullable=True
    )

    # Пересоздать индексы с новыми именами
    op.drop_index('ix_specialists_examinations_doctor_category', table_name='specialists_examinations')
    op.create_index('ix_specialists_examinations_valid_category', 'specialists_examinations', ['valid_category'])

    op.drop_index('ix_specialists_examinations_icd10_code', table_name='specialists_examinations')
    op.create_index('ix_specialists_examinations_diagnosis_accompany_id', 'specialists_examinations', ['diagnosis_accompany_id'])

    print("✅ Поля успешно переименованы для соответствия внешнему API:")
    print("   specialty_ru → med_commission_member")
    print("   doctor_category → valid_category")
    print("   icd10_code → diagnosis_accompany_id")
    print("   additional_comment → additional_act_comment")
    print("   complaints → complain")


def downgrade() -> None:
    """
    Откат переименования полей
    """

    # Откатываем индексы
    op.drop_index('ix_specialists_examinations_diagnosis_accompany_id', table_name='specialists_examinations')
    op.create_index('ix_specialists_examinations_icd10_code', 'specialists_examinations', ['icd10_code'])

    op.drop_index('ix_specialists_examinations_valid_category', table_name='specialists_examinations')
    op.create_index('ix_specialists_examinations_doctor_category', 'specialists_examinations', ['doctor_category'])

    # Откатываем переименования (в обратном порядке)
    op.alter_column(
        'specialists_examinations',
        'complain',
        new_column_name='complaints',
        existing_type=sa.Text(),
        existing_nullable=True
    )

    op.alter_column(
        'specialists_examinations',
        'additional_act_comment',
        new_column_name='additional_comment',
        existing_type=sa.Text(),
        existing_nullable=True
    )

    op.alter_column(
        'specialists_examinations',
        'diagnosis_accompany_id',
        new_column_name='icd10_code',
        existing_type=sa.String(10),
        existing_nullable=False
    )

    op.alter_column(
        'specialists_examinations',
        'valid_category',
        new_column_name='doctor_category',
        existing_type=sa.String(10),
        existing_nullable=False
    )

    op.alter_column(
        'specialists_examinations',
        'med_commission_member',
        new_column_name='specialty_ru',
        existing_type=sa.String(255),
        existing_nullable=True
    )

    print("⏪ Откат выполнен: поля возвращены к исходным названиям")
