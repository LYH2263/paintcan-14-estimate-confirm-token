import sqlite3
def list_all(conn): return [dict(r) for r in conn.execute("SELECT * FROM rooms ORDER BY id").fetchall()]
def get(conn, rid):
    row = conn.execute("SELECT * FROM rooms WHERE id=?", (rid,)).fetchone()
    return dict(row) if row else None
