"""cascade delete on audit_competition_events.competition_id

Revision ID: c3f1a2b4d5e6
Revises: 28fcc248bd4e
Create Date: 2026-05-10 16:30:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = 'c3f1a2b4d5e6'
down_revision = '28fcc248bd4e'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    fks = inspector.get_foreign_keys('audit_competition_events')
    old_fk = next(
        (fk for fk in fks if fk['referred_table'] == 'competitions'),
        None,
    )

    if old_fk and old_fk.get('name'):
        op.drop_constraint(
            old_fk['name'],
            'audit_competition_events',
            type_='foreignkey',
        )

    op.create_foreign_key(
        'fk_audit_comp_events_competition_id',
        'audit_competition_events',
        'competitions',
        ['competition_id'],
        ['id'],
        ondelete='CASCADE',
    )


def downgrade():
    op.drop_constraint(
        'fk_audit_comp_events_competition_id',
        'audit_competition_events',
        type_='foreignkey',
    )
    op.create_foreign_key(
        'audit_competition_events_competition_id_fkey',
        'audit_competition_events',
        'competitions',
        ['competition_id'],
        ['id'],
    )
