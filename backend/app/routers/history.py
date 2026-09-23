from fastapi import APIRouter
from app.services.paint_service import PaintService
router = APIRouter()
@router.get("/history")
def history(limit: int = 50):
    with PaintService() as s: return {"items": s.history(limit)}
