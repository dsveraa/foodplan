"""boolean de carbos en platos

Revision ID: 8ed57f5dcaa9
Revises: e542b17842d2
Create Date: 2025-01-04 16:57:20.151247

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8ed57f5dcaa9'
down_revision = 'e542b17842d2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('platos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tiene_carbos', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('platos', schema=None) as batch_op:
        batch_op.drop_column('tiene_carbos')

    # ### end Alembic commands ###
