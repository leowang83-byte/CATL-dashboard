from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

import psycopg
from psycopg.rows import dict_row


@contextmanager
def get_conn(database_url: str) -> Iterator[psycopg.Connection]:
    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        yield conn


def start_run(conn: psycopg.Connection, job_name: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO etl_run_log (job_name, status, started_at)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (job_name, "running", datetime.now(timezone.utc)),
        )
        return int(cur.fetchone()["id"])


def finish_run(
    conn: psycopg.Connection,
    run_id: int,
    status: str,
    records_processed: int = 0,
    error_message: str | None = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE etl_run_log
            SET status = %s,
                finished_at = %s,
                records_processed = %s,
                error_message = %s
            WHERE id = %s
            """,
            (status, datetime.now(timezone.utc), records_processed, error_message, run_id),
        )

