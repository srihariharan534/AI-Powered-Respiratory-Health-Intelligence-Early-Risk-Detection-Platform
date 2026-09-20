"""enable_postgis_extension

Revision ID: 0001_enable_postgis
Revises: None
Create Date: 2026-09-19 19:50:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_enable_postgis"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable PostGIS spatial extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")


def downgrade() -> None:
    # Drop PostGIS spatial extension
    op.execute("DROP EXTENSION IF EXISTS postgis;")
