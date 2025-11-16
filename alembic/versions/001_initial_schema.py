"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-11-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create games table
    op.create_table(
        'games',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('public_id', sa.String(), nullable=False, unique=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('api_key', sa.String(), nullable=False, unique=True),
        sa.Column('created_at', sa.String(), nullable=False),
    )

    # Create highscores table
    op.create_table(
        'highscores',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('player_name', sa.String(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
    )


def downgrade() -> None:
    op.drop_table('highscores')
    op.drop_table('games')
