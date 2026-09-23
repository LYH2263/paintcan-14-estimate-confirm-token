from fastapi import APIRouter
from app.services.paint_service import PaintService
router = APIRouter()
@router.get("/dashboard")
def dashboard():
    with PaintService() as s: return s.dashboard()
