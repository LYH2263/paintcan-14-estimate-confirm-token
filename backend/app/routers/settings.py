from fastapi import APIRouter
from app.services.paint_service import PaintService
router = APIRouter()
@router.get("/settings")
def settings():
    with PaintService() as s: return s.settings()
