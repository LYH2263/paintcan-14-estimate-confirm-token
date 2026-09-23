from app.db import connect
from app.engines.estimate import estimate_room
from app.repositories import openings, receipts, rooms, runs, settings

class ReceiptRejected(Exception):
    def __init__(self, status, code, detail):
        super().__init__(detail)
        self.status = status
        self.code = code
        self.detail = detail

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
    def _compute(self, room_id, coats=None, coverage=None):
        detail = self.room_detail(room_id)
        if not detail: return None
        r = detail["room"]
        cov, ct = settings.coverage_coats(self._c)
        cov = float(coverage or cov)
        ct = int(coats or ct)
        ops = [{"w": o["w"], "h": o["h"]} for o in detail["openings"]]
        result = estimate_room(r["length"], r["width"], r["height"], ops, cov, ct)
        snap = receipts.snapshot(r, detail["openings"])
        return ct, cov, result, snap
    def estimate(self, room_id, persist, coats=None, coverage=None):
        computed = self._compute(room_id, coats, coverage)
        if not computed: return None
        ct, cov, result, _ = computed
        rid = runs.insert(self._c, "estimate", {"room_id": room_id, "coats": ct, "coverage": cov}, result, room_id) if persist else None
        return {"run_id": rid, "room_id": room_id, **result}
    def precheck(self, room_id, coats=None, coverage=None):
        # 只计算并签发一次性回执，绝不写 calc_runs
        computed = self._compute(room_id, coats, coverage)
        if not computed: return None
        ct, cov, result, snap = computed
        token = receipts.issue(self._c, room_id, ct, cov, snap, result)
        return {"net_m2": result["net_m2"], "liters": result["liters"], "receipt": token}
    def confirm(self, token):
        row = self._c.execute("SELECT room_id FROM estimate_receipts WHERE token=?", (token,)).fetchone()
        if not row:
            raise ReceiptRejected(404, "invalid_receipt", "回执不存在")
        room_id = row["room_id"]
        detail = self.room_detail(room_id)
        if not detail:
            raise ReceiptRejected(404, "invalid_receipt", "房间不存在")
        current_snap = receipts.snapshot(detail["room"], detail["openings"])
        # 核销与写历史必须同一提交：先在事务内完成核销+插入，最后一次 commit
        try:
            data = receipts.consume(self._c, token, current_snap)
            run_id = runs.insert(
                self._c, "estimate",
                {"room_id": room_id, "coats": data["coats"], "coverage": data["coverage"], "receipt": token},
                data["result"], room_id, commit=False,
            )
        except receipts.ReceiptError as e:
            self._c.rollback()
            raise ReceiptRejected(409, e.code, e.detail)
        except Exception:
            self._c.rollback()  # 历史未落则核销也一并撤销，不留半条写入
            raise
        self._c.commit()
        return {"run_id": run_id, "room_id": room_id, **data["result"]}
    def dashboard(self):
        rs = rooms.list_all(self._c)
        return {"room_count": len(rs), "clean": len([x for x in rs if "种子" not in x["name"] and "多种" not in x["name"]]), "dirty": len([x for x in rs if "多种" in x["name"]])}
