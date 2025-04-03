"""Initial migration

Revision ID: 58df793a54f6
Revises: 
Create Date: 2025-04-03 18:59:08.560335

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


# revision identifiers, used by Alembic.
revision: str = '58df793a54f6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('apartments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('post_link', sa.TEXT(), nullable=False),
    sa.Column('user', sa.TEXT(), nullable=False),
    sa.Column('timestamp', sa.TEXT(), nullable=False),
    sa.Column('text', sa.TEXT(), nullable=False),
    sa.Column('text_embedding', pgvector.sqlalchemy.vector.VECTOR(dim=384), nullable=True),
    sa.Column('price', sa.TEXT(), nullable=True),
    sa.Column('location', sa.TEXT(), nullable=False),
    sa.Column('phone_numbers', sa.ARRAY(sa.String()), nullable=False),
    sa.Column('image_urls', sa.ARRAY(sa.String()), nullable=False),
    sa.Column('mentions', sa.ARRAY(sa.String()), nullable=False),
    sa.Column('summary', sa.TEXT(), nullable=False),
    sa.Column('source', sa.TEXT(), nullable=False),
    sa.Column('group_id', sa.TEXT(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('post_link')
    )
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('channel', sa.String(length=50), nullable=False),
    sa.Column('recipient', sa.String(length=255), nullable=False),
    sa.Column('message', sa.String(length=1000), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=False),
    sa.Column('telegram_id', sa.String(length=255), nullable=True),
    sa.Column('phone_number', sa.String(length=20), nullable=True),
    sa.Column('notify_telegram', sa.Boolean(), nullable=False),
    sa.Column('notify_email', sa.Boolean(), nullable=False),
    sa.Column('notify_whatsapp', sa.Boolean(), nullable=False),
    sa.Column('min_price', sa.Integer(), nullable=True),
    sa.Column('max_price', sa.Integer(), nullable=True),
    sa.Column('min_area', sa.Integer(), nullable=True),
    sa.Column('max_area', sa.Integer(), nullable=True),
    sa.Column('min_rooms', sa.Integer(), nullable=True),
    sa.Column('max_rooms', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('users')
    op.drop_table('notifications')
    op.drop_table('apartments')
    # ### end Alembic commands ###
