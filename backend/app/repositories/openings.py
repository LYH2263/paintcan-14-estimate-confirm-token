import sqlite3
def for_room(conn, room_id):
    return [dict(r) for r in conn.execute("SELECT * FROM openings WHERE room_id=?", (room_id,)).fetchall()]
