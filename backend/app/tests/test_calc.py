import pytest
from app.engines.estimate import estimate_room
from app.engines.paint_volume import paint_liters
from app.engines.wall_area import wall_area

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
