"""columna de disponibilidad PlatoIngrediente

Revision ID: 5c874ed1216c
Revises: 724c81f6d90e
Create Date: 2025-01-18 12:41:04.002321

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c874ed1216c'
down_revision = '724c81f6d90e'
branch_labels = None
depends_on = None


def upgrade():
    # 1️⃣ Asegurar que se agrega como BOOLEAN (y no BOOLEAN[])
    op.add_column('plato_ingredientes', sa.Column('disponible', sa.Boolean, nullable=True, server_default=sa.text('false')))

    # 2️⃣ Asegurar que los valores existentes sean False
    op.execute("UPDATE plato_ingredientes SET disponible = false")

    # 3️⃣ Cambiar la columna para que sea NOT NULL
    op.alter_column('plato_ingredientes', 'disponible', nullable=False)

def downgrade():
    op.drop_column('plato_ingredientes', 'disponible')

