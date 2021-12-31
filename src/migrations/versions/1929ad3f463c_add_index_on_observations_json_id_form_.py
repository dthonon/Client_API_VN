"""Add index on observations_json.id_form_universal

Revision ID: 1929ad3f463c
Revises: 
Create Date: 2021-12-29 23:29:06.208386

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1929ad3f463c"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        index_name="ix_import_observations_json_id_form_universal",
        table_name="observations_json",
        columns=["id_form_universal"],
    )


def downgrade():
    op.drop_index(
        index_name="ix_import_observations_json_id_form_universal",
        table_name="observations_json",
    )
