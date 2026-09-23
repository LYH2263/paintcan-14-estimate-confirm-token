from fastapi import APIRouter, HTTPException

from app.schemas.estimate import ConfirmRequest, PrecheckRequest
from app.services.paint_service import PaintService, ReceiptError

router = APIRouter()

_RECEIPT_STATUS = {"not_found": 404, "reused": 409, "expired": 410, "changed": 409}


@router.post("/estimate/precheck")
def precheck(body: PrecheckRequest):
    with PaintService() as s:
        r = s.precheck(body.room_id, body.coats, body.coverage)
        if not r:
            raise HTTPException(404, "房间不存在")
        return r


@router.post("/estimate/confirm")
def confirm(body: ConfirmRequest):
    with PaintService() as s:
        try:
            return s.confirm(body.receipt_token)
        except ReceiptError as e:
            raise HTTPException(_RECEIPT_STATUS.get(e.code, 409),
                                {"code": e.code, "detail": e.detail})
