def paint_liters(net_m2: float, coverage_m2_per_l: float, coats: int) -> dict:
    if coverage_m2_per_l <= 0 or coats <= 0:
        raise ValueError("coverage and coats must be positive")
    need = float(net_m2) * int(coats) / float(coverage_m2_per_l)
    return {"liters": round(need, 2), "coats": int(coats), "coverage": float(coverage_m2_per_l)}
