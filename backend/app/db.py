import os
from contextlib import contextmanager

from psycopg2 import pool
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": os.environ.get("DB_NAME", "football_analytics"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "postgres"),
}

_connection_pool = None
    
def _get_pool():
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = pool.ThreadedConnectionPool(minconn=1, maxconn=10, **DB_CONFIG)
    return _connection_pool


@contextmanager
def get_cursor():
    """Borrow a connection from the pool for the duration of one request,
    always returning it to the pool even if the request raises."""
    conn_pool = _get_pool()
    conn = conn_pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn_pool.putconn(conn)
