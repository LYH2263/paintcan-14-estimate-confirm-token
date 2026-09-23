import json

import pytest

from app import seed
from app.db import connect
from app.engines.estimate import estimate_room
from app.services.paint_service import PaintService, ReceiptError


@pytest.fixture()
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr("app.db.DB_PATH", tmp_path / "test.db")
    seed.init_db()
    yield


def _run_count(conn):
    return conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]


def test_precheck_does_not_insert_run(fresh_db):
    with PaintService() as s:
        before = _run_count(s._c)
        pre = s.precheck(1)
        after = _run_count(s._c)
    assert set(pre) == {"room_id", "net_m2", "liters", "receipt_token", "expires_at"}
    assert after == before
    assert pre["receipt_token"]


def test_precheck_liters_match_engine(fresh_db):
    # 与现有引擎同一口径：客厅 5x4x2.8、两门窗、覆盖率8、2遍 → 净46.41 / 11.6升
    with PaintService() as s:
        pre = s.precheck(1)
    assert pre["net_m2"] == 46.41
    assert pre["liters"] == 11.6
    direct = estimate_room(5, 4, 2.8,
                           [{"w": 0.9, "h": 2.1}, {"w": 1.5, "h": 1.4}], 8, 2)
    assert (pre["net_m2"], pre["liters"]) == (direct["net_m2"], direct["liters"])


def test_confirm_writes_exactly_one_run(fresh_db):
    with PaintService() as s:
        before = _run_count(s._c)
        pre = s.precheck(1)
        assert _run_count(s._c) == before
        out = s.confirm(pre["receipt_token"])
        assert _run_count(s._c) == before + 1
    assert out["run_id"] is not None
    assert out["liters"] == pre["liters"]
    assert out["net_m2"] == pre["net_m2"]
    row = connect().execute(  # 落库结果即引擎结果
        "SELECT result_json FROM calc_runs WHERE id=?", (out["run_id"],)).fetchone()
    assert json.loads(row["result_json"])["liters"] == 11.6


def test_reused_token_rejected_and_no_new_row(fresh_db):
    with PaintService() as s:
        pre = s.precheck(1)
        s.confirm(pre["receipt_token"])
        n = _run_count(s._c)
        with pytest.raises(ReceiptError) as ei:
            s.confirm(pre["receipt_token"])
        assert ei.value.code == "reused"
        assert _run_count(s._c) == n


def test_unknown_token_rejected(fresh_db):
    with PaintService() as s:
        n = _run_count(s._c)
        with pytest.raises(ReceiptError) as ei:
            s.confirm("deadbeef")
        assert ei.value.code == "not_found"
        assert _run_count(s._c) == n


def test_expired_token_rejected_and_no_new_row(fresh_db):
    with PaintService() as s:
        pre = s.precheck(1)
        n = _run_count(s._c)
        s._c.execute("UPDATE estimate_receipts SET expires_at='2000-01-01T00:00:00+00:00'"
                     " WHERE token=?", (pre["receipt_token"],))
        s._c.commit()
        with pytest.raises(ReceiptError) as ei:
            s.confirm(pre["receipt_token"])
        assert ei.value.code == "expired"
        assert _run_count(s._c) == n
        # 过期回执已作废，再确认仍不落库
        with pytest.raises(ReceiptError) as ei:
            s.confirm(pre["receipt_token"])
        assert ei.value.code in ("expired", "reused")
        assert _run_count(s._c) == n


def test_room_dims_changed_rejected(fresh_db):
    with PaintService() as s:
        pre = s.precheck(1)
        n = _run_count(s._c)
        s._c.execute("UPDATE rooms SET height=3.2 WHERE id=1")
        s._c.commit()
        with pytest.raises(ReceiptError) as ei:
            s.confirm(pre["receipt_token"])
        assert ei.value.code == "changed"
        assert _run_count(s._c) == n


def test_opening_changed_rejected(fresh_db):
    with PaintService() as s:
        pre = s.precheck(1)
        n = _run_count(s._c)
        s._c.execute("UPDATE openings SET w=1.0 WHERE room_id=1 AND kind='door'")
        s._c.commit()
        with pytest.raises(ReceiptError) as ei:
            s.confirm(pre["receipt_token"])
        assert ei.value.code == "changed"
        assert _run_count(s._c) == n


def test_opening_added_rejected(fresh_db):
    with PaintService() as s:
        pre = s.precheck(1)
        n = _run_count(s._c)
        s._c.execute("INSERT INTO openings(room_id,kind,w,h) VALUES (1,'window',1.0,1.0)")
        s._c.commit()
        with pytest.raises(ReceiptError) as ei:
            s.confirm(pre["receipt_token"])
        assert ei.value.code == "changed"
        assert _run_count(s._c) == n
