from pydantic import BaseModel


class PrecheckRequest(BaseModel):
    room_id: int
    coats: int | None = None
    coverage: float | None = None


class ConfirmRequest(BaseModel):
    receipt_token: str
