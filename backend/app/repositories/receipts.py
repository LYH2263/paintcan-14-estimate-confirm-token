import json, secrets
from datetime import datetime, timedelta, timezone

TTL_SECONDS = 600


class ReceiptError(Exception):
    def __init__(self, code, detail):
        super().__init__(detail)
        self.code = code
        self.detail = detail


def snapshot(room, openings):
    # 预检时刻房间长宽高与门窗（宽高）的完整快照
    return {
        "length": float(room["length"]),
        "width": float(room["width"]),
        "height": float(room["height"]),
        "openings": sorted(
            ({"kind": o.get("kind"), "w": float(o["w"]), "h": float(o["h"])} for o in openings),
            key=lambda o: (str(o["kind"]), o["w"], o["h"]),
        ),
    }


def issue(conn, room_id, coats, coverage, snap, result, ttl_seconds=TTL_SECONDS):
    now = datetime.now(timezone.utc)
    token = secrets.token_urlsafe(24)
    conn.execute(
        "INSERT INTO estimate_receipts(token,room_id,coats,coverage,snapshot_json,result_json,created_at,expires_at,used)"
        " VALUES (?,?,?,?,?,?,?,?,0)",
        (token, room_id, int(coats), float(coverage),
         json.dumps(snap, ensure_ascii=False), json.dumps(result, ensure_ascii=False),
         now.isoformat(), (now + timedelta(seconds=ttl_seconds)).isoformat()),
    )
    conn.commit()
    return token


def consume(conn, token, current_snapshot):
    """在调用方事务内核销回执并返回其落库数据；任何失败均抛 ReceiptError，不提交。"""
    row = conn.execute("SELECT * FROM estimate_receipts WHERE token=?", (token,)).fetchone()
    if not row:
        raise ReceiptError("invalid_receipt", "回执不存在")
    if row["used"]:
        raise ReceiptError("receipt_reused", "回执已使用，请勿重复提交")
    if datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
        raise ReceiptError("receipt_expired", "回执已过期，请重新预检")
    if json.loads(row["snapshot_json"]) != current_snapshot:
        raise ReceiptError("snapshot_changed", "房间长宽高或门窗相对预检快照已变化，请重新预检")
    cur = conn.execute("UPDATE estimate_receipts SET used=1 WHERE token=? AND used=0", (token,))
    if cur.rowcount != 1:
        raise ReceiptError("receipt_reused", "回执已使用，请勿重复提交")
    return {
        "room_id": row["room_id"],
        "coats": row["coats"],
        "coverage": row["coverage"],
        "result": json.loads(row["result_json"]),
    }
