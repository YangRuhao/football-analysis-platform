import os
from contextlib import contextmanager

from psycopg2 import pool
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": os.environ.get("DB_NAME", "football_analytics"),
    "user": os.environ.get("DB_USER", "football_app"),
    "password": os.environ.get("DB_PASSWORD"),
}

POOL_MIN = int(os.environ.get("DB_POOL_MIN", "1"))
POOL_MAX = int(os.environ.get("DB_POOL_MAX", "10"))
_connection_pool = None


def _get_pool():
    global _connection_pool
    if _connection_pool is None:
        if not DB_CONFIG["password"]:
            raise RuntimeError("DB_PASSWORD must be set; refusing to use an insecure default password")
        if POOL_MIN < 1 or POOL_MAX < POOL_MIN:
            raise RuntimeError("Invalid DB_POOL_MIN/DB_POOL_MAX configuration")
        _connection_pool = pool.ThreadedConnectionPool(POOL_MIN, POOL_MAX, **DB_CONFIG)
    return _connection_pool


def close_pool():
    global _connection_pool
    if _connection_pool is not None:
        _connection_pool.closeall()
        _connection_pool = None


def check_database():
    with get_cursor() as cur:
        cur.execute("SELECT 1")
        return cur.fetchone()[0] == 1


@contextmanager
def get_cursor():
    conn = _get_pool().getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _get_pool().putconn(conn)
