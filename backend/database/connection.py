import os
import threading
from contextlib import contextmanager

import psycopg
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

DATABASE_URL_DIRECT = os.getenv("DATABASE_URL_DIRECT", "").strip()

# These limits apply per backend process, so the deployment-wide maximum is
# DB_POOL_MAX multiplied by the number of processes and instances.
POOL_MIN_SIZE = int(os.getenv("DB_POOL_MIN", "0"))
POOL_MAX_SIZE = int(os.getenv("DB_POOL_MAX", "5"))
if POOL_MIN_SIZE < 0 or POOL_MAX_SIZE < 1 or POOL_MIN_SIZE > POOL_MAX_SIZE:
    raise ValueError("DB_POOL_MIN and DB_POOL_MAX must satisfy 0 <= min <= max, with max >= 1")

_pool: ConnectionPool | None = None
_pool_lock = threading.Lock()


def open_pool() -> None:
    """Create the pool once; request and script access can initialize it lazily."""
    global _pool
    if _pool is not None:
        return
    with _pool_lock:
        if _pool is not None:  # re-check inside the lock (thread-safe lazy open)
            return
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not configured")

        pool = ConnectionPool(
            conninfo=DATABASE_URL,
            min_size=POOL_MIN_SIZE,
            max_size=POOL_MAX_SIZE,
            kwargs={
                "connect_timeout": 10,
                "prepare_threshold": None,
            },
            max_idle=240,
            max_lifetime=1800,
            timeout=30,
            open=False,
        )
        pool.open(wait=True, timeout=30)
        _pool = pool


def close_pool() -> None:
    """Close the pool. Call from the FastAPI lifespan on shutdown."""
    global _pool
    with _pool_lock:
        pool, _pool = _pool, None
    if pool is not None:
        pool.close()


@contextmanager
def get_db():
    """Borrow a pooled connection.

    Commits on success, rolls back on exception, and always returns the
    connection to the pool:

        with get_db() as conn:
            rows = conn.execute("SELECT ...", (x,)).fetchall()
    """
    if _pool is None:
        open_pool()  # lazy open for scripts and tests
    with _pool.connection() as conn:
        yield conn


def get_direct_connection() -> psycopg.Connection:
    """One-off non-pooled connection for init_db and migrations. Caller closes it."""
    url = DATABASE_URL_DIRECT or DATABASE_URL
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg.connect(url, connect_timeout=10)