"""
Ajout du champ user_id à CompanyContext
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('company_context', sa.Column('user_id', sa.Integer(), nullable=False, server_default='1'))
    op.create_foreign_key('fk_companycontext_user', 'company_context', 'user', ['user_id'], ['id'])
    op.alter_column('company_context', 'user_id', server_default=None)

def downgrade():
    op.drop_constraint('fk_companycontext_user', 'company_context', type_='foreignkey')
    op.drop_column('company_context', 'user_id')
