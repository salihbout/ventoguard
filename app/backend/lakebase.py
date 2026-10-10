"""Lakebase Postgres access: a small psycopg pool whose password is a Databricks OAuth token.

Tokens live 60 minutes. The pool is rebuilt with a fresh token after 45, which also covers
reconnects after the endpoint scales to zero.
"""
import os
import threading
import time
from contextlib import contextmanager
from functools import lru_cache

import psycopg
from databricks.sdk import WorkspaceClient
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import LAKEBASE_ENDPOINT, OPS

TOKEN_TTL_S = 45 * 60


@lru_cache
def ws() -> WorkspaceClient:
    return WorkspaceClient()


class Lakebase:
    def __init__(self):
        self._pool: ConnectionPool | None = None
        self._born = 0.0
        self._lock = threading.Lock()

    def _new_pool(self) -> ConnectionPool:
        w = ws()
        token = w.postgres.generate_database_credential(endpoint=LAKEBASE_ENDPOINT).token
        host = os.getenv("PGHOST") or w.postgres.get_endpoint(name=LAKEBASE_ENDPOINT).status.hosts.host
        user = os.getenv("PGUSER") or w.current_user.me().user_name
        conninfo = psycopg.conninfo.make_conninfo(
            host=host, port=int(os.getenv("PGPORT", "5432")), dbname=os.getenv("PGDATABASE", "databricks_postgres"),
            user=user, password=token, sslmode="require")
        return ConnectionPool(conninfo, min_size=1, max_size=8, kwargs={"autocommit": True, "row_factory": dict_row},
                              check=ConnectionPool.check_connection, open=True)

    def pool(self) -> ConnectionPool:
        with self._lock:
            if self._pool is None or time.time() - self._born > TOKEN_TTL_S:
                old, self._pool, self._born = self._pool, self._new_pool(), time.time()
                if old:
                    old.close()
            return self._pool

    @contextmanager
    def cursor(self):
        with self.pool().connection() as conn, conn.cursor() as cur:
            yield cur

    def query(self, sql: str, params=None) -> list[dict]:
        for attempt in range(2):
            try:
                with self.cursor() as cur:
                    cur.execute(sql, params)
                    return cur.fetchall() if cur.description else []
            except psycopg.OperationalError:
                self._born = 0  # force a new pool with a fresh token, retry once
                if attempt:
                    raise
        return []


db = Lakebase()


def init_ops_schema():
    """The app's service principal creates (and therefore owns) its own OLTP schema."""
    db.query(f"CREATE SCHEMA IF NOT EXISTS {OPS}")
    db.query(f"""
        CREATE TABLE IF NOT EXISTS {OPS}.work_orders (
            wo_id SERIAL PRIMARY KEY,
            turbine_id TEXT NOT NULL,
            component TEXT,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN',
            planned_date DATE,
            crew TEXT,
            notes TEXT,
            failure_prob_14d NUMERIC(6,4),
            expected_avoidable_eur NUMERIC(14,0),
            created_by TEXT,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now())""")
