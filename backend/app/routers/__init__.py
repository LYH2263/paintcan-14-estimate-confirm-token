from fastapi import APIRouter
from app.routers import dashboard, estimate, history, rooms, settings
api = APIRouter(prefix="/api")
for r in (dashboard, rooms, estimate, history, settings): api.include_router(r.router)
