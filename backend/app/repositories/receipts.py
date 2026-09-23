import json
from datetime import datetime, timedelta, timezone


def _now():
    return datetime.now(timezone.utc)


def _token() -> str:
    import secrets
    return secrets.token_hex(20)


def insert(conn, *, room_id, coats, coverage, snapshot, result, ttl_seconds):
    """落一条预检回执（与 calc_runs 无关），返回回执令牌。"""
    token = _token()
    expires_at = (_now() + timedelta(seconds=ttl_seconds)).isoformat()
    conn.execute(
        "INSERT INTO estimate_receipts(token,room_id,coats,coverage,snapshot_json,result_json,expires_at,used,created_at)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (token, room_id, coats, coverage,
         json.dumps(snapshot, ensure_ascii=False),
         json.dumps(result, ensure_ascii=False),
         expires_at, 0, _now().isoformat()),
    )
    conn.commit()
    return token


def get_open(conn, token):
    row = conn.execute(
        "SELECT * FROM estimate_receipts WHERE token=? AND used=0", (token,)
    ).fetchone()
    return dict(row) if row else None


def consume(conn, token):
    """核销回执（置 used=1）。须与 calc_runs 写入在同一事务内。"""
    return conn.execute(
        "UPDATE estimate_receipts SET used=1 WHERE token=? AND used=0", (token,)
    )
