from pydantic import BaseModel
class EstimateRequest(BaseModel):
    room_id: int
    coats: int | None = None
    coverage: float | None = None
    persist: bool = True

class PrecheckRequest(BaseModel):
    room_id: int
    coats: int | None = None
    coverage: float | None = None

class ConfirmRequest(BaseModel):
    receipt: str
