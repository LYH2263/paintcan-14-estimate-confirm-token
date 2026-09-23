import os
import tempfile

import pytest

# 所有 app 模块导入前指定独立数据目录，避免污染开发库
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="paintcan-test-"))

from app.db import connect
from app.engines.estimate import estimate_room
from app.engines.paint_volume import paint_liters
from app.engines.wall_area import wall_area
from app.repositories import receipts, runs
from app.seed import init_db
from app.services.paint_service import PaintService, ReceiptRejected

init_db()


def test_living_room_net():
    a = wall_area(5, 4, 2.8, [{"w": 0.9, "h": 2.1}, {"w": 1.5, "h": 1.4}])
    assert a["gross_m2"] == 50.4
    assert a["net_m2"] == 46.41


def test_liters_two_coats():
    v = paint_liters(46.41, 8, 2)
    assert v["liters"] == 11.6


def test_estimate_combined():
    e = estimate_room(5, 4, 2.8, [{"w": 0.9, "h": 2.1}, {"w": 1.5, "h": 1.4}], 8, 2)
    assert e["liters"] == 11.6


def test_bad_coverage():
    with pytest.raises(ValueError):
        paint_liters(10, 0, 2)


# ---------- 预检 / 确认两步流程 ----------

def _run_count():
    with connect() as c:
        return runs.count(c)


def test_precheck_does_not_insert_run_and_matches_engine():
    before = _run_count()
    with PaintService() as s:
        pre = s.precheck(1)
    after = _run_count()
    assert after == before  # 预检不得增加 calc_runs 条数
    assert set(pre) == {"net_m2", "liters", "receipt"}  # 只回包净面积、升数与令牌
    # 升数/净面积口径与现有引擎一致
    assert pre["net_m2"] == 46.41
    assert pre["liters"] == 11.6


def test_confirm_inserts_exactly_one_row():
    before = _run_count()
    with PaintService() as s:
        pre = s.precheck(1)
        assert _run_count() == before
        out = s.confirm(pre["receipt"])
    assert _run_count() == before + 1  # 确认成功后仅新增一条
    assert out["run_id"] is not None
    assert out["net_m2"] == pre["net_m2"] and out["liters"] == pre["liters"]


def test_receipt_reuse_rejected_without_extra_row():
    before = _run_count()
    with PaintService() as s:
        pre = s.precheck(1)
        s.confirm(pre["receipt"])
        with pytest.raises(ReceiptRejected) as ei:
            s.confirm(pre["receipt"])
    assert ei.value.code == "receipt_reused"
    assert _run_count() == before + 1  # 复用拒绝，条数不再增加


def test_unknown_receipt_rejected():
    before = _run_count()
    with PaintService() as s:
        with pytest.raises(ReceiptRejected) as ei:
            s.confirm("not-a-real-token")
    assert ei.value.code == "invalid_receipt"
    assert _run_count() == before


def test_expired_receipt_rejected():
    before = _run_count()
    with PaintService() as s:
        computed = s._compute(1)
        ct, cov, result, snap = computed
        token = receipts.issue(s._c, 1, ct, cov, snap, result, ttl_seconds=-10)
        with pytest.raises(ReceiptRejected) as ei:
            s.confirm(token)
    assert ei.value.code == "receipt_expired"
    assert _run_count() == before


def test_snapshot_changed_rejected_then_fresh_precheck_confirms():
    before = _run_count()
    with PaintService() as s:
        pre = s.precheck(1)
        # 预检后房间高度发生变化
        s._c.execute("UPDATE rooms SET height=? WHERE id=?", (3.0, 1))
        s._c.commit()
        with pytest.raises(ReceiptRejected) as ei:
            s.confirm(pre["receipt"])
        assert ei.value.code == "snapshot_changed"
        assert _run_count() == before
        # 恢复后重新预检可正常确认
        s._c.execute("UPDATE rooms SET height=? WHERE id=?", (2.8, 1))
        s._c.commit()
        pre2 = s.precheck(1)
        out = s.confirm(pre2["receipt"])
        assert out["liters"] == 11.6
    assert _run_count() == before + 1


def test_opening_changed_rejected():
    before = _run_count()
    with PaintService() as s:
        pre = s.precheck(1)
        s._c.execute("UPDATE openings SET h=? WHERE room_id=? AND kind='door'", (2.0, 1))
        s._c.commit()
        with pytest.raises(ReceiptRejected) as ei:
            s.confirm(pre["receipt"])
        assert ei.value.code == "snapshot_changed"
        assert _run_count() == before
        s._c.execute("UPDATE openings SET h=? WHERE room_id=? AND kind='door'", (2.1, 1))
        s._c.commit()


def test_consume_and_history_share_one_commit(monkeypatch):
    # 模拟核销后、提交前插入历史失败：两者必须一同回滚，回执仍可再次确认成功
    before = _run_count()
    with PaintService() as s:
        pre = s.precheck(1)
        real_insert = runs.insert

        def boom(*a, **kw):
            raise RuntimeError("history write failed")

        monkeypatch.setattr(runs, "insert", boom)
        with pytest.raises(RuntimeError):
            s.confirm(pre["receipt"])
        monkeypatch.setattr(runs, "insert", real_insert)
        # 记录未落、核销也未生效：同一回执随后可成功确认
        assert _run_count() == before
        out = s.confirm(pre["receipt"])
        assert out["run_id"] is not None
    assert _run_count() == before + 1
