def wall_area(length: float, width: float, height: float, openings: list[dict]) -> dict:
    walls = 2 * (float(length) + float(width)) * float(height)
    hole = sum(float(o["w"]) * float(o["h"]) for o in openings)
    net = max(0.0, walls - hole)
    return {"gross_m2": round(walls, 2), "openings_m2": round(hole, 2), "net_m2": round(net, 2)}
