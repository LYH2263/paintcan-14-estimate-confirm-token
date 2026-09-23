from app.engines.paint_volume import paint_liters
from app.engines.wall_area import wall_area

def estimate_room(length, width, height, openings, coverage, coats):
    area = wall_area(length, width, height, openings)
    vol = paint_liters(area["net_m2"], coverage, coats)
    return {**area, **vol}
