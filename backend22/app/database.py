import duckdb
import threading
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(HERE, "data", "kepsa.duckdb")

_write_lock = threading.Lock()
_con = None


def get_connection():
    """Single shared connection. DuckDB allows multiple cursors over one
    connection to read concurrently; writes are serialized via _write_lock
    to avoid corrupting the file under concurrent requests."""
    global _con
    if _con is None:
        _con = duckdb.connect(DB_PATH)
    return _con


def query(sql, params=None):
    """Read query -> list[dict]"""
    con = get_connection()
    cur = con.cursor()
    res = cur.execute(sql, params or [])
    cols = [d[0] for d in res.description]
    rows = res.fetchall()
    return [dict(zip(cols, row)) for row in rows]


def execute_write(sql, params=None):
    """Write query (INSERT/UPDATE/DELETE), serialized with a lock."""
    con = get_connection()
    with _write_lock:
        con.execute(sql, params or [])
