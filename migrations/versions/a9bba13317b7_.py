"""empty message

Revision ID: a9bba13317b7
Revises: b61adf005219
Create Date: 2016-04-05 21:07:04.277835

"""

# revision identifiers, used by Alembic.
revision = 'a9bba13317b7'
down_revision = 'b61adf005219'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('posts', sa.Column('body_html', sa.Text(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('posts', 'body_html')
    ### end Alembic commands ###