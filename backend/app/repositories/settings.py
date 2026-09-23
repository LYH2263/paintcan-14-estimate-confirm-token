import sqlite3
def get_map(conn): return {r["key"]: r["value"] for r in conn.execute("SELECT * FROM settings").fetchall()}
def coverage_coats(conn):
    m = get_map(conn)
    return float(m.get("coverage", "8")), int(m.get("coats", "2"))
