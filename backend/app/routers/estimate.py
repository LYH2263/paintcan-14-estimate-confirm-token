from fastapi import APIRouter, HTTPException
from app.schemas.estimate import ConfirmRequest, EstimateRequest, PrecheckRequest
from app.services.paint_service import PaintService, ReceiptRejected
router = APIRouter()
@router.post("/estimate")
def post_estimate(body: EstimateRequest):
    with PaintService() as s:
        r = s.estimate(body.room_id, body.persist, body.coats, body.coverage)
        if not r: raise HTTPException(404)
        return r
@router.post("/estimate/precheck")
def post_precheck(body: PrecheckRequest):
    with PaintService() as s:
        r = s.precheck(body.room_id, body.coats, body.coverage)
        if not r: raise HTTPException(404, detail="房间不存在")
        return r
@router.post("/estimate/confirm")
def post_confirm(body: ConfirmRequest):
    with PaintService() as s:
        try:
            return s.confirm(body.receipt)
        except ReceiptRejected as e:
            raise HTTPException(e.status, detail={"code": e.code, "message": e.detail})
