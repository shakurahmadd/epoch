"""consolidate observations by station date

Revision ID: a1f3c9d2e847
Revises: 730b03846ac6
Create Date: 2026-05-07

"""
from typing import Union, Sequence
from alembic import op


revision: str = 'a1f3c9d2e847'
down_revision: Union[str, Sequence[str], None] = '730b03846ac6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Consolidate temperature and rainfall rows that share the same (station_id, date)
    # into a single row. Previously, separate ingestion runs inserted them as separate
    # rows because the PK was an auto-increment id rather than (station_id, date).
    op.execute("""
        CREATE TABLE observations_consolidated AS
        SELECT
            station_id,
            date,
            MAX(max_air_temp)  AS max_air_temp,
            MIN(min_air_temp)  AS min_air_temp,
            SUM(prcp_amt)      AS prcp_amt
        FROM observations
        GROUP BY station_id, date
    """)

    op.execute("DROP TABLE observations")
    op.execute("ALTER TABLE observations_consolidated RENAME TO observations")

    op.execute("""
        ALTER TABLE observations
        ADD CONSTRAINT observations_pkey PRIMARY KEY (station_id, date)
    """)

    op.execute("""
        ALTER TABLE observations
        ADD CONSTRAINT observations_station_id_fkey
        FOREIGN KEY (station_id) REFERENCES stations(src_id)
    """)


def downgrade() -> None:
    # This migration is irreversible — the original un-consolidated rows are gone.
    raise NotImplementedError(
        "Cannot downgrade: the pre-consolidation observations data no longer exists."
    )
