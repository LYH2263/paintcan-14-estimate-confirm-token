import json
import os
from datetime import datetime, timedelta, timezone

from app.db import connect
from app.engines.estimate import estimate_room
from app.repositories import openings, receipts, rooms, runs, settings

RECEIPT_TTL_SECONDS = int(os.environ.get("RECEIPT_TTL_SECONDS", "300"))


class ReceiptError(Exception):
    """确认预检回执失败。code: not_found | reused | expired | changed"""
    def __init__(self, code, detail):
        super().__init__(detail)
        self.code = code
        self.detail = detail


def _snapshot(room, ops):
    """房间长宽高 + 门窗（种类、宽、高）的规范化快照，用于确认时比对。"""
    return {
        "length": float(room["length"]),
        "width": float(room["width"]),
        "height": float(room["height"]),
        "openings": sorted(
            ({"kind": o["kind"], "w": float(o["w"]), "h": float(o["h"])} for o in ops),
            key=lambda o: (o["kind"], o["w"], o["h"]),
        ),
    }


class PaintService:
    def __init__(self): self._c = connect()
    def close(self): self._c.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def list_rooms(self): return rooms.list_all(self._c)
    def room_detail(self, rid):
        r = rooms.get(self._c, rid)
        if not r: return None
        return {"room": r, "openings": openings.for_room(self._c, rid)}
    def settings(self): return settings.get_map(self._c)
    def history(self, limit=50): return runs.list_recent(self._c, limit)
    def dashboard(self):
        rs = rooms.list_all(self._c)
        return {"room_count": len(rs), "clean": len([x for x in rs if "种子" not in x["name"] and "多种" not in x["name"]]), "dirty": len([x for x in rs if "多种" in x["name"]])}

    def _compute(self, room_id, coats=None, coverage=None):
        """读取房间并按现有引擎计算；不写任何表。"""
        detail = self.room_detail(room_id)
        if not detail: return None
        r = detail["room"]
        cov, ct = settings.coverage_coats(self._c)
        cov = float(coverage if coverage is not None else cov)
        ct = int(coats if coats is not None else ct)
        ops = [{"w": o["w"], "h": o["h"]} for o in detail["openings"]]
        result = estimate_room(r["length"], r["width"], r["height"], ops, cov, ct)
        snapshot = _snapshot(r, detail["openings"])
        return {"coats": ct, "coverage": cov, "snapshot": snapshot, "result": result}

    def precheck(self, room_id, coats=None, coverage=None):
        """预检：只出净面积、升数与一次性回执令牌；calc_runs 条数不变。"""
        c = self._compute(room_id, coats, coverage)
        if not c: return None
        token = receipts.insert(
            self._c, room_id=room_id, coats=c["coats"], coverage=c["coverage"],
            snapshot=c["snapshot"], result=c["result"], ttl_seconds=RECEIPT_TTL_SECONDS)
        return {"room_id": room_id, "net_m2": c["result"]["net_m2"],
                "liters": c["result"]["liters"], "receipt_token": token,
                "expires_at": (datetime.now(timezone.utc)
                               + timedelta(seconds=RECEIPT_TTL_SECONDS)).isoformat()}

    def confirm(self, token):
        """持同一回执确认：核销回执与写 calc_runs 在同一事务，要么都成要么都不成。"""
        conn = self._c
        row = receipts.get_open(conn, token)
        if not row:
            # 令牌不存在或已核销（复用）
            exists = conn.execute(
                "SELECT 1 FROM estimate_receipts WHERE token=?", (token,)).fetchone()
            raise ReceiptError("reused" if exists else "not_found",
                               "回执不存在或已被使用")
        if datetime.now(timezone.utc).isoformat() > row["expires_at"]:
            # 过期即作废，防止过期回执在任何竞态下被确认
            conn.execute("UPDATE estimate_receipts SET used=1 WHERE token=?", (token,))
            conn.commit()
            raise ReceiptError("expired", "回执已过期，请重新预检")

        room = rooms.get(conn, row["room_id"])
        if not room:
            raise ReceiptError("changed", "房间不存在，预检快照已失效")
        ops = openings.for_room(conn, row["room_id"])
        current_snapshot = _snapshot(room, ops)
        if current_snapshot != json.loads(row["snapshot_json"]):
            raise ReceiptError("changed", "房间长宽高或门窗相对预检时已变化，请重新预检")

        # 快照一致 → 按预检时钉住的 coats/coverage 经同一引擎复算，口径必然一致
        result = estimate_room(
            room["length"], room["width"], room["height"],
            [{"w": o["w"], "h": o["h"]} for o in ops],
            float(row["coverage"]), int(row["coats"]))
        if result != json.loads(row["result_json"]):
            raise ReceiptError("changed", "预检与确认的计算结果不一致，请重新预检")

        payload = {"room_id": row["room_id"], "coats": int(row["coats"]),
                   "coverage": float(row["coverage"])}
        try:
            cur = receipts.consume(conn, token)
            if cur.rowcount != 1:
                conn.rollback()
                raise ReceiptError("reused", "回执已被使用")
            rid = runs.insert(conn, "estimate", payload, result,
                              room_id=row["room_id"], commit=False)
            conn.commit()
        except ReceiptError:
            raise
        except Exception:
            conn.rollback()
            raise
        return {"run_id": rid, "room_id": row["room_id"], **result}
